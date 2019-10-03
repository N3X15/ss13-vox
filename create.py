import argparse
import collections
import hashlib
import jinja2
import json
import logging
import os
import re
import subprocess
import sys
import time
import multiprocessing
from typing import Optional
from enum import IntFlag

script_dir = os.path.dirname(os.path.realpath(__file__))

from buildtools import os_utils, log
from buildtools.config import YAMLConfig, BaseConfig

from ss13vox.phrase import Phrase, EPhraseFlags, ParsePhraseListFrom
from ss13vox.pronunciation import Pronunciation, DumpLexiconScript, ParseLexiconText

"""
Usage:
    $ python create.py voxwords.txt

Requires festival, sox, and vorbis-tools.

create.py - Uses festival to generate word oggs.

Copyright 2013-2019 Rob "N3X15" Nelson <nexis@7chan.org>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

###############################################
# CONFIG
###############################################

CODEBASE = 'vg'

# Voice you want to use
# VOICE='rab_diphone'
# This is the nitech-made ARCTIC voice, tut on how to install:
# http://ubuntuforums.org/showthread.php?t=751169 ("Installing the enhanced Nitech HTS voices" section)
# VOICE='nitech_us_bdl_arctic_hts'
# VOICE='nitech_us_jmk_arctic_hts'
# VOICE='nitech_us_awb_arctic_hts'
VOICE = 'nitech_us_slt_arctic_hts'  # less bored US female
# VOICE='nitech_us_clb_arctic_hts' # DEFAULT, bored US female (occasionally comes up with british pronunciations?!)
# VOICE='nitech_us_rms_arctic_hts'

# PHONESET='mrpa'
PHONESET = ''

MALE = False
# What we do with SoX:
if MALE:
    VOICE = 'nitech_us_slt_arctic_hts'  # less bored US female
    # VOICE='cmu_us_slt_arctic_hts'
    SOX_ARGS = 'pitch -500'
    SOX_ARGS += ' stretch 1.2'  # Starts the gravelly sound, lowers pitch a bit.
    SOX_ARGS += ' synth sine amod 60'
    SOX_ARGS += ' chorus 0.7 0.9 55 0.4 0.25 2 -t'
    SOX_ARGS += ' phaser 0.9 0.85 4 0.23 1.3 -s'
else:
    VOICE = 'nitech_us_clb_arctic_hts'  # DEFAULT, bored US female (occasionally comes up with british pronunciations?!)
    SOX_ARGS = 'stretch 1.1'
    SOX_ARGS += ' chorus 0.7 0.9 55 0.4 0.25 2 -t'
    SOX_ARGS += ' phaser 0.9 0.85 4 0.23 1.3 -s'
SOX_ARGS += ' bass -40'
SOX_ARGS += ' highpass 22 highpass 22'
SOX_ARGS += ' compand 0.01,1 -90,-90,-70,-70,-60,-20,0,0 -5 -20'  # Dynamic range compression.
# SOX_ARGS += ' echos 0.8 0.5 100 0.25 10 0.25' # Good with stretch, otherwise sounds like bees.
SOX_ARGS += ' echos 0.3 0.5 100 0.25 10 0.25'  # Good with stretch, otherwise sounds like bees.
#SOX_ARGS += ' delay 0.5'
SOX_ARGS += ' norm'

# Direct from TG's PR (https://github.com/tgstation/tgstation/pull/36492)
# May bump up quality and rate slightly...
RECOMPRESS_ARGS = [
    # Audio Codec
    '-c:a',     'libvorbis',
    # Force to mono (should already be, since festival outputs mono...)
    '-ac',      '1',
    # Sampling rate in Hz. TG uses 16kHz.
    '-ar',      '16000',
    # Audio quality [0,9]. TG uses 0.
    '-q:a',     '0',
    # Playback speed
    '-speed',   '0',
    # Number of threads to use.  This works OK on my laptop, but you may need fewer
    #'-threads', '8',
    # Now specified in -j.
    # Force overwrite
    '-y']

# Have to do the trimming seperately.
PRE_SOX_ARGS = 'trim 0 -0.1'  # Trim off last 0.2s.

# Shit we shouldn't change or overwrite. (Boops, pauses, etc)
OLD_SFX = {
    '.': 1,
    ',': 1,
    'bloop': 1,
    'bizwarn': 1,  # Is this a misspelling of the below?
    'buzwarn': 1,
    'doop': 1,
    'dadeda': 1,
    'woop': 1,
}

################################################
# ROB'S AWFUL CODE BELOW (cleanup planned)
################################################


OTHERSOUNDS = []
KNOWN_PHONEMES = {}
PHRASELENGTHS = dict(OLD_SFX.items())
ALL_WORDS={}


def md5sum(filename):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()

def GenerateForWord(phrase: Phrase, args: Optional[argparse.Namespace] = None):
    global PHRASELENGTHS, OLD_SFX, SOX_ARGS, KNOWN_PHONEMES, OTHERSOUNDS
    my_phonemes = {}
    if phrase.hasFlag(EPhraseFlags.OLD_VOX):
        log.info('Skipping %s.ogg (Marked as OLD_VOX)', phrase.id)
        return
    if phrase.hasFlag(EPhraseFlags.NOT_VOX):
        OTHERSOUNDS += [phrase.id]

    if phrase.parsed_phrase is not None:
        for _word in phrase.parsed_phrase:
            _word = _word.lower()
            if _word in KNOWN_PHONEMES:
                my_phonemes[_word] = KNOWN_PHONEMES[_word].toLisp().replace('\n', '')

    md5 = phrase.phrase
    md5 += '\n'.join(my_phonemes.values())
    md5 += SOX_ARGS + PRE_SOX_ARGS + ''.join(RECOMPRESS_ARGS)
    md5 += VOICE + PHONESET
    md5 += phrase.filename

    #phrase.filename = os.path.join('sound', 'vox_fem', phrase.id + '.ogg')
    #if '/' in phrase.id:
    #    phrase.filename = os.path.join(phrase.id + '.ogg')
    oggfile = os.path.abspath(os.path.join('dist', phrase.filename))
    cachefile = os.path.abspath(os.path.join('cache', phrase.id.replace(os.sep, '_').replace('.', '') + '.dat'))

    parent = os.path.dirname(oggfile)
    if not os.path.isdir(parent):
        os.makedirs(parent)

    parent = os.path.dirname(cachefile)
    if not os.path.isdir(parent):
        os.makedirs(parent)

    if os.path.isfile(oggfile):
        old_md5 = ''
        if os.path.isfile(cachefile):
            with open(cachefile, 'r') as md5f:
                old_md5 = md5f.read()
        if old_md5 == md5:
            log.info('Skipping {0}.ogg (exists)'.format(phrase.id))
            return
    log.info('Generating {0}.ogg ({1})'.format(phrase.id, repr(phrase.phrase)))
    text2wave = None
    if phrase.hasFlag(EPhraseFlags.SFX):
        text2wave = 'ffmpeg -i '+phrase.phrase+' tmp/VOX-word.wav'
    else:
        with open('tmp/VOX-word.txt', 'w') as wf:
            wf.write(phrase.phrase)

        text2wave = 'text2wave tmp/VOX-word.txt -o tmp/VOX-word.wav'
        if os.path.isfile('tmp/VOXdict.lisp'):
            text2wave = 'text2wave -eval tmp/VOXdict.lisp tmp/VOX-word.txt -o tmp/VOX-word.wav'
    with open(cachefile, 'w') as wf:
        wf.write(md5)
    for fn in ('tmp/VOX-word.wav', 'tmp/VOX-soxpre-word.wav', 'tmp/VOX-sox-word.wav'):
        if os.path.isfile(fn):
            os.remove(fn)

    cmds = []
    cmds += [(text2wave.split(' '), 'tmp/VOX-word.wav')]
    cmds += [(['sox', 'tmp/VOX-word.wav', 'tmp/VOX-soxpre-word.wav'] + PRE_SOX_ARGS.split(' '), 'tmp/VOX-soxpre-word.wav')]
    cmds += [(['sox', 'tmp/VOX-soxpre-word.wav', 'tmp/VOX-sox-word.wav'] + SOX_ARGS.split(' '), 'tmp/VOX-sox-word.wav')]
    cmds += [(['oggenc', 'tmp/VOX-sox-word.wav', '-o', 'tmp/VOX-encoded.ogg'], 'tmp/VOX-encoded.ogg')]
    cmds += [(['ffmpeg', '-i', 'tmp/VOX-encoded.ogg']+RECOMPRESS_ARGS+['-threads',args.threads]+[oggfile], oggfile)]
    for command_spec in cmds:
        (command, cfn) = command_spec
        with os_utils.TimeExecution(command[0]):
            os_utils.cmd(command, echo=False, critical=True, show_output=False)
    for command_spec in cmds:
        (command, cfn) = command_spec
        if not os.path.isfile(fn):
            log.error("File '{0}' doesn't exist, command '{1}' probably failed!".format(cfn, command))
            sys.exit(1)

def main():
    argp = argparse.ArgumentParser(description='Generation script for ss13-vox.')
    argp.add_argument('--codebase', choices=['vg', 'tg'], default='vg', help='Which codebase to generate for. (Affects output code and paths.)')
    argp.add_argument('--threads', '-j', type=int, default=multiprocessing.cpu_count(), help='How many threads to use in ffmpeg.')
    argp.add_argument('phrasefiles', nargs='+', type=str, help='A list of phrase files.')
    args = argp.parse_args()

    if not os.path.isdir('tmp'):
        os.makedirs('tmp')

    DIST_DIR = 'dist'
    CODE_DIR = ''
    PREEX_SOUND = 'sound/vox/{ID}.wav'
    NUVOX_SOUND = 'sound/vox_fem/{ID}.ogg'
    vox_sounds_path = ''
    templatefile = ''

    pathcfg = BaseConfig()
    pathcfg.cfg = YAMLConfig('paths.yml').cfg[args.codebase]
    PREEX_SOUND = pathcfg.get('sound.old-vox', PREEX_SOUND)
    NUVOX_SOUND = pathcfg.get('sound.new-vox', PREEX_SOUND)
    vox_sounds_path = os.path.join(DIST_DIR, pathcfg.get('vox_sounds.path'))
    templatefile = pathcfg.get('vox_sounds.template')
    vox_data_path = os.path.join(DIST_DIR, pathcfg.get('vox_data'))

    DATA_DIR = os.path.join(DIST_DIR, 'data')
    os_utils.ensureDirExists(DATA_DIR)
    with log.info('Parsing lexicon...'):
        lexicon = ParseLexiconText('lexicon.txt')
        DumpLexiconScript(VOICE, lexicon.values(), 'tmp/VOXdict.lisp')

    phrases=[]
    phrasesByID = {}
    broked = False
    for filename in args.phrasefiles:
        for p in ParsePhraseListFrom(filename):
            if p.id in phrasesByID:
                duplicated = phrasesByID[p.id]
                log.critical('Duplicate phrase with ID %s in file %s on line %d! First instance in file %s on line %d.', p.id, p.deffile, p.defline, duplicated.deffile, duplicated.defline)
                broked = True
                continue
            phrases += [p]
            phrasesByID[p.id] = p
        if broked:
            sys.exit(1)

    soundsToKeep = set()
    for sound in OTHERSOUNDS:
        soundsToKeep.add(os.path.join(DIST_DIR, sound + '.ogg'))

    phrases.sort(key=lambda x: x.id)

    for phrase in phrases:
        # If it has a path, it's being manually specified.
        if '/' in phrase.id:
            phrase.filename = phrase.id + '.ogg'
        else:
            phrase.filename = NUVOX_SOUND.format(ID=phrase.id)
            if phrase.id in OLD_SFX:
                phrase.flags |= EPhraseFlags.OLD_VOX
                phrase.filename = PREEX_SOUND.format(ID=phrase.id)

        if not phrase.hasFlag(EPhraseFlags.OLD_VOX):
            GenerateForWord(phrase, args)

        soundsToKeep.add(os.path.join(DIST_DIR, phrase.filename))

    jenv = jinja2.Environment(loader=jinja2.FileSystemLoader(['./templates']))
    templ = jenv.get_template(templatefile)
    with log.info('Writing sound list to %s...', vox_sounds_path):
        os_utils.ensureDirExists(os.path.dirname(vox_sounds_path))
        with open(vox_sounds_path, 'w') as f:
            f.write(templ.render(WORDS=[p for p in phrases if not p.hasFlag(EPhraseFlags.NOT_VOX)]))
    soundsToKeep.add(vox_sounds_path)

    os_utils.ensureDirExists(DATA_DIR)
    with open(os.path.join(DATA_DIR, 'vox_data.json'), 'w') as f:
        data = {
            'version': 1,
            'compiled': time.time(),
            'voice': VOICE,
            'phoneset': PHONESET,
            #'phonemes': KNOWN_PHONEMES,
            'words': collections.OrderedDict({w.id: w.serialize() for w in phrases if '/' not in w.id}),
        }
        json.dump(data, f, indent=2)
    soundsToKeep.add(os.path.join(DATA_DIR, 'vox_data.json'))

    for root, dirs, files in os.walk(DIST_DIR, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            if filename not in soundsToKeep:
                log.warning('Removing {0} (no longer defined)'.format(filename))
                os.remove(filename)

if __name__ == '__main__':
    main()
