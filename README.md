# SS13 VOX

TTS-based announcer inspired by Half Life's announcement system.

**This project was originally written in 2013 when I was still learning python, so it's a bit rough around the edges.** I am slowly trying to improve the code.

**I AM UNABLE TO GET THIS WORKING ON UBUNTU 22.04 LTS DUE TO A PROBLEM WITH UBUNTU AND VIRTUALBOX.**  Please be patient while I work on this.

## Installing

**This system has only been tested on Ubuntu 20.04 (focal).** Therefore, this should be installed and run on an Ubuntu system. A VM (such as VMWare, VirtualBox, or Xen) is recommended, but not necessary.

1. Run `sudo apt install python3 && pip3 install -U poetry && poetry install --no-root` to install and configure Python 3 for Ubuntu.
1. Run `sudo python3 setup.py` to install and configure SoX, Festival, and oggenc.
  * NOTE: During the install process, setup.py will download and install operating system packages, and install new Festival voices.

## Generating Sounds

### /vg/-based Servers
Simply edit `wordlists/vg` to taste, and run generate.sh.

Everything you need will end up in `dist/`. Note that old HL VOX sounds like `beep`, `bloop`, etc are not included and are expected to be in `sound/vox/`.

If words come out incorrectly pronounced, add the word to lexicon.txt following the guide at the top of the file. This will generate the required LISP script for you.

### TG-based Servers
1. Open `config.yml`
1. Change `codebase` to `tg` so it'll generate the correct code for your server.

You may also wish to duplicate `announcements.txt` and `voxwords.txt` and modify them for TG's needs.  If you choose to do this, make sure to point to the new files in `config.yml`.

# Changing Voices
You can select which voice to use for each sex in `config.yml` in the `voices:` list.

## Voice Sexes
<table><tr><th>Sex</th><th>Meaning</th></tr>
<tr><th><code>default</code></th><td>Non-AI automated announcements, like <code>vox_login</code>.</td></tr>
<tr><th><code>fem</code></th><td>Feminine voice</td></tr>
<tr><th><code>mas</code></th><td>Masculine voice</td></tr>
</table>

## Voice IDs
Each voice requires manual tuning and fuckery in order to work with the standardized echoes and reverbs added later during generation, so not every voice in festival is available here.

<table><tr><th>ID</th><th>Sex</th><th>Festival ID</th><th>Notes</th></tr>
<tr><th><code>us-clb</code></th><td>F</td><td><code>nitech_us_clb_arctic_hts</code></td><td>Used by default on /vg/.  US female with no accent.</td></tr>
<tr><th><code>us-rms</code></th><td>M</td><td><code>nitech_us_rms_arctic_hts</code></td><td>Used by default on /vg/.  US male with no accent, sounds kinda like DECTalk without post-processing.</td></tr>
<tr><th><code>us-slt</code></th><td>F</td><td><code>nitech_us_slt_arctic_hts</code></td><td>US female with midwestern accent and flatter voice. Buggy at times: Can drop to a british accent.</td></tr>
</table>

# Adding to the List

Simply edit the files in `wordlist/` according to the following format:

```
apple
zebra
# Comment bound to wordfile. It'll follow it around when organize.py is run.
wordfile = This is a sample phrase that will be saved to wordfile.ogg
```

If it's a single letter, add it to the voxwords.txt as ```a = A.```

# Testing Phrases

To test a phrase as though it were from in-game, run (replace `$SEX` with `fem` or `mas`):

```shell
$ python3 test.py --voice=$SEX sarah connor please report to medbay for johnson inspection
```

This will call `play` for you.

# Fixing Generated Code

Coding standards change over time, and this repo is relatively slow to update.  

If you need different dm output, please see `templates/` and edit the appropriate file (`vglist.jinja` or `tglist.jinja`).  Once done, run `generate.sh` again.  Afterwards, please send us a PR so everyone else gets the update.