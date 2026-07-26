#!/usr/bin/env python3
"""
Module to read information about disks used in a system
"""
import re
import subprocess
from pathlib import Path


def infer_values(self, disk):
    """
    Make some educated guesses resp. infer vendor from disk models
    """
    unk_vendor = {'Micron_': 'Micron',
                 'SAMSUNG ': 'Samsung',
                 'SOLIDIGM ': 'Solidigm'
                }
#
#          Guess raid controllers
#
    if ((self.disk_d[disk]["Model"] == "LOGICAL VOLUME") or
        self.disk_d[disk]["Vendor"] in ("BROADCOM", "AVAGO")):
        self.disk_d[disk]["hwRaid"] = "(Y)"

#
#           Guess disk vendors
#
    if self.disk_d[disk]["Vendor"] == "Unknown":
        for vendor in unk_vendor.items():
            if self.disk_d[disk]["Model"].startswith(vendor):
                self.disk_d[disk]["Vendor"] = unk_vendor[vendor]
                self.disk_d[disk]["Model"] = self.disk_d[disk]["Model"][len(vendor):]

class DISKinfo:
    """
    Read lsblk output and /sys/class/block to get
    device information. Sanitize information for
    vendor/model in known cases
    """
    def __init__(self, load_data=None):

#
#  Initialize data fields
#

        self.disk_d = {}

        if not load_data:
#
# Retrieve data from local machine
#

            with subprocess.Popen('lsblk -P | grep TYPE| grep disk', shell=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE) as raw:
                for line in raw.stdout.readlines():
                    line = line.decode()
                    re_match = re.match(r'NAME="(.*?)"', line)
                    if re_match:
                        disk = re_match.group(1).strip()
                        self.disk_d[disk] = {}
                        self.disk_d[disk]["hwRaid"] = "(N)"
                    re_match = re.match(r'.*SIZE="(.*?)"', line)
                    if re_match:
                        size = re_match.group(1).strip()
                        self.disk_d[disk]["size"] = size

            for disk in self.disk_d:
                sc_path = f"/sys/class/block/{disk}/"
#
#           Size in /sys/class/block/<device>/size is in 512 byte blocks
#
                sc_size = Path(sc_path + "size").read_text(encoding="us-ascii").rstrip()
                self.disk_d[disk]["blockTot"] = f"{int(sc_size):.1e}"
                try:
                    vendor = Path(sc_path + "device/vendor").read_text(encoding="us-ascii").rstrip()
                except OSError:
                    vendor = "Unknown"
                self.disk_d[disk]["Vendor"] = vendor
                try:
                    model = Path(sc_path + "device/model").read_text(encoding="us-ascii").rstrip()
                except OSError:
                    model = "Unknown"
                self.disk_d[disk]["Model"] = model

                infer_values(self, disk)
        else:
#
#  Re-create object from saved dictionary
#
            for key in vars(self):
                setattr(self, key, load_data[key])


    def __str__(self):
        header = "Disk    Size   Blocks  Vendor     Model                          HWRaid\n"
        disk_string = header
        for disk in sorted(self.disk_d):
            disk_string = disk_string + \
                    f"{disk:7s} {self.disk_d[disk]['size']:6s} " + \
                    f"{self.disk_d[disk]['blockTot']:8s}" + \
                    f"{self.disk_d[disk]['Vendor']:10s} {self.disk_d[disk]['Model']:30s} " + \
                    f"{self.disk_d[disk]['hwRaid']}\n"
        return disk_string.rstrip()


if __name__ == '__main__':
    MyDISK = DISKinfo()
    print(MyDISK)
    if len(str(MyDISK)) == 0:
        testDict = dict(disk_d=dict(World=dict(hwRaid="(N)", size="42P", blockTot="3.e+100",
                                                     Vendor="Turtle", Model="Magic")))
        loadDisk = DISKinfo(testDict)
        print(loadDisk)
