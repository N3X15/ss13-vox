# SS13 VOX

TTS-based announcer inspired by Half Life's announcement system.

**This project was originally written in 2013 when I was still learning python, so it's a bit rough around the edges.** I am slowly trying to improve the code.

## Installing

**This system has only been tested on Ubuntu.** Therefore, this should be installed and run on an Ubuntu system. A VM is recommended, but not necessary.

1. Run ```sudo apt install python3.6 && pip install -r requirements.txt``` to install and configure Python 3.6 for Ubuntu.
1. Run ```sudo python3.6 setup.py``` to install and configure SoX, Festival, and oggenc.
  * NOTE: During the install process, setup.py will download and install packages, and install new Festival voices.

## Generating voices

Simply edit voxwords.txt and announcements.txt to taste, and run generate.sh.

Sounds encoded will end up in the sounds directory, alongside a cache directory and a tmp directory. Pauses and beeps/bloops will NOT be generated.

If words come out incorrectly pronounced, add the word to lexicon.txt following the guide at the top of the file. This will generate the required LISP script for you.


# Adding to the List

Simply edit voxwords.txt or announcements.txt and add the desired phrase:

```
wordfile = This is a sample phrase that will be saved to wordfile.ogg
```

To test a phrase as though it were from in-game, run:

```
play sounds/{sarah,connor,report,to,medbay,for,health,inspection}.ogg
```

If it's a single letter, add it to the voxwords.txt as ```a = A.```
