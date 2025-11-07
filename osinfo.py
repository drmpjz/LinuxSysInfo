#!/usr/bin/env python3
import re
import socket
import os.path
import subprocess

class OSinfo:
    def __init__(self):
        try:
            self.FQDN=socket.gethostbyaddr(socket.gethostname())[0]
        except:
            self.FQDN = socket.gethostname()    
        self.hostName = self.FQDN.split('.')[0]
        self.OS = "Unknown"
        self.OSversion = "Unknown"
        if os.path.isfile('/etc/os-release'):
            for line in open('/etc/os-release', 'r'):
                m = re.match(r'^VERSION_ID\s*=\s*\"(.*)\"$', line)
                if m:
                    self.OSversion = m.group(1)
                m = re.match(r'^NAME\s*=\s*(.*)$', line)
                if m:
                    self.OS = m.group(1)
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
            self.TOE = (vstring.decode()).strip()
        except:
            self.TOE = None
    def __str__(self):
        OSstring = "Node {0} (FQDN: {1}) running {2} version {3} with kernel {4}.".format(
                    self.hostName, self.FQDN, self.OS, self.OSversion, self.kernel)
        if self.TOE:
            OSstring = OSstring +  " TOE is {0}".format(self.TOE)
        else:
            OSstring = OSstring + " No TOE installed."        
        return OSstring

if __name__ == '__main__':
    MyOS = OSinfo()
    print(MyOS)
