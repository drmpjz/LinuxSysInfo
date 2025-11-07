#!/usr/bin/env python3
import re
import glob
import subprocess

def normMem(sizeByte):
    memUnit = ['B','kB', 'MB', 'GB', 'TB', 'PB']
    unit = 0
    while sizeByte > 1024:
        sizeByte = sizeByte / 1024
        unit += 1
    return int(sizeByte), memUnit[unit]

class MEMinfo:
    def __init__(self):

        self.maxDIMM = self.maxMem = 0
        self.maxUnit = ""
        self.emptyList = list()
        self.bankDict = dict()
        self.isVM = False
        self.oldVer = "Old Linux release, memory information not yet supported by udevadm"


        raw = subprocess.Popen('udevadm info -e | grep -e MEMORY_DEVICE -e MEMORY_ARRAY', shell=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for line in raw.stdout.readlines():
            line = line.decode()
            m = re.match(r'E: MEMORY_ARRAY_NUM_DEVICES=(.*)', line)
            if m:
                self.maxDIMM = int(m.group(1).strip())
            m=re.match(r'E: MEMORY_ARRAY_MAX_CAPACITY=(.*)', line)
            if m:
                sizeByte = int(m.group(1).strip())
                self.maxMem, self.maxUnit = normMem(sizeByte)
            m=re.match(r'E: MEMORY_DEVICE_(.*)_PRESENT=0', line)
            if m:
                bankNum = int(m.group(1).strip())
                self.emptyList.append(bankNum)
            m=re.match(r'E: MEMORY_DEVICE_(.\d*)_SIZE=(.*)', line)
            if m:
                bankNum = int(m.group(1).strip())
                bankSize, bankUnit =  normMem( int(m.group(2).strip()))
                self.bankDict[bankNum] = dict(size=bankSize, unit=bankUnit)
            m=re.match(r'E: MEMORY_DEVICE_(.*)_TYPE=(.*)', line)
            if m:
                bankNum = int(m.group(1).strip())
                if bankNum not in self.emptyList:
                    bankType = m.group(2).strip()
                    self.bankDict[bankNum]['type'] = bankType
                    if bankType == "RAM":
                       self.bankDict[bankNum]['speed'] = "N.A."
                       self.isVM = True
            m=re.match(r'E: MEMORY_DEVICE_(.*?)_.*SPEED_MTS=(.*)', line)
            if m:
                bankNum = int(m.group(1).strip())
                if bankNum not in self.emptyList:
                    self.bankDict[bankNum]['speed'] = m.group(2).strip()
            m=re.match(r'E: MEMORY_DEVICE_(.*)_MANUFACTURER=(.*)', line)
            if m:
                bankNum = int(m.group(1).strip())
                if bankNum not in self.emptyList:
                    self.bankDict[bankNum]['vendor'] = m.group(2).strip()
            m=re.match(r'E: MEMORY_DEVICE_(.*)_PART_NUMBER=(.*)', line)
            if m:
                bankNum = int(m.group(1).strip())
                if bankNum not in self.emptyList:
                    self.bankDict[bankNum]['vendorPart'] = m.group(2).strip()

        if len(self.bankDict) != 0:
            self.oldVer = ""

        if self.maxDIMM == 0 and self.oldVer == "":
            self.maxDIMM = len(self.bankDict.keys()) + len(self.emptyList)
# Hack since sometimes the information about the last bank is missing
# and memory banks always come in two's....
            if not self.isVM:
                self.maxDIMM = self.maxDIMM + self.maxDIMM%2
                self.emptyList.append(max(self.emptyList)+2)

    def __str__(self):
        totSize = 0
        totUnit = ""
        refNum = ""
        uniformMem = True
        if self.oldVer != "":
            return self.oldVer    
        for bankNum in sorted(self.bankDict.keys()):  
            totSize = totSize + self.bankDict[bankNum]['size']
            if totUnit == "":
                totUnit = self.bankDict[bankNum]['unit']
            elif totUnit != self.bankDict[bankNum]['unit']:
                raise
            if refNum == "":
                refNum = bankNum
                refDict = self.bankDict[bankNum]
            else:
                for key in refDict:
                    if refDict[key] != self.bankDict[bankNum][key]:
                        uniformMem = False
        if len(self.bankDict) == 1:
            slot = "Slot"
            module = "Module"
        else:
            slot = "Slots"
            module = "Modules"
        if self.isVM:
            systemType = "Virtual Machine"
        else:
            systemType = "System"
        MEMstring = "{5} with maximum {0} {1} of memory on {2} banks and {3} {4} installed.\n".format(self.maxMem, 
                    self.maxUnit, self.maxDIMM, totSize, totUnit, systemType)
        if len(self.emptyList) > 0:
            if len(self.emptyList) == 1:
                slot = "Slot"
            else:
                slot = "Slots"    
            MEMstring = MEMstring + "{1} {0} empty.\n".format(self.emptyList, slot)
        else:
            MEMstring = MEMstring + "All banks populated.\n"
        if len(self.emptyList) != 0:      
                MEMstring = MEMstring + "{0} {1} filled with {2}:\n".format(slot, sorted(self.bankDict.keys()), module)
        if uniformMem:        
            MEMstring = MEMstring + "{0} {1} {2}@{3} {4} {5}".format(refDict['size'], refDict['unit'], refDict['type'],
                                                                     refDict['speed'], refDict['vendor'], refDict['vendorPart'])                
        else:
            for bankNum in sorted(self.bankDict.keys()): 
                MEMstring = MEMstring + "[{6}] {0} {1} {2}@{3} {4} {5}\n".format(self.bankDict[bankNum]['size'],
                                                                               self.bankDict[bankNum]['unit'],
                                                                               self.bankDict[bankNum]['type'],
                                                                               self.bankDict[bankNum]['speed'],
                                                                               self.bankDict[bankNum]['vendor'],
                                                                               self.bankDict[bankNum]['vendorPart'],
                                                                               bankNum)
            MEMstring = MEMstring.rstrip()    
        return MEMstring

if __name__ == '__main__':
    MyMEM = MEMinfo()
    print(MyMEM)
