# SS13 VOX

TTS-based announcer inspired by Half Life's announcement system.

## Installing

0. **This system has only been tested on Ubuntu.** Therefore, this should be installed and run on an Ubuntu system. A VM is recommended, but not necessary.
1. Run ```git submodule update --init --recursive``` after cloning.
2. Run ```sudo python setup.py``` to install and configure SoX, Festival, and oggenc. 
  * NOTE: During the install process, setup.py will download and install packages, and install new Festival voices.
  
## Generating voices

Simply edit voxwordlist.txt and announcements.txt to taste, and run generate.sh.
