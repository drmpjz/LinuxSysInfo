#!/usr/bin/env python3
"""
Collect information about CPU in a system
"""
import re
import glob
from pathlib import Path
import subprocess
import sys

def norm_mem(size_byte, unit_byte=""):
    """
    Convert number of bytes to nearest SI class
    """
    mem_unit = ['B','kB', 'MB', 'GB', 'TB', 'PB']
    if unit_byte != "":
        if unit_byte == "KB":
            unit_byte = "kB"
            unit = mem_unit.index(unit_byte)
    else:
        unit = 0
    while size_byte > 1024:
        size_byte = size_byte / 1024
        unit += 1
    return round(size_byte,1), mem_unit[unit]

def norm_freq(input_hz, unit_hz=""):
    """
    Convert frequency in Hz to nearest SI class
    """
    freq_unit = ['kHz', 'MHz', 'GHz']
    if unit_hz != "":
        unit = freq_unit.index(unit_hz)
    else:
        unit = 0
    input_hz = float(input_hz)
    while input_hz > 1000:
        input_hz = input_hz / 1000
        unit +=1
    return round(input_hz,1), freq_unit[unit]

def read_cpuinfo(self):
    """
    Read various CPU characteristics from /proc/cpuinfo
    """
    model  = set()
    self.core_attr["log"] = 0
    cores = set()
    siblings = set()
    c_size = set()
    core_layout = ""
    max_khz = set()


    with open('/proc/cpuinfo', 'r', encoding='us-ascii') as raw:
        for item in raw:
            re_match = re.match(r'model name\s*:(.*)',item)
            if re_match:
                model.add(re_match.group(1).strip())
            re_match = re.match(r'cache size\s*:(.*)',item)
            if re_match:
                c_size.add(re_match.group(1).strip())
            re_match = re.match(r'processor\s*:(.*)', item)
            if re_match:
                self.core_attr["log"] = max(self.core_attr["log"], int(re_match.group(1)))
            re_match = re.match(r'cpu cores\s*:(.*)', item)
            if re_match:
                cores.add(int(re_match.group(1)))
            re_match = re.match(r'siblings\s*:(.*)', item)
            if re_match:
                siblings.add(int(re_match.group(1)))
            re_match = re.match(r'physical id\s*:(.*)', item)
            if re_match:
                socket = re_match.group(1)
                core_layout = core_layout + socket
                self.sockets = max(self.sockets, int(socket)+1)

    self.core_attr["log"] += 1

    plausi_check(model, cores, siblings, c_size, self.core_attr["log"])

    if len(cores) == 0:
        self.core_attr["phys"] = None
    else:
        self.core_attr["phys"]= cores.pop()

    self.model = ' '.join((model.pop()).split())


    c_raw, c_unit = c_size.pop().split()
    c_norm, c_unit = norm_mem(int(c_raw), c_unit)
    self.l3_size = f"{c_norm} {c_unit}"

    return  siblings, core_layout, max_khz

def read_dmesg(self):
    """
    Parse dmesg file to retrieve cpu frequency information
    """
    with subprocess.Popen(["dmesg"], stdout=subprocess.PIPE) as dmesg_pipe:
        out, err = dmesg_pipe.communicate()

    if err is not  None:
        print("Could not read dmesg")
        print(f"Error condiition: {err}")
        sys.exit()

    re_match = re.match(r'(.*)tsc: Detected (.*?) processor', str(out))
    if re_match:
        input_hz, freq_unit = re_match.group(2).split()
        norm_hz, freq_unit = norm_freq(input_hz, freq_unit)
        self.freq["base"] = f"{norm_hz} {freq_unit}"

def plausi_check(model, cores, siblings, c_size, logcpu):
    """G
    Check if retrieved CPU information is plausible
    """
    if len(model)*len(cores)*len(siblings)*len(c_size) > 1:
        print("Non Standard Configuration with varying CPU characterics")
        print("Models:", model)
        print("Number of Logical CPUs:", logcpu)
        print("Number of Cores", cores)
        print("Number of siblings", siblings)
        print("Cache Size:", c_size)
        raise ValueError("Unexpected Core setup")

class CPUinfo:
    """
    Collect and store information about CPU
    """
    def __init__(self, load_data=None):
#
#  Initialize data fields
#
        self.model = self.l3_size =  "Unknown"
        self.freq        = dict(max = "Unknown", base = "Unkown")
        self.core_attr   = dict(log = 0, phys = None, hyp_th = False)
        self.core_layout = "No Cores"
        self.sockets     = 1
        self.numa_cores  = [0]

        if not load_data:
#
# Retrieve data from local machine
#

            numa_cores = []

            siblings,  core_layout, max_khz = read_cpuinfo(self)
            check_cpu = 0

            while check_cpu < self.core_attr["log"]:
                sd_path = f"/sys/devices/system/cpu/cpu{check_cpu}/cpufreq/scaling_max_freq"
                check_cpu += 1
                try:
                    max_khz.add(Path(sd_path).read_text(encoding='us-ascii').rstrip())
                except OSError:
                    max_khz.add("Unknown")


            read_dmesg(self)

            self.core_layout = core_layout.strip()
            raw_max_khz = max_khz.pop()
            if raw_max_khz != "Unknown":
                freq_max, freq_unit = norm_freq(int(raw_max_khz))
                self.freq["max"] = f"{freq_max} {freq_unit}"
            else:
                self.freq["max"] = raw_max_khz
            if self.core_attr["phys"] is None:
                self.core_attr["hyp_th"]= False
                self.sockets = self.core_attr["log"]
            else:
                siblings = siblings.pop()
                if siblings > self.core_attr["phys"]:
                    self.core_attr["hyp_th"] = True
                else:
                    self.core_attr["hyp_th"] = False

            glob_list = glob.glob('/sys/devices/system/node/node*')
            glob_list.sort()
            for node_dir in glob_list:
                cpu_list_file = node_dir+'/cpulist'
                numa_cores.append(open(cpu_list_file, "r", encoding="us-ascii").read().strip())
            self.numa_cores = numa_cores
        else:
#
#  Re-create object from saved dictionary
#
            for key in vars(self):
                setattr(self, key, load_data[key])


    def __str__(self):
        cpu_string = f"System with {self.core_attr['log']} logical CPUs of type {self.model}\n"
        cpu_string = cpu_string + f'(Base Frequency: {self.freq["base"]} '
        cpu_string = cpu_string + f'Max Frequency: {self.freq["max"]}) '
        cpu_string = cpu_string + f"with {self.l3_size} Cache\n"
        if self.core_attr['phys']:
            cpu_string = cpu_string + f"with {self.core_attr['phys']} cores each"
        if self.sockets > 1:
            socket_string = "sockets"
        else:
            socket_string = "socket"
        cpu_string = cpu_string + f" on {self.sockets} {socket_string}"
        if self.core_attr['phys']:
            cpu_string = cpu_string + " with Hyperthreading "
            if self.core_attr["hyp_th"]:
                cpu_string = cpu_string + "enabled"
            else:
                cpu_string = cpu_string + "disabled"
        if self.sockets > 1:
            cpu_string = cpu_string + f"\nCore Layout: {self.core_layout}"
        if len(self.numa_cores) > 1:
            numa_string = "NUMA domains - "
            for (i, cores) in enumerate(self.numa_cores):
                numa_string = numa_string + f"{i}: {cores} "
            cpu_string = cpu_string + "\n" + numa_string
        else:
            cpu_string = cpu_string + f"\nnon-NUMA system {self.numa_cores[0]}"

        return cpu_string

if __name__ == '__main__':
    MyCPU = CPUinfo()
    print(MyCPU)
    if len(str(MyCPU)) == 0:
        freqDict = {"base": "1 Hz", "max": "Unknown"}
        coreDict = {"phys": 2, "hyp_th": False}
        cpuDict = {"model": "Sumerian Claytablet", "freq": freqDict, "core_layout": "0 1"}
        cpuDict.update(core_att=coreDict)
        cpuDict.update(dict(l3_size="1 kB", sockets=1))
        cpuDict.update(dict(numa_cores=[0,1]))
        loadCPU = CPUinfo(cpuDict)
        print(loadCPU)
