#!/usr/bin/env python3
class COMPinfo:
    def __init__(self):
        try:
            inp = open('/sys/class/dmi/id/sys_vendor', 'r')
        except:
            self.vendor = "Unknown"
        self.vendor = inp.readline().rstrip()        
        try:
            inp = open('/sys/class/dmi/id/product_name', 'r')
        except:
            self.model = "Unknown"
        self.model = inp.readline().rstrip()        

    def __str__(self):
        COMPstring = "Vendor: {0} Model: {1}. ".format(
                    self.vendor, self.model)
        return COMPstring

if __name__ == '__main__':
    MyCOMP = COMPinfo()
    print(MyCOMP)
