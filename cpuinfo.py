#!/usr/bin/env python3
import re
import glob
from pathlib import Path
import subprocess


def normMem(sizeByte, unitByte=""):
    memUnit = ['B','kB', 'MB', 'GB', 'TB', 'PB']
    if unitByte != "":
        if unitByte == "KB":
            unitByte = "kB"
            unit = memUnit.index(unitByte)
    else:
        unit = 0
    while sizeByte > 1024:
        sizeByte = sizeByte / 1024
        unit += 1
    return round(sizeByte,1), memUnit[unit]

def normFreq(inputHz, unitHz=""):
    freqUnit = ['kHz', 'MHz', 'GHz']
    if unitHz != "":
        unit = freqUnit.index(unitHz)
    else:
        unit = 0
    inputHz = float(inputHz)    
    while inputHz > 1000:
        inputHz = inputHz / 1000
        unit +=1
    return round(inputHz,1), freqUnit[unit]

class CPUinfo:
    def __init__(self):

        numaCores = list()
        model  = set()
        logcpu = 0
        cores = set()
        siblings = set()
        cSize = set()
        coreLayout = ""
        maxkHz = set()
        self.freqBase = "Unknown"


        raw = open('/proc/cpuinfo', 'r')
        for item in raw:
            m = re.match(r'model name\s*:(.*)',item)
            if m:
                model.add(m.group(1).strip())
            m = re.match(r'cache size\s*:(.*)',item)
            if m:
                cSize.add(m.group(1).strip())
            m = re.match(r'processor\s*:(.*)', item)
            if m:
                logcpu = max(logcpu, int(m.group(1)))
            m = re.match(r'cpu cores\s*:(.*)', item)
            if m:
                cores.add(int(m.group(1)))      
            m = re.match(r'siblings\s*:(.*)', item)
            if m:
                siblings.add(int(m.group(1)))   
            m = re.match(r'physical id\s*:(.*)', item)
            if m:
                coreLayout = coreLayout + m.group(1)    

        logcpu += 1

        checkCPU = 0

        while checkCPU < logcpu:
            sdPath = "/sys/devices/system/cpu/cpu{0}/cpufreq/scaling_max_freq".format(checkCPU)
            checkCPU += 1
            try:
               maxkHz.add(Path(sdPath ).read_text().rstrip())
            except:
               maxkHz.add("Unknown")

        dmesgPipe = subprocess.Popen(["dmesg"], stdout=subprocess.PIPE)

        out, err = dmesgPipe.communicate()
        m = re.match(r'(.*)tsc: Detected (.*?) processor', str(out))
        if m:
          inputHz, freqUnit = m.group(2).split()
          normHz, freqUnit = normFreq(inputHz, freqUnit)
          self.freqBase = "{0} {1}".format(normHz, freqUnit) 

        if len(model)*len(cores)*len(siblings)*len(cSize) > 1:
            print("Non Standard Configuration with varying CPU characterics")
            print("Models:", model)
            print("Number of Logical CPUs:", logcpu) 
            print("Number of Cores", cores)
            print("Number of siblings", siblings)
            print("Cache Size:", cSize)
            raise 
        self.model = ' '.join((model.pop()).split())
        self.logcpu = logcpu
        self.coreLayout = coreLayout.strip()
        cRaw, cUnit = cSize.pop().split()
        cNorm, cUnit = normMem(int(cRaw), cUnit)
        self.l3Size = "{0} {1}".format(cNorm, cUnit)
        rawMaxkHz = maxkHz.pop()
        if rawMaxkHz != "Unknown":
            freqMax, freqUnit = normFreq(int(rawMaxkHz))
            self.freqMax = "{0} {1}".format(freqMax, freqUnit)
        else:
            self.freqMax = rawMaxkHz
        if len(cores) == 0: 
            self.cores = None
            self.ht = False
            self.sockets = self.logcpu
        else:
            self.cores =  cores.pop()
            siblings = siblings.pop()
            self.sockets = int(self.logcpu/max(self.cores, siblings))
            if siblings > self.cores:
                self.ht = True
            else:
                self.ht = False   

        globList = glob.glob('/sys/devices/system/node/node*')
        globList.sort()
        for nodeDir in globList:
            numaCores.append(open(nodeDir+'/cpulist', "r").read().strip())
        self.numaCores = numaCores


    def __str__(self):
        CPUstring = "System with {0} logical CPUs of type {1}\n(Base Frequency: {2} Max Frequency: {3}) with {4} Cache\n".format(
                    self.logcpu, self.model, self.freqBase, self.freqMax, self.l3Size)
        if self.cores:
            CPUstring = CPUstring + "with {0} cores each".format(self.cores)
        CPUstring = CPUstring + " on {0} socket(s)".format(self.sockets)
        if self.cores:
            CPUstring = CPUstring + " with Hyperthreading "
            if self.ht:
                CPUstring = CPUstring + "enabled"
            else:
                CPUstring = CPUstring + "disabled"
        if self.sockets > 1:
            CPUstring = CPUstring + "\nCore Layout: {0}".format(self.coreLayout)        
        if len(self.numaCores) > 1:
            NUMAstring = "NUMA domains - "
            for (i, cores) in enumerate(self.numaCores):
                 NUMAstring = NUMAstring + "{0}: {1} ".format(i, cores) 
            CPUstring = CPUstring + "\n" + NUMAstring
        else: 
            CPUstring = CPUstring + "\nnon-NUMA system {0}".format(self.numaCores[0])

                
        return CPUstring

if __name__ == '__main__':
    MyCPU = CPUinfo()
    print(MyCPU)
