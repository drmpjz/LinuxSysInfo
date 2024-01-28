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
            m = re.match('^(\w{2}\:\w{2}\.\d) (.*)\s*$', line)
            if m:
                slot = m.group(1)
                Ctype = m.group(2)
                cardDict[slot] = dict({"Card": Ctype})
            m = re.match('^\s+Subsystem: (.*)\s*$', line)
            if m:
                cardDict[slot]["Subsys"] = m.group(1)
                         
            
        raw = os.popen('/sbin/ip addr show', 'r')

        self.devices = dict()
        self.currDev = ""

        for item in raw:
            m = re.match('^\d+: (.*):', item)
            if m:
#
# Check (and potentially discard) previous device
#

                if self.devices.get(self.currDev, "") != "" and \
                   self.devices[self.currDev].get("IPAdd", "") == "":
                    self.devices.pop(self.currDev, None)
                self.currDev = m.group(1)
                self.devices[self.currDev] = dict()
            m = re.match('^\s+link/(ether|infiniband) (\w{2}:.*) brd', item)
            if m:
                self.devices[self.currDev]["MAC"] = str.upper(m.group(2))
            m = re.match('^\s+inet (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/\d{1,2}', item)
            if m:
                ipAdd = m.group(1)
                if ipAdd != "127.0.0.1":
                    self.devices[self.currDev]["IPAdd"] = ipAdd
                    self.getEthTool(self.currDev, cardDict, self.devices[self.currDev])
                    self.getSysFS(self.currDev, self.devices[self.currDev])                    
                        
#                   
# Check (and potentially discard) final device
#
        if self.devices.get(self.currDev, "") != "" and \
           self.devices[self.currDev].get("IPAdd", "") == "":        
            self.devices.pop(self.currDev, None)

#
# Now check if we found any bonding devices
#
        for dev in self.devices:
            if dev.startswith('bond'):
                self.devices[dev]["SlaveList"] = dict()
                bondInfo = open('/proc/net/bonding/{0}'.format(dev), 'r')
                for line in bondInfo:
                    m = re.match('^Currently Active Slave: (.*)$', line)
                    if m:
                        self.devices[dev]["Active"] = m.group(1)
                    m = re.match('^Slave Interface: (.*)$', line) 
                    if m:
                        slaveDevice = m.group(1)
                        self.devices[dev]["SlaveList"][slaveDevice] = dict()
                        self.getEthTool(slaveDevice, cardDict, self.devices[dev]["SlaveList"][slaveDevice])
                        self.getSysFS(slaveDevice, self.devices[dev]["SlaveList"][slaveDevice])
                        p = subprocess.Popen('/sbin/ip addr show  ' + slaveDevice, shell=True,
                                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        for line in p.stdout.readlines():
                            m = re.match('^\s+link/(ether|infiniband) (\w{2}:.*) brd', line)
                            if m:
                                self.devices[dev]["SlaveList"][slaveDevice]["MAC"] = str.upper(m.group(2))
            else:
                self.translateVendorID(dev, self.devices[dev])


        
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
            m = re.match('^driver: (.*)$', line)
            if m:
                rootDict["Driver"] = m.group(1)
            m = re.match('^version: (.*)$', line)
            if m:
                rootDict["Version"] = m.group(1)
            m = re.match('^firmware-version: (.*)$', line)
            if m:
                rootDict["FW"] = m.group(1)
            m = re.match('^bus-info: (.*)$', line)
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
            m = re.match('^{0}\s*(.*)$'.format(vendorID), line)
            if m:
                rootDict["VendorID"] = m.group(1)

                        
    def __str__(self):
        NETstring = "{0:6s}  {1:15s} {2:20s} {3:7s} {4:30s} {5:25s} {6:12s} {7:90s} {8}\n".format("Device", "IP Address", "Vendor",
                                                                                                  "Driver", "Version", "FW", "PCI",          
                                                                                                  "Card", "Subsys")
        for device in self.devices:
            NETstring = NETstring + "{0:6s}  {1:15s} {2:20s} {3:7s} {4:30s} {5:25s} {6:12s} {7:90s} {8}\n".format(device,
                                                                     self.devices[device]["IPAdd"],
                                                                     self.devices[device]["VendorID"],
                                                                     self.devices[device]["Driver"],
                                                                     self.devices[device]["Version"],
                                                                     self.devices[device]["FW"],
                                                                     self.devices[device]["PCI"],
                                                                     self.devices[device]["Card"],
                                                                     self.devices[device]["Subsys"]
                                                                   )  
            if device.startswith('bond'):
                NETstring = NETstring + "    Active Slave: {0}\n".format(self.devices[device]["Active"])
                for dev in self.devices[device]["SlaveList"]:
                    NETstring = NETstring + "{0:6s} {1:15s} {2:20s} {3:7s} {4:30s} {5:19s} {6:12s} {7:90s} {8}\n".format(dev, 
                                                                                  16*"-",
                                                                                  self.devices[device]["SlaveList"][dev].get("VendorID", 16*"-"),
                                                                                  self.devices[device]["SlaveList"][dev]["Driver"],
                                                                                  self.devices[device]["SlaveList"][dev]["Version"],
                                                                                  self.devices[device]["SlaveList"][dev]["FW"],
                                                                                  self.devices[device]["SlaveList"][dev]["PCI"],
                                                                                  self.devices[device]["SlaveList"][dev]["Card"],
                                                                                  self.devices[device]["SlaveList"][dev]["Subsys"]
                                                                                  )
        NETstring = NETstring[:-1]
        return NETstring
#
if __name__ == '__main__':
    MyNet = NETinfo()
    print(MyNet)
