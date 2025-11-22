#!/usr/bin/env python3

class COMPinfo:
    def __init__(self, loadData=None):
#
#  Initialize data fields
#
        self.vendor      = "Unknown"
        self.model       = "Unknown"

        if not loadData:
#
# Retrieve data from local machine
#
            try:
                inp = open('/sys/class/dmi/id/sys_vendor', 'r')
                self.vendor = inp.readline().rstrip()        
            except:
                pass
            try:
                inp = open('/sys/class/dmi/id/product_name', 'r')
                self.model = inp.readline().rstrip()        
            except:
                pass
        else:
#
#  Re-create object from saved dictionary
#
            for key in vars(self):
                setattr(self, key, loadData[key])


    def __str__(self):
        COMPstring = "Vendor: {0} Model: {1}. ".format(
                    self.vendor, self.model)
        return COMPstring

if __name__ == '__main__':
    MyCOMP = COMPinfo()
    print(MyCOMP)
    if False:
        compDict = dict(vendor="DEC", model="PDP-11")
        loadComp = COMPinfo(compDict)
        print(loadComp)


