#!/usr/bin/env python3
"""
Collect system overview
"""
import json
import argparse
from pathlib  import Path
from osinfo   import OSinfo
from compinfo import COMPinfo
from cpuinfo  import CPUinfo
from meminfo  import MEMinfo
from netinfo  import NETinfo
from diskinfo import DISKinfo

def save_data(obj_dict):
    """
    Save internal data structure as JSON file
    """
    data_dict = {}
    for key in obj_dict:
        data_dict[key] = vars(obj_dict[key])
    print(data_dict)
    json.dump(data_dict, open("data.json", "w", encoding='utf-8'), indent = 4)

def load_data(load_file):
    """
    Restore internal data structure from JSON file
    """
    data_dict = json.load(open(load_file, "r", encoding='utf-8'))
    return data_dict

parser = argparse.ArgumentParser(prog="sysinfo",
                                 description="Collect computer system information",
                                 epilog="Thank you for using %(prog)s :-)"
                                )

fileOpt = parser.add_argument_group("File I/O")
fileOpt.add_argument("-s", "--save", metavar=("<output.json>"),
                     help="Dump system data to JSON file")
fileOpt.add_argument("-l", "--load", metavar=("<input.json>"),
                     help="Load system data from JSON file")

generalOpt = parser.add_argument_group("General options")
generalOpt.add_argument("-q", "--quiet", help="Suppress output to terminal", action="store_true")
generalOpt.add_argument("--version", action="version", version="%(prog)s 0.1.3")

args = parser.parse_args()


partList = ["OS", "Comp", "CPU", "RAM", "Network", "Disk"]


if args.load:
    input_file = Path(args.load)
    if not input_file.is_file():
        parser.exit(1, message=f"Input file {args.load} does not exist\n")
    else:
        sysDict = load_data(args.load)
else:
    sysDict = {}
    sysDict["OS"]      = OSinfo()
    sysDict["Comp"]    = COMPinfo()
    sysDict["CPU"]     = CPUinfo()
    sysDict["RAM"]     = MEMinfo()
    sysDict["Network"] = NETinfo()
    sysDict["Disk"]    = DISKinfo()

if args.save:
    save_data(sysDict)

if not args.quiet:
    for part in partList:
        print(sysDict[part])
