#!/usr/bin/env python3
"""
Module to read information about network interfaces used in a system
"""

import re
import subprocess
import os
import os.path

def get_numa(dev, root_dict):
    """
    Determine NUMA node the card is connected to
    """
    root_dict["NUMA"] = "--"
    numa_file = f'/sys/class/net/{dev}/device/numa_node'
    if os.path.isfile(numa_file):
        with open(numa_file, 'r', encoding='us-ascii') as file:
            root_dict["NUMA"] = file.read().rstrip()

def translate_vendor_id(root_dict):
    """
    Lookup vendor information in OS database
    """
    vendor_id = root_dict["VendorID"]
    if vendor_id.startswith("0x"):
        vendor_id  = vendor_id[2:]
    with open("/usr/share/hwdata/pci.ids", 'r', encoding='utf-8') as pci_db:
        for line in pci_db:
            re_match = re.match(rf'^{vendor_id}\s*(.*)$', line)
            if re_match:
                root_dict["VendorID"] = re_match.group(1)

def get_sysfs(dev, root_dict):
    """
    Read low level information from /sys/class/net
    """
    root_dict["ModAlias"] = ""
    root_dict["PCIslot"] = ""
    root_dict["uDriver"] = ""
    uevent_file = f'/sys/class/net/{dev}/device/uevent'
    if os.path.isfile(uevent_file):
        with open(uevent_file, 'r', encoding="us-ascii") as uevent_fh:
            for line in uevent_fh:
                [tag,value] = line.strip().split("=")
                if tag == "MODALIAS":
                    root_dict["ModAlias"] = value
                if tag == "DRIVER":
                    root_dict["uDriver"] = value
                if tag == "PCI_SLOT_NAME":
                    root_dict["PCIslot"] = value
    try:
        root_dict["VendorID"] = open(f'/sys/class/net/{dev}/device/vendor', 'r',
                                     encoding="us-ascii").read().strip()
    except OSError:
        root_dict["VendorID"] = "Generic"
    try:
        root_dict["Type"] = open(f'/sys/class/net/{dev}/device/device', 'r',
                                 encoding="us-ascii").read().strip()
    except OSError:
        root_dict["Type"] = "Network adaptor"

def get_ethtool(dev, card_dict, root_dict):
    """
    Read low level card information from ethtool
    """
