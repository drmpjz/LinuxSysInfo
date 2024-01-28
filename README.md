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
