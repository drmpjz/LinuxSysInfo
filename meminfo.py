#!/usr/bin/env python3
"""
Module to read memory information of a system
"""
import re
import subprocess

def norm_mem(size_byte):
    """
    Make memory sizes human readable
    """
    mem_unit = ['B','kB', 'MB', 'GB', 'TB', 'PB']
    unit = 0
    while size_byte > 1024:
        size_byte = size_byte / 1024
        unit += 1
    return int(size_byte), mem_unit[unit]

def read_udev(self):
    """
    Read memory information from  udevadm
    """
    with subprocess.Popen('udevadm info -e | grep -e MEMORY_DEVICE -e MEMORY_ARRAY',
                          shell=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)  as raw:
        for line in raw.stdout.readlines():
            line = line.decode()
            re_match = re.match(r'E: MEMORY_ARRAY_NUM_DEVICES=(.*)', line)
            if re_match:
                self.max_dimm = int(re_match.group(1).strip())
            re_match = re.match(r'E: MEMORY_ARRAY_MAX_CAPACITY=(.*)', line)
            if re_match:
                size_byte = int(re_match.group(1).strip())
                self.max_mem, self.max_unit = norm_mem(size_byte)
            re_match = re.match(r'E: MEMORY_DEVICE_(.*)_PRESENT=0', line)
            if re_match:
                bank_num = int(re_match.group(1).strip())
                self.empty_list.append(bank_num)
            re_match = re.match(r'E: MEMORY_DEVICE_(.\d*)_SIZE=(.*)', line)
            if re_match:
                bank_num = int(re_match.group(1).strip())
                bank_size, bank_unit =  norm_mem( int(re_match.group(2).strip()))
                self.bank_dict[bank_num] = dict(size=bank_size, unit=bank_unit)
            re_match = re.match(r'E: MEMORY_DEVICE_(.*)_TYPE=(.*)', line)
            if re_match:
                bank_num = int(re_match.group(1).strip())
                if bank_num not in self.empty_list:
                    bank_type = re_match.group(2).strip()
                    self.bank_dict[bank_num]['type'] = bank_type
                    if bank_type == "RAM":
                        self.bank_dict[bank_num]['speed'] = "N.A."
                        self.is_vm = True
            re_match = re.match(r'E: MEMORY_DEVICE_(.*?)_.*SPEED_MTS=(.*)', line)
            if re_match:
                bank_num = int(re_match.group(1).strip())
                if bank_num not in self.empty_list:
                    self.bank_dict[bank_num]['speed'] = re_match.group(2).strip()
            re_match = re.match(r'E: MEMORY_DEVICE_(.*)_MANUFACTURER=(.*)', line)
            if re_match:
                bank_num = int(re_match.group(1).strip())
                if bank_num not in self.empty_list:
                    self.bank_dict[bank_num]['vendor'] = re_match.group(2).strip()
            re_match = re.match(r'E: MEMORY_DEVICE_(.*)_PART_NUMBER=(.*)', line)
            if re_match:
                bank_num = int(re_match.group(1).strip())
                if bank_num not in self.empty_list:
                    self.bank_dict[bank_num]['vendorPart'] = re_match.group(2).strip()

class MEMinfo:
    """
    udevadm contains info about memory DIMMs and
    system capacity
    """
    def __init__(self, load_data=None):

#
#  Initialize data fields
#

        self.max_dimm = self.max_mem = 0
        self.max_unit = ""
        self.empty_list = []
        self.bank_dict = {}
        self.is_vm = False
        self.old_ver = "Old Linux release, memory information not yet supported by udevadm"

        if not load_data:
#
# Retrieve data from local machine
#

            read_udev(self)

            if len(self.bank_dict) != 0:
                self.old_ver = ""

            if self.max_dimm == 0 and self.old_ver == "":
                self.max_dimm = len(self.bank_dict.keys()) + len(self.empty_list)
# Hack since sometimes the information about the last bank is missing
# and memory banks always come in two's....
                if not self.is_vm:
                    self.max_dimm = self.max_dimm + self.max_dimm%2
                    self.empty_list.append(max(self.empty_list)+2)
        else:
#
#  Re-create object from saved dictionary
#
            for key in vars(self):
                setattr(self, key, load_data[key])


    def __str__(self):
        tot_size = 0
        tot_unit = ""
        ref_num = ""
        uniform_mem = True
        if self.old_ver != "":
            return self.old_ver
        for bank_num in sorted(self.bank_dict.keys()):
            tot_size = tot_size + self.bank_dict[bank_num]['size']
            if tot_unit == "":
                tot_unit = self.bank_dict[bank_num]['unit']
            elif tot_unit != self.bank_dict[bank_num]['unit']:
                raise Exception("Inconsitent information on number of DIMMs")
            if ref_num == "":
                ref_num = bank_num
                ref_dict = self.bank_dict[bank_num]
            else:
                for key in ref_dict:
                    if ref_dict[key] != self.bank_dict[bank_num][key]:
                        uniform_mem = False
        if len(self.bank_dict) == 1:
            slot = "Slot"
            module = "Module"
        else:
            slot = "Slots"
            module = "Modules"
        if self.is_vm:
            system_type = "Virtual Machine"
        else:
            system_type = "System"
        mem_str = f"{system_type} with maximum {self.max_mem} {self.max_unit} of memory "
        mem_str = mem_str + f"on {self.max_dimm} banks and {tot_size} {tot_unit} installed.\n"
        if len(self.empty_list) > 0:
            if len(self.empty_list) == 1:
                slot = "Slot"
            else:
                slot = "Slots"
            mem_str = mem_str + f"{slot} {self.empty_list} empty.\n"
            mem_str = mem_str + f"{slot} {sorted(self.bank_dict.keys())} filled with {module}:\n"
        else:
            mem_str = mem_str + "All banks populated.\n"
        if uniform_mem:
            mem_str = mem_str + f"{ref_dict['size']} {ref_dict['unit']} "
            mem_str = mem_str + f"{ref_dict['type']}@{ref_dict['speed']} {ref_dict['vendor']} "
            mem_str = mem_str + f"{ref_dict['vendorPart']}"
        else:
            for bank_num in sorted(self.bank_dict.keys()):
                local_dict = self.bank_dict[bank_num]
                mem_str = mem_str + f"[{bank_num}] {local_dict['size']} "
                mem_str = mem_str + f"{local_dict['unit']} "
                mem_str = mem_str + f"{local_dict['type']}@{local_dict['speed']} "
                mem_str = mem_str + f"{local_dict['vendor']} {local_dict['vendorPart']}\n"
            mem_str = mem_str.rstrip()
        return mem_str

if __name__ == '__main__':
    MyMEM = MEMinfo()
    print(MyMEM)
    if len(str(MyMEM)) == 0:
        memDict = {'max_dimm': 4, 'max_mem': 2.71, 'max_unit': "PB", 'empty_list': [1,2,3],
                   'is_vm': False, 'old_ver': ""}
        memDict["bank_dict"] = {}
        memDict["bank_dict"][0]=dict(size=1, unit="TB", type="USSR2", speed="ludicrous",
                                                vendor="Brooks", vendorPart="1")
        loadMem = MEMinfo(memDict)
        print(loadMem)
