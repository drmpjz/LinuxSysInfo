#!/usr/bin/env python3
import re
import glob
import subprocess
from pathlib import Path

unkVendor = {'Micron_': 'Micron',
             'SAMSUNG ': 'Samsung',
             'SOLIDIGM ': 'Solidigm'
            }

def normSize(sizeByte):
    memUnit = ['B','kB', 'MB', 'GB', 'TB', 'PB']
    unit = 0
    while sizeByte > 1024:
        sizeByte = sizeByte / 1024
        unit += 1
    return int(sizeByte), memUnit[unit]

class DISKinfo:
    def __init__(self):

        self.isVM = False
        self.diskDict = dict()

        raw = subprocess.Popen('lsblk -P | grep TYPE| grep disk', shell=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for line in raw.stdout.readlines():
            self.oldVer = ""
            line = line.decode()
            m = re.match('NAME="(.*?)"', line)
            if m:
                disk = m.group(1).strip()
                self.diskDict[disk] = dict()
                self.diskDict[disk]["hwRaid"] = "(N)"
            m = re.match('.*SIZE="(.*?)"', line)
            if m:
                size = m.group(1).strip()
                self.diskDict[disk]["size"] = size
        
        for disk in self.diskDict:
            scPath = "/sys/class/block/{}/".format(disk)
#
#           Size in /sys/class/block/<device>/size is in 512 byte blocks
#
            scSize = Path(scPath + "size").read_text().rstrip()
            self.diskDict[disk]["blockTot"] = "{:.1e}".format(int(scSize))
            try:
                scVendor = Path(scPath + "device/vendor").read_text().rstrip()
            except:
                scVendor = "Unknown"
            self.diskDict[disk]["Vendor"] = scVendor    
            try:
                scModel = Path(scPath + "device/model").read_text().rstrip()
            except:
                scModel = "Unknown"
            self.diskDict[disk]["Model"] = scModel
#
#          Guess raid controllers
#
            if ((self.diskDict[disk]["Vendor"] == "HPE" and self.diskDict[disk]["Model"] == "LOGICAL VOLUME") or
                (self.diskDict[disk]["Vendor"] == "BROADCOM") or (self.diskDict[disk]["Vendor"] == "AVAGO")):
               self.diskDict[disk]["hwRaid"] = "(Y)"
    
#
#           Guess disk vendors
#
            if self.diskDict[disk]["Vendor"] == "Unknown":
                for vendor in unkVendor:
                    if self.diskDict[disk]["Model"].startswith(vendor):
                        self.diskDict[disk]["Vendor"] = unkVendor[vendor]
                        self.diskDict[disk]["Model"] = self.diskDict[disk]["Model"][len(vendor):]


    def __str__(self):
        header = "Disk    Size   Blocks  Vendor     Model                          HWRaid\n"
        diskString = header
        for disk in sorted(self.diskDict):
            diskString = diskString + \
                    "{0:7s} {1:6s} {2:7s} {3:10s} {4:30s} {5}\n".format(disk,\
                                                      self.diskDict[disk]["size"],\
                                                      self.diskDict[disk]["blockTot"],\
                                                      self.diskDict[disk]["Vendor"],\
                                                      self.diskDict[disk]["Model"],\
                                                      self.diskDict[disk]["hwRaid"])
        return diskString.rstrip()


if __name__ == '__main__':
    MyDISK = DISKinfo()
    print(MyDISK)
