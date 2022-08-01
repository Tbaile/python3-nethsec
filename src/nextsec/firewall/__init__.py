#!/usr/bin/python3

#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

'''
Firewall utilities
'''

import json
import subprocess
from nextsec import utils

def get_device_name(hwaddr):
    '''
    Retrieve the physical device name given the MAC address

    Aarguments:
      hwaddr -- MAC address string

    Returns:
      The device name as a string if the network interface has been found, None otherwise.
    '''
    interfaces = json.loads(subprocess.run(["/sbin/ip", "--json", "address", "show"], check=True, capture_output=True).stdout)
    for interface in interfaces:
        if interface["address"] == hwaddr:
            return interface["ifname"]

    return None

def get_interface_name(uci, hwaddr):
    '''
    Retrieve the logical UCI interface name given the MAC address
    '''
    name = get_device_name(hwaddr)
    for section in uci.get("network"):
        if  uci.get("network", section) == "interface" and (uci.get("network", section, "device") == name):
            return section

    return None

def add_to_zone(uci, device, zone):
    '''
    Add given device to a firewall zone
    '''
    for section in uci.get("firewall"):
        s_type = uci.get("firewall", section)
        if s_type == "zone":
            zname = uci.get("firewall", section, "name")
            if zname == zone:
                try:
                    devices = uci.get_all("firewall", section, "device")
                except:
                    devices = []
                if not device in devices:
                    devices.append(device)
                    uci.set("firewall", section, "device", devices)


def add_to_lan(uci, device):
    '''
    Shortuct to add a device to lan zone
    '''
    add_to_zone(uci, device, 'lan')

def add_to_wan(uci, device):
    '''
    Shortuct to add a device to wan zone
    '''
    add_to_zone(uci, device, 'wan')

def allow_service(uci, name, port, proto):
    '''
    Create an ACCEPT traffic rile for the given service
    '''
    name = utils.sanitize(name)
    rname = utils.sanitize(f"allow_{name}")
    uci.set("firewall", rname, "rule")
    uci.set("firewall", rname, "name", f"Allow-{name}")
    uci.set("firewall", rname, "src", "wan")
    uci.set("firewall", rname, "dest_port", port)
    uci.set("firewall", rname, "proto", proto)
    uci.set("firewall", rname, "target", "ACCEPT")

def block_service(uci, name):
    '''
    Remove the ACCEPT traffic rul for the given service
    '''
    name = utils.sanitize(name)
    rname = utils.sanitize(f"allow_{name}")
    uci.delete("firewall", rname)

def apply(uci):
    '''
    Apply firewall configuration
    '''
    uci.commit('firewall')
    subprocess.run(["/etc/init.d/firewall", "reload"], check=True)
