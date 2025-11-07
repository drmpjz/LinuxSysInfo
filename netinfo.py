#!/usr/bin/env python3

import re
import socket
import os.path
import subprocess
import os

class NETinfo:

    macDict = dict()
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

    def __init__(self):
    
        PCIbus = os.popen('/sbin/lspci -v', 'r')
        cardDict = dict()
        for line in PCIbus:
            m = re.match(r'^(.*\w{2}\:\w{2}\.\d) (.*)\s*$', line)
            if m:
                slot = m.group(1)
                Ctype = m.group(2)
                cardDict[slot] = dict({"Card": Ctype})
            m = re.match(r'^\s+Subsystem: (.*)\s*$', line)
            if m:
                cardDict[slot]["Subsys"] = m.group(1)
#
# Sometimes Subsystem masquerades as DeviceName....
#
            m = re.match(r'^\s+DeviceName: (.*)\s*$', line)
            if m:
                if cardDict[slot].get("Subsys", "") == "":
                    cardDict[slot]["Subsys"] = m.group(1)
                         
            
        raw = os.popen('/sbin/ip addr show', 'r')

        self.devices = dict()
        self.globalSlaves = list()
        self.trunkDev = dict()
        self.currDev = ""
        self.indent  = " "*3

        for item in raw:
            m = re.match(r'^\d+: (.*):', item)
            if m:
                self.currDev = m.group(1)
                self.devices[self.currDev] = dict()
                self.devices[self.currDev]["IPAdd"] = "-"*15
            m = re.match(r'^\s+link/(ether|infiniband) (\w{2}:.*) brd', item)
            if m:
                self.devices[self.currDev]["MAC"] = str.upper(m.group(2))
            m = re.match(r'^\s+inet (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/\d{1,2}', item)
            if m:
                ipAdd = m.group(1)
                self.devices[self.currDev]["IPAdd"] = ipAdd

            self.getEthTool(self.currDev, cardDict, self.devices[self.currDev])
            self.getSysFS(self.currDev, self.devices[self.currDev]) 
            self.getNUMA(self.currDev, self.devices[self.currDev])                  
                        
#                   
# Remove loopback
#

        for dev in list(self.devices):
            if self.devices[dev]["IPAdd"] == "127.0.0.1":        
                self.devices.pop(dev, None)
            if "@" in dev:
                self.trunkDev[dev] = dict()
                self.trunkDev[dev]["IPAdd"] = self.devices[dev]["IPAdd"]
                self.devices.pop(dev, None)

