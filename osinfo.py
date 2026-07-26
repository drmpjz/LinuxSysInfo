#!/usr/bin/env python3
"""
Find (Linux) OS version running on current server
"""
import re
import socket
from pathlib import Path
import platform
import subprocess


class OSinfo:
    """
    Find OS name and version from files in /etc, kernel version from /proc
    Check for TCP offload engine (specifically Solarflare (Enterprise) Onload)
    """
    def __init__(self, load_data=None):

        # Initialize data fields.
        self.fqdn = "unknown.dom"
        self.host_name = "unknown"
        self.os_name = "Unknown"
        self.os_version = "Unknown"
        self.kernel = "42"
        self.toe = None

        if not load_data:

            # Retrieve data from local machine.
            try:
                self.fqdn = socket.gethostbyaddr(socket.gethostname())[0]
            except (socket.herror, socket.gaierror, OSError):
                self.fqdn = socket.gethostname()
            self.host_name = self.fqdn.split('.')[0]

            self.get_osinfo()

            kernel_release = Path('/proc/sys/kernel/osrelease')
            if kernel_release.is_file():
                self.kernel = kernel_release.read_text(encoding='utf-8', errors='replace').strip()
            else:
                self.kernel = platform.release()
            try:
                completed = subprocess.run(
                    ['onload', '--version'],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.toe = completed.stdout.splitlines()[0].strip() if completed.stdout else None
            except (FileNotFoundError, OSError, UnicodeError):
                self.toe = None
        else:

            # Re-create object from saved dictionary.
            for key in vars(self):
                setattr(self, key, load_data[key])

    def get_osinfo(self):
        """
        Version information kept in different files/format depending
        on distribution. Function covers the one I work with, could
        be extended....
        """
        if Path('/etc/os-release').is_file():
            with Path('/etc/os-release').open('r', encoding='utf-8',
                      errors='replace') as os_rel:
                for line in os_rel:
                    match = re.match(r'^VERSION_ID\s*=\s*"(.*)"$', line)
                    if match:
                        self.os_version = match.group(1)
                    match = re.match(r'^NAME\s*=\s*(.*)$', line)
                    if match:
                        self.os_name = match.group(1).replace('"', '')
        elif Path('/etc/SuSE-release').is_file():
            with Path('/etc/SuSE-release').open('r', encoding='utf-8',
                      errors='replace') as suse_release:
                for line in suse_release:
                    match = re.match(r'^VERSION = (.*)$', line)
                    if match:
                        self.os_version = match.group(1)
                    match = re.match(r'^(.*suse.*?)\s*\d*', line, re.IGNORECASE)
                    if match:
                        self.os_name = match.group(1)
        elif Path('/etc/redhat-release').is_file():
            with Path('/etc/redhat-release').open('r', encoding='utf-8',
                      errors='replace') as redhat_release:
                for line in redhat_release:
                    match = re.match(r'^(.*?) Linux .* release (\d+\.\d+)', line, re.IGNORECASE)
                    if match:
                        self.os_name = match.group(1)
                        self.os_version = match.group(2)

# Create human readable output of the OSinfo object

    def __str__(self):
        os_string = (
            f"Node {self.host_name} (FQDN: {self.fqdn}) running {self.os_name} "
            f"version {self.os_version} with kernel {self.kernel}."
        )
        if self.toe:
            os_string = f"{os_string} \n TOE is {self.toe}"
        else:
            os_string = f"{os_string} \n No TOE installed."
        return os_string


if __name__ == '__main__':
    my_os = OSinfo()
    print(my_os)
    if len(str(my_os)) == 0:
        os_dict = dict(fqdn="test.dom", host_name="test", os_name="Tux", os_version="Best",
                       kernel="3.141", toe=6)
        load_os = OSinfo(os_dict)
        print(load_os)
