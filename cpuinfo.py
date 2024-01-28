#!/usr/bin/env python3
import re
import glob

class CPUinfo:
    def __init__(self):

        numaCores = list()
        model  = set()
        logcpu = 0
        cores = set()
        siblings = set()
        coreLayout = ""


        raw = open('/proc/cpuinfo', 'r')
        for item in raw:
            m = re.match('model name\s*:(.*)',item)
            if m:
                model.add(m.group(1).strip())
            m = re.match('processor\s*:(.*)', item)
            if m:
                logcpu = max(logcpu, int(m.group(1)))
            m = re.match('cpu cores\s*:(.*)', item)
            if m:
                cores.add(int(m.group(1)))      
            m = re.match('siblings\s*:(.*)', item)
            if m:
                siblings.add(int(m.group(1)))   
            m = re.match('physical id\s*:(.*)', item)
            if m:
                coreLayout = coreLayout + m.group(1)    

        logcpu += 1
        if len(model)*len(cores)*len(siblings) > 1:
            print("Non Standard Configuration with varying CPU characterics")
            print("Models:", model)
            print("Number of Logical CPUs:", logcpu) 
            print("Number of Cores", cores)
            print("Number of siblings", siblings)
            raise 
        self.model = ' '.join((model.pop()).split())
        self.logcpu = logcpu
        self.coreLayout = coreLayout.strip()
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
        CPUstring = "System with {0} logical CPUs of type {1}\n".format(self.logcpu, self.model)
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