#
# Now remove loopback and check if we found any bonding devices
#
        for dev in self.devices:
            if dev.startswith('bond'):
               self.devices[dev]["SlaveList"] = dict()
               self.devices[dev]["BondType"] = ""
               bondInfo = open('/proc/net/bonding/{0}'.format(dev), 'r')
               for line in bondInfo:
                   m = re.match(r'^802.3ad info', line)
                   if m:
                       self.devices[dev]["BondType"] = "LACP 802.3ad"
                   m = re.match(r'Bonding Mode: fault-tolerance', line)
                   if m:
                       self.devices[dev]["BondType"] = "active-backup"
                   m = re.match(r'^Currently Active Slave: (.*)$', line)
                   if m:
                       self.devices[dev]["Active"] = m.group(1)
                   m = re.match(r'^Slave Interface: (.*)$', line) 
                   if m:
                       slaveDevice = m.group(1)
                       self.globalSlaves.append(slaveDevice)
                       self.devices[dev]["SlaveList"][slaveDevice] = dict()
                       self.getEthTool(slaveDevice, cardDict, self.devices[dev]["SlaveList"][slaveDevice])
                       self.getSysFS(slaveDevice, self.devices[dev]["SlaveList"][slaveDevice])
                       self.getNUMA(slaveDevice, self.devices[dev]["SlaveList"][slaveDevice])
                       p = subprocess.Popen('/sbin/ip addr show  ' + slaveDevice, shell=True,
                                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                       for line in p.stdout.readlines():
                           m = re.match(r'^\s+link/(ether|infiniband) (\w{2}:.*) brd', line.decode('ISO-8859-1'))
                           if m:
                               self.devices[dev]["SlaveList"][slaveDevice]["MAC"] = str.upper(m.group(2))
                       self.translateVendorID(slaveDevice,self.devices[dev]["SlaveList"][slaveDevice])
            else:
                self.translateVendorID(dev, self.devices[dev])

#
# Thought one could get biosdevname from /etc/systemd/network in case device was renamed
# but this is just a convention.
#

        
    def getEthTool(self, dev, cardDict, rootDict):
#
#       Initialize fields for devices without bus-info in ethtool
#
        rootDict["Card"] = ""
        rootDict["Subsys"] = "" 
        p = subprocess.Popen('/usr/sbin/ethtool -i ' + dev, shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            line = line.decode()
            m = re.match(r'^driver: (.*)$', line)
            if m:
                rootDict["Driver"] = m.group(1)
            m = re.match(r'^version: (.*)$', line)
            if m:
                rootDict["Version"] = m.group(1)
            m = re.match(r'^firmware-version: (.*)$', line)
            if m:
                rootDict["FW"] = m.group(1)
            m = re.match(r'^bus-info: (.*)$', line)
            if m:
                rootDict["PCI"] = m.group(1)
                for card in cardDict:
                    if rootDict["PCI"].endswith(card):
                        rootDict["Card"] = cardDict[card]["Card"]
                        rootDict["Subsys"] = cardDict[card]["Subsys"]
        retval = p.wait()

    def getSysFS(self, dev, rootDict):
        rootDict["ModAlias"] = ""
        rootDict["PCIslot"] = ""
        rootDict["uDriver"] = ""
        ueventFile = '/sys/class/net/{0}/device/uevent'.format(dev)
        if os.path.isfile(ueventFile):
            ueventFH = open(ueventFile, 'r')
            for line in ueventFH:
                [tag,value] = line.strip().split("=")
                if tag == "MODALIAS":
                    rootDict["ModAlias"] = value
                if tag == "DRIVER":
                    rootDict["uDriver"] = value
                if tag == "PCI_SLOT_NAME":
                    rootDict["PCIslot"] = value                
        try:
            rootDict["VendorID"] = open('/sys/class/net/{0}/device/vendor'.format(dev), 'r').read().strip()
        except:
            rootDict["VendorID"] = "Generic"
        try:
            rootDict["Type"] = open('/sys/class/net/{0}/device/device'.format(dev), 'r').read().strip()
        except:
            rootDict["Type"] = "Network adaptor"    
    
    def translateVendorID(self, dev, rootDict):
        vendorID = rootDict["VendorID"]
        if vendorID.startswith("0x"):
            vendorID  = vendorID[2:]
        pciDB = open("/usr/share/hwdata/pci.ids", 'r')
        for line in pciDB:
            m = re.match(r'^{0}\s*(.*)$'.format(vendorID), line)
            if m:
                rootDict["VendorID"] = m.group(1)

    def getNUMA(self, dev, rootDict):
        rootDict["NUMA"] = "--"
        numaFile = '/sys/class/net/{0}/device/numa_node'.format(dev)
        if os.path.isfile(numaFile):
            with open(numaFile, 'r') as file:
                rootDict["NUMA"] = file.read().rstrip()

    def formatTrunk(self, dev, outString):
        vlanString = ""
        for vlanDev in sorted(self.trunkDev):
            if "@" + dev in vlanDev:
                displayName, dummy = vlanDev.split("@")
                vlanString = vlanString + "{0}: {1} ".format(displayName, self.trunkDev[vlanDev]["IPAdd"])
        if vlanString != "":
            outString = outString + self.indent + vlanString + "\n"
        return outString

    def __str__(self):
        headLayout  = "{0:13s}  {1:15s} {2:25s} {3:10s} {4:30s} {5:27s} {6:4s} {7:12s}\n"
        slaveLayout = "{0:13s}  {1:9s} {2:25s} {3:10s} {4:30s} {5:27s} {6:4s} {7:12s}\n"
        cardLayout  = "{0:90s}\n{1}{2}\n"
        NETstring = headLayout.format("Device", "IP Address", "Vendor", "Driver", "Version", "FW", "NUMA", "PCI")
        NETstring = NETstring + self.indent + cardLayout.format("Card", self.indent, "Subsys")
        for device in sorted(self.devices):
            if device.startswith('bond'):
                NETstring = NETstring + headLayout.format(device, self.devices[device]["IPAdd"],
                                                                 self.devices[device]["VendorID"],
                                                                 self.devices[device]["Driver"],
                                                                 self.devices[device]["Version"],
                                                                 self.devices[device]["FW"], 
                                                                 "", ""
                                                                 )
                NETstring = NETstring + self.indent + "Bond Mode: {0}\n".format(self.devices[device]["BondType"])
                if self.devices[device]["BondType"] == "active-backup":
                    NETstring = NETstring[:-1] + self.indent + "Active Slave: {0}\n".format(self.devices[device]["Active"])
                NETstring = self.formatTrunk(device, NETstring)
                for dev in self.devices[device]["SlaveList"]:
                    NETstring = NETstring  + self.indent*2 + slaveLayout.format(dev, 9*"-",
                                                                  self.devices[device]["SlaveList"][dev].get("VendorID", 16*"-"),
                                                                  self.devices[device]["SlaveList"][dev]["Driver"],
                                                                  self.devices[device]["SlaveList"][dev]["Version"],
                                                                  self.devices[device]["SlaveList"][dev]["FW"],
                                                                  self.devices[device]["SlaveList"][dev]["NUMA"],
                                                                  self.devices[device]["SlaveList"][dev]["PCI"],
                                                           )
                    NETstring = NETstring  + self.indent*3 + cardLayout.format(self.devices[device]["SlaveList"][dev]["Card"],
                                                                  self.indent*3,                                                                   
                                                                  self.devices[device]["SlaveList"][dev]["Subsys"]
                                                           )
    
            elif device not in self.globalSlaves:
                NETstring = NETstring + headLayout.format(device, self.devices[device]["IPAdd"],
                                                                 self.devices[device]["VendorID"],
                                                                 self.devices[device]["Driver"],
                                                                 self.devices[device]["Version"],
                                                                 self.devices[device]["FW"],
                                                                 self.devices[device]["NUMA"],
                                                                 self.devices[device]["PCI"],
                                                                 )
                NETstring = self.formatTrunk(device, NETstring)   
                NETstring = NETstring  + self.indent + cardLayout.format(self.devices[device]["Card"],
                                                                 self.indent,
                                                                 self.devices[device]["Subsys"]
                                                                 )
        NETstring = NETstring[:-1]
        return NETstring
#
if __name__ == '__main__':
    MyNet = NETinfo()
    print(MyNet)
