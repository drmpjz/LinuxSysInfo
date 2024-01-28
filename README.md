# LinuxSysInfo

A few scripts to collect HW info on a Linux system

Sometimes (or often depending on what you do :-) ) you need to quickly check the HW components in a Linux system.

There are already great tools and low levels ways out there to do this, but

* they might need superuser privileges (e.g. dmidecode)
* they might need installation via the system package manager
* the output might not be very userfriendly

The scripts collected here address these issues, i.e.

* no elevated privileges are required to run them
* no special SW needs to be installed, as long as you can bring the files with you and the system has python 3 installed you are good to go
* the output creates a summary of the relevant information

## Examples

> ./compinfo.py  
> Vendor: LENOVO Model: 10AGS0VS01.

> ./cpuinfo.py  
> System with 4 logical CPUs of type Intel(R) Core(TM) i5-4570 CPU @ 3.20GHz  
> with 4 cores each on 1 socket(s) with Hyperthreading disabled  
> non-NUMA system 0-3

> ./cpuinfo.py  
> System with 32 logical CPUs of type Intel(R) Xeon(R) CPU E5-2450L 0 @ 1.80GHz  
> with 8 cores each on 2 socket(s) with Hyperthreading enabled  
> Core Layout: 0 0 0 0 0 0 0 0 1 1 1 1 1 1 1 1 0 0 0 0 0 0 0 0 1 1 1 1 1 1 1 1  
> NUMA domains - 0: 0-7,16-23 1: 8-15,24-31

> ./meminfo.py  
> System with maximum 32 GB of memory on 4 banks and 8 GB installed.  
> Slots [0, 2] empty.  
> Slots [1, 3] filled with Modules:  
> 4 GB DDR3@1600 Ramaxel Technology RMR5030MN68F9F1600

> ./netinfo.py 
> Device  IP Address      Vendor               Driver  Version                        FW                        PCI          Card                                                                                       Subsys
> eth0    10.0.7.37       Intel Corporation    igb     5.14.21-150500.53-default      1.59, 0x800008d2, 1.289.0 0000:02:00.0 Ethernet controller: Intel Corporation I350 Gigabit Network Connection (rev 01)            Hewlett-Packard Company Ethernet 1Gb 4-port 366i Adapter