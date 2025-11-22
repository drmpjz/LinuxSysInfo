#!/usr/bin/env python3
import re
import socket
import os.path
import subprocess
import sys

class OSinfo:
    def __init__(self, loadData=None):

#
#  Initialize data fields
#
        self.FQDN      = "unknown.dom"
        self.hostName  = "unknown"
        self.OS        = "Unknown"
        self.OSversion = "Unknown"
        self.kernel    = "42"
        self.TOE       = None

        if not loadData:
#
# Retrieve data from local machine
#
        
            try:
                self.FQDN=socket.gethostbyaddr(socket.gethostname())[0]
            except:
                self.FQDN = socket.gethostname()    
            self.hostName = self.FQDN.split('.')[0]
            if os.path.isfile('/etc/os-release'):
                for line in open('/etc/os-release', 'r'):
                    m = re.match(r'^VERSION_ID\s*=\s*\"(.*)\"$', line)
                    if m:
                        self.OSversion = m.group(1)
                    m = re.match(r'^NAME\s*=\s*(.*)$', line)
                    if m:
                        self.OS = (m.group(1)).replace('"', '')
            elif os.path.isfile('/etc/SuSE-release'):
                for line in open('/etc/SuSE-release', 'r'):
                    m = re.match(r'^VERSION = (.*)$', line)
                    if m:
                        self.OSversion = m.group(1)
                    m = re.match(r'^(.*suse.*?)\s*\d*', line, re.IGNORECASE)
                    if m:
                        self.OS = m.group(1)
            elif os.path.isfile('/etc/redhat-release'):
                for line in open('/etc/redhat-release', 'r'):
                    m = re.match(r'^(.*?) Linux .* release (\d+\.\d+)', line, re.IGNORECASE)
                    if m:
                        self.OS = m.group(1)
                        self.OSversion = m.group(2)
            for line in open('/proc/sys/kernel/osrelease'):
                self.kernel = line.strip()
            try:
                raw = subprocess.Popen('onload --version', shell=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                vstring = raw.stdout.readline()
                self.TOE = (vstring.decode(sys.stdout.encoding)).strip()
            except:
                self.TOE = None
        else:
#
#  Re-create object from saved dictionary
#
            for key in vars(self):
                setattr(self, key, loadData[key])
            

#
# Create human readable output of the OSinfo object
#

    def __str__(self):
        OSstring = "Node {0} (FQDN: {1}) running {2} version {3} with kernel {4}.".format(
                    self.hostName, self.FQDN, self.OS, self.OSversion, self.kernel)
        if self.TOE:
            OSstring = "{0} \n TOE is {1}".format(OSstring, self.TOE)
        else:
            OSstring = "{0} \n No TOE installed.".format(OSstring)        
        return OSstring

if __name__ == '__main__':
    MyOS = OSinfo()
    print(MyOS)
    if False:
        osDict = dict(FQDN="test.dom", hostName="test", OS="Tux", OSversion="Best",
                      kernel="3.141", TOE=6)
        loadOS = OSinfo(osDict)
        print(loadOS)
    