#
#    Initialize fields for devices without bus-info in ethtool
#
    root_dict["Card"] = ""
    root_dict["Subsys"] = ""
    with subprocess.Popen('/usr/sbin/ethtool -i ' + dev, shell=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as eth_out:
        for line in eth_out.stdout.readlines():
            line = line.decode()
            re_match = re.match(r'^driver: (.*)$', line)
            if re_match:
                root_dict["Driver"] = re_match.group(1)
            re_match = re.match(r'^version: (.*)$', line)
            if re_match:
                root_dict["Version"] = re_match.group(1)
            re_match = re.match(r'^firmware-version: (.*)$', line)
            if re_match:
                root_dict["FW"] = re_match.group(1)
            re_match = re.match(r'^bus-info: (.*)$', line)
            if re_match:
                root_dict["PCI"] = re_match.group(1)
                for card in card_dict:
                    if root_dict["PCI"].endswith(card):
                        root_dict["Card"] = card_dict[card]["Card"]
                        root_dict["Subsys"] = card_dict[card]["Subsys"]

def get_pci_info():
    """
    Generate dictionary of PCI(e) cards in the system
    """
    pci_bus = os.popen('/sbin/lspci -v', 'r')
    card_dict = {}
    for line in pci_bus:
        re_match = re.match(r'^(.*\w{2}\:\w{2}\.\d) (.*)\s*$', line)
        if re_match:
            slot = re_match.group(1)
            card_type = re_match.group(2)
            card_dict[slot] = dict({"Card": card_type})
        re_match = re.match(r'^\s+Subsystem: (.*)\s*$', line)
        if re_match:
            card_dict[slot]["Subsys"] = re_match.group(1)
#
# Sometimes Subsystem masquerades as DeviceName....
#
        re_match = re.match(r'^\s+DeviceName: (.*)\s*$', line)
        if re_match:
            if card_dict[slot].get("Subsys", "") == "":
                card_dict[slot]["Subsys"] = re_match.group(1)

    return card_dict

class NETinfo:
    """
    Read pci, ip and bond information to
    collect an overview of network interfaces
    in a system
    """

    macDict = {}
    macDict["00:23:7D"] = "Hewlett Packard"
    macDict["00:1C:C4"] = "Hewlett Packard"
    macDict["24:BE:05"] = "Hewlett Packard"
    macDict["2C:76:8A"] = "Hewlett Packard"
    macDict["3C:D9:2B"] = "Hewlett Packard"
    macDict["9C:8E:99"] = "Hewlett Packard"
    macDict["98:4B:E1"] = "Hewlett Packard"
    macDict["AC:16:2D"] = "Hewlett Packard"
    macDict["B4:99:BA"] = "Hewlett Packard"
    macDict["E8:39:35"] = "Hewlett Packard"
    macDict["00:24:D7"] = "Intel"
    macDict["B8:AC:6F"] = "Dell"
    macDict["00:02:C9"] = "Mellanox"
    macDict["00:0A:68"] = "Solarflare"
    macDict["00:0F:53"] = "Solarflare"
    macDict["00:07:43"] = "Chelsio"
    macDict["00:10:18"] = "Broadcom"

    def __init__(self, load_data=None):

#
#  Initialize data fields
#
        self.devices = {}
        self.trunk_dev = {}

        if not load_data:

            global_slaves = []
#
# Retrieve data from local machine
#

            card_dict = get_pci_info()

            self.get_ip(card_dict)

            self.norm_dev_list()

            self.proc_bond(card_dict, global_slaves)
#
# Finally remove all slaveDevies from primary list (else they are twice enumerated)
#

            for dev in global_slaves:
                self.devices.pop(dev, None)

#
# Thought one could get biosdevname from /etc/systemd/network in case device was renamed
# but this is just a convention.
#
        else:
#
#  Re-create object from saved dictionary
#
            for key in vars(self):
                setattr(self, key, load_data[key])

    def proc_bond(self, card_dict, global_slaves):
        """
        Remove loopback device and pick up on trunk devices.
        """
        for dev in self.devices:
            if dev.startswith('bond'):
                self.devices[dev]["SlaveList"] = {}
                self.devices[dev]["BondType"] = ""
                with open(f'/proc/net/bonding/{dev}', 'r', encoding="us-ascii") as bond_info:
                    for line in bond_info:
                        re_match = re.match(r'^802.3ad info', line)
                        if re_match:
                            self.devices[dev]["BondType"] = "LACP 802.3ad"
                        re_match = re.match(r'Bonding Mode: fault-tolerance', line)
                        if re_match:
                            self.devices[dev]["BondType"] = "active-backup"
                        re_match = re.match(r'^Currently Active Slave: (.*)$', line)
                        if re_match:
                            self.devices[dev]["Active"] = re_match.group(1)
                        re_match = re.match(r'^Slave Interface: (.*)$', line)
                        if re_match:
                            slave_device = re_match.group(1)
                            global_slaves.append(slave_device)
                            slave_dict= {}
                            get_ethtool(slave_device, card_dict, slave_dict)
                            get_sysfs(slave_device, slave_dict)
                            get_numa(slave_device, slave_dict)
                            with subprocess.Popen('/sbin/ip addr show  ' + slave_device,
                                                  shell=True, stdout=subprocess.PIPE,
                                                  stderr=subprocess.STDOUT) as ipas:
                                for ipas_line in ipas.stdout.readlines():
                                    rem = re.match(r'^\s+link/(ether|infiniband) (\w{2}:.*) brd',
                                                 ipas_line.decode('ISO-8859-1'))
                                    if rem:
                                        slave_dict["MAC"] = str.upper(rem.group(2))
                            translate_vendor_id(slave_dict)
                            self.devices[dev]["SlaveList"][slave_device] = slave_dict
            else:
                translate_vendor_id(self.devices[dev])

    def norm_dev_list(self):
        """
        Remove loopback device and pick up on trunk devices.
        """
        for dev in list(self.devices):
            if self.devices[dev]["IPAdd"] == "127.0.0.1":
                self.devices.pop(dev, None)
            if "@" in dev:
                self.trunk_dev[dev] = {}
                self.trunk_dev[dev]["IPAdd"] = self.devices[dev]["IPAdd"]
                self.devices.pop(dev, None)


    def get_ip(self, card_dict):
        """
        Get information about defined ip interfaces on the
        system
        """
        raw = os.popen('/sbin/ip addr show', 'r')

        curr_dev = ""

        for item in raw:
            re_match = re.match(r'^\d+: (.*):', item)
            if re_match:
                curr_dev = re_match.group(1)
                self.devices[curr_dev] = {}
                self.devices[curr_dev]["IPAdd"] = "-"*15
            re_match = re.match(r'^\s+link/(ether|infiniband) (\w{2}:.*) brd', item)
            if re_match:
                self.devices[curr_dev]["MAC"] = str.upper(re_match.group(2))
            re_match = re.match(r'^\s+inet (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/\d{1,2}', item)
            if re_match:
                ip_add = re_match.group(1)
                self.devices[curr_dev]["IPAdd"] = ip_add

            get_ethtool(curr_dev, card_dict, self.devices[curr_dev])
            get_sysfs(curr_dev, self.devices[curr_dev])
            get_numa(curr_dev, self.devices[curr_dev])

    def format_trunk(self, dev, out_string, indent):
        """
        Special print format for trunk interfaces (i.e. several VLANs on
        one interface)
        """
        vlan_string = ""
        for vlan_dev in sorted(self.trunk_dev):
            if "@" + dev in vlan_dev:
                display_name, dummy = vlan_dev.split("@")
                vlan_string = vlan_string + f'{display_name}: {self.trunk_dev[vlan_dev]["IPAdd"]} '
        if vlan_string != "":
            out_string = out_string + indent + vlan_string + "\n"
        return out_string

    def __str__(self):
        indent  = " "*3
        head_layout  = "{0:13s}  {1:15s} {2:25s} {3:10s} {4:30s} {5:27s} {6:4s} {7:12s}\n"
        slave_layout = "{0:13s}  {1:9s} {2:25s} {3:10s} {4:30s} {5:27s} {6:4s} {7:12s}\n"
        card_layout  = "{0:90s}\n{1}{2}\n"
        net_str = head_layout.format("Device", "IP Address", "Vendor",
                                     "Driver", "Version", "FW", "NUMA", "PCI")
        net_str = net_str + indent + card_layout.format("Card", indent, "Subsys")
        for device in sorted(self.devices):
            if device.startswith('bond'):
                net_str = net_str + head_layout.format(device, self.devices[device]["IPAdd"],
                                                                 self.devices[device]["VendorID"],
                                                                 self.devices[device]["Driver"],
                                                                 self.devices[device]["Version"],
                                                                 self.devices[device]["FW"],
                                                                 "", ""
                                                                 )
                net_str = net_str + indent + f'Bond Mode: {self.devices[device]["BondType"]}\n'
                if self.devices[device]["BondType"] == "active-backup":
                    net_str = net_str[:-1] + indent +\
                                f'Active Slave: {self.devices[device]["Active"]}\n'
                net_str = self.format_trunk(device, net_str, indent)
                for dev in self.devices[device]["SlaveList"]:
                    slave_dict =  self.devices[device]["SlaveList"][dev]
                    net_str = net_str  + indent*2 + slave_layout.format(dev, 9*"-",
                                                            slave_dict.get("VendorID", 16*"-"),
                                                            slave_dict["Driver"],
                                                            slave_dict["Version"],
                                                            slave_dict["FW"],
                                                            slave_dict["NUMA"],
                                                            slave_dict["PCI"],
                                                           )
                    net_str = net_str  + indent*3 + card_layout.format(slave_dict["Card"],
                                                                  indent*3, slave_dict["Subsys"])

            else:
                net_str = net_str + head_layout.format(device, self.devices[device]["IPAdd"],
                                                                 self.devices[device]["VendorID"],
                                                                 self.devices[device]["Driver"],
                                                                 self.devices[device]["Version"],
                                                                 self.devices[device]["FW"],
                                                                 self.devices[device]["NUMA"],
                                                                 self.devices[device]["PCI"],
                                                                )

                net_str = self.format_trunk(device, net_str, indent)
                net_str = net_str  + indent + card_layout.format(self.devices[device]["Card"],
                                                                 indent,
                                                                 self.devices[device]["Subsys"]
                                                                 )
        net_str = net_str[:-1]
        return net_str

if __name__ == '__main__':
    MyNet = NETinfo()
    print(MyNet)
    if len(str(MyNet)) == 0:
        netDict= dict(devices=dict(carrierPidgeon=dict(IPAdd='127.0.0.2', Card='', Subsys='',
                      Driver="corn", Version='08/15', FW='bird',
                      PCI='1.2.3', ModAlias='', PCIslot='1', uDriver='', VendorID='BirdHouse',
                      Type='Bird transport', NUMA='2', MAC='Cheese')), trunk_dev={})
        loadNet = NETinfo(netDict)
        print(loadNet)
