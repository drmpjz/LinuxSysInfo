#!/usr/bin/env python3
import re
import socket
import os.path
import subprocess
import json
import argparse
from pathlib  import Path
from osinfo   import OSinfo
from compinfo import COMPinfo
from cpuinfo  import CPUinfo 
from meminfo  import MEMinfo
from netinfo  import NETinfo
from diskinfo import DISKinfo

def saveData(objDict):
    dataDict = dict()
    for key in objDict:
        dataDict[key] = vars(objDict[key])
    print(dataDict)
    json.dump(dataDict, open("data.json", "w"), indent = 4)

def loadData(inputFile):
    dataDict = json.load(open(inputFile, "r"))
    return dataDict

parser = argparse.ArgumentParser(prog="sysinfo", 
                                 description="Collect computer system information",
                                 epilog="Thank you for using %(prog)s :-)"
                                )

fileOpt = parser.add_argument_group("File I/O")
fileOpt.add_argument("-s", "--save", metavar=("<output.json>"), help="Dump system data to JSON file")
fileOpt.add_argument("-l", "--load", metavar=("<input.json>"), help="Load system data from JSON file")

generalOpt = parser.add_argument_group("General options")
generalOpt.add_argument("-q", "--quiet", help="Suppress output to terminal", action="store_true")
generalOpt.add_argument("--version", action="version", version="%(prog)s 0.1.2")

args = parser.parse_args()


print(args.save)
partList = ["OS", "Comp", "CPU", "RAM", "Network", "Disk"]


if args.load:
    inputFile = Path(args.load)
    if not inputFile.is_file():
        parser.exit(1, message="Input file {0} does not exist\n".format(args.load))
    else:
        sysDict = loadData(args.load)
else:
    sysDict = dict()
    sysDict["OS"]      = OSinfo()
    sysDict["Comp"]    = COMPinfo()
    sysDict["CPU"]     = CPUinfo()
    sysDict["RAM"]     = MEMinfo()
    sysDict["Network"] = NETinfo()
    sysDict["Disk"]    = DISKinfo()

if args.save:
    saveData(sysDict)

if not args.quiet:
    for part in partList:
        print(sysDict[part])
