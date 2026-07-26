#!/usr/bin/env python3
"""
Module to read Vendor/Model of a system
"""
class COMPinfo:
    """
    Either retrive data from dmi info or read from existing
    dictionary
    """
    def __init__(self, load_data=None):
#
#  Initialize data fields
#
        self.vendor      = "Unknown"
        self.model       = "Unknown"

        if not load_data:
#
# Retrieve data from local machine
#
            try:
                with open('/sys/class/dmi/id/sys_vendor', 'r', encoding="us-ascii") as inp:
                    self.vendor = inp.readline().rstrip()
            except OSError:
                pass
            try:
                with open('/sys/class/dmi/id/product_name', 'r',  encoding="us-ascii") as inp:
                    self.model = inp.readline().rstrip()
            except OSError:
                pass
        else:
#
#  Re-create object from saved dictionary
#
            for key in vars(self):
                setattr(self, key, load_data[key])


    def __str__(self):
        comp_string = f"Vendor: {self.vendor} Model: {self.model}. "
        return comp_string

if __name__ == '__main__':
    MyCOMP = COMPinfo()
    print(MyCOMP)
    if len(str(MyCOMP)) == 0:
        compDict = dict(vendor="DEC", model="PDP-11")
        loadComp = COMPinfo(compDict)
        print(loadComp)
