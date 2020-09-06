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

from typing import Optional, Dict, List
from enum import IntFlag

script_dir = os.path.dirname(os.path.realpath(__file__))

from buildtools import os_utils, log, utils
from buildtools.config import YAMLConfig, BaseConfig

from ss13vox.proc import InitClass
from ss13vox.phrase import Phrase, EPhraseFlags, ParsePhraseListFrom, FileData
from ss13vox.pronunciation import Pronunciation, DumpLexiconScript, ParseLexiconText
from ss13vox.voice import EVoiceSex, Voice, VoiceRegistry, USSLTFemale, SFXVoice

"""
Usage:
    $ python create.py voxwords.txt

Requires festival, sox, and vorbis-tools.

create.py - Uses festival to generate word oggs.

Copyright 2013-2020 Rob "N3X15" Nelson <nexis@7chan.org>

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
    # Now specified in -j.
    #'-threads', '8',
    # Force overwrite
    '-y']

# Have to do the trimming seperately.
PRE_SOX_ARGS = 'trim 0 -0.1'  # Trim off last 0.2s.


################################################
# ROB'S AWFUL CODE BELOW (cleanup planned)
################################################


OTHERSOUNDS = []
KNOWN_PHONEMES = {}
PHRASELENGTHS = {}
ALL_WORDS={}


def md5sum(filename):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()

def GenerateForWord(phrase: Phrase, voice: Voice, writtenfiles: set, args: Optional[argparse.Namespace] = None):
    global PHRASELENGTHS, OLD_SFX, KNOWN_PHONEMES, OTHERSOUNDS
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


    #filename = phrase.filename.format(ID=phrase.id, SEX=voice.assigned_sex)
    filename = phrase.getFinalFilename(voice.assigned_sex)
    sox_args = voice.genSoxArgs(args)

    md5 = json.dumps(phrase.serialize())
    md5 += '\n'.join(my_phonemes.values())
    md5 += ''.join(sox_args) + PRE_SOX_ARGS + ''.join(RECOMPRESS_ARGS)
    md5 += voice.fast_serialize()
    md5 += filename

    #filename = os.path.join('sound', 'vox_fem', phrase.id + '.ogg')
    #if '/' in phrase.id:
    #    filename = os.path.join(phrase.id + '.ogg')
    oggfile = os.path.abspath(os.path.join('dist', filename))
    cachebase = os.path.abspath(os.path.join('cache', phrase.id.replace(os.sep, '_').replace('.', '')))
    checkfile = cachebase + voice.ID + '.dat'
    cachefile = cachebase + voice.ID + '.json'

    fdata = FileData()
    fdata.voice = voice.ID
    fdata.filename = os.path.relpath(oggfile, 'dist')

    def commitWritten():
        nonlocal phrase, voice, oggfile, writtenfiles, fdata
        if voice.ID == SFXVoice.ID:
            # Both masculine and feminine voicepacks link to SFX.
            for sex in ['fem', 'mas']:
                phrase.files[sex] = fdata
        else:
            phrase.files[voice.assigned_sex] = fdata
        writtenfiles.add(os.path.abspath(oggfile))

    parent = os.path.dirname(oggfile)
    if not os.path.isdir(parent):
        os.makedirs(parent)

    parent = os.path.dirname(cachefile)
    if not os.path.isdir(parent):
        os.makedirs(parent)

    if os.path.isfile(oggfile) and os.path.isfile(cachefile):
        old_md5 = ''
        if os.path.isfile(checkfile):
            with open(checkfile, 'r') as md5f:
                old_md5 = md5f.read()
        if old_md5 == md5:
            cachedata = {}
            with open(cachefile, 'r') as cachef:
                cachedata = json.load(cachef)
            fdata.deserialize(cachedata)

            log.info('Skipping {0} for {1} (exists)'.format(filename, voice.ID))
            commitWritten()
            return
    log.info('Generating {0} for {1} ({2!r})'.format(filename, voice.ID, phrase.phrase))
    text2wave = None
    if phrase.hasFlag(EPhraseFlags.SFX):
        text2wave = ['ffmpeg', '-i', phrase.phrase, 'tmp/VOX-word.wav']
    else:
        phrasefile = os.path.join('tmp','VOX-word.txt')

        text2wave = ['text2wave']
        if os.path.isfile('tmp/VOXdict.lisp'):
            text2wave += ['-eval','tmp/VOXdict.lisp']
        if phrase.hasFlag(EPhraseFlags.SING):
            text2wave += ['-mode', 'singing', phrase.phrase]
        else:
            with open(phrasefile, 'w') as wf:
                wf.write(phrase.phrase)
            text2wave += [phrasefile]
        text2wave += ['tmp/VOX-word.txt', '-o', 'tmp/VOX-word.wav']
    with open(checkfile, 'w') as wf:
        wf.write(md5)
    for fn in ('tmp/VOX-word.wav', 'tmp/VOX-soxpre-word.wav', 'tmp/VOX-sox-word.wav', 'tmp/VOX-encoded.ogg'):
        if os.path.isfile(fn):
            os.remove(fn)

    cmds = []
    cmds += [(text2wave, 'tmp/VOX-word.wav')]
    if not phrase.hasFlag(EPhraseFlags.NO_PROCESS) or not phrase.hasFlag(EPhraseFlags.NO_TRIM):
        cmds += [(['sox', 'tmp/VOX-word.wav', 'tmp/VOX-soxpre-word.wav'] + PRE_SOX_ARGS.split(' '), 'tmp/VOX-soxpre-word.wav')]
    if not phrase.hasFlag(EPhraseFlags.NO_PROCESS):
        cmds += [(['sox', cmds[-1][1], 'tmp/VOX-sox-word.wav'] + sox_args, 'tmp/VOX-sox-word.wav')]
    cmds += [(['oggenc', cmds[-1][1], '-o', 'tmp/VOX-encoded.ogg'], 'tmp/VOX-encoded.ogg')]
    cmds += [(['ffmpeg', '-i', 'tmp/VOX-encoded.ogg']+RECOMPRESS_ARGS+['-threads',args.threads]+[oggfile], oggfile)]
    for command_spec in cmds:
        (command, cfn) = command_spec
        with os_utils.TimeExecution(command[0]):
            os_utils.cmd(command, echo=args.echo, critical=True, show_output=command[0] in ('text2wave',))

    command = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', oggfile]
    with os_utils.TimeExecution(command[0]):
        captured = os_utils.cmd_out(command, echo=False, critical=True)
        fdata.fromJSON(json.loads(captured))
        fdata.checksum = md5sum(oggfile)
        if (not phrase.hasFlag(EPhraseFlags.SFX)) and fdata.duration > 10.0:
            fdata.duration -= 10.0

    for command_spec in cmds:
        (command, cfn) = command_spec
        if not os.path.isfile(fn):
            log.error("File '{0}' doesn't exist, command '{1}' probably failed!".format(cfn, command))
            sys.exit(1)

    with open(cachefile, 'w') as f:
        json.dump(fdata.serialize(), f)

    commitWritten()

def main():
    argp = argparse.ArgumentParser(description='Generation script for ss13-vox.')
    argp.add_argument('--threads', '-j', type=int, default=multiprocessing.cpu_count(), help='How many threads to use in ffmpeg.')
    argp.add_argument('--echo', '-e', action='store_true', default=False, help='Echo external commands to console.')
    args = argp.parse_args()

    if not os.path.isdir('tmp'):
        os.makedirs('tmp')

    DIST_DIR = 'dist'
    PREEX_SOUND = 'sound/vox/{ID}.wav'
    NUVOX_SOUND = 'sound/vox_{SEX}/{ID}.wav'
    voices = []
    vox_sounds_path = ''
    templatefile = ''

    config = BaseConfig()
    config.cfg = YAMLConfig('config.yml')
    pathcfg = BaseConfig()
    pathcfg.cfg = YAMLConfig('paths.yml').cfg[config.get('codebase', 'vg')]

    PREEX_SOUND = pathcfg.get('sound.old-vox', PREEX_SOUND)
    NUVOX_SOUND = pathcfg.get('sound.new-vox', NUVOX_SOUND)

    voice_assignments = {}
    all_voices = []
    default_voice: Voice = VoiceRegistry.Get(USSLTFemale.ID)
    sfx_voice: SFXVoice = SFXVoice()
    configured_voices: Dict[str, dict] = {}
    for sexID, voiceid in config.get('voices', {'fem': USSLTFemale.ID}).items():
        voice = VoiceRegistry.Get(voiceid)
        assert sexID != ''
        voice.assigned_sex = sexID
        if sexID in ('fem', 'mas'):
            sex = EVoiceSex(sexID)
            assert voice.SEX == sex
            voices += [voice]
        elif sexID == 'default':
            default_voice = voice
        voice_assignments[voice.assigned_sex] = []
        all_voices += [voice]
        configured_voices[sexID] = voice.serialize()

    voice_assignments[sfx_voice.assigned_sex] = []
    all_voices += [sfx_voice]
    configured_voices[sfx_voice.assigned_sex] = sfx_voice.serialize()

    vox_sounds_path = os.path.join(DIST_DIR, pathcfg.get('vox_sounds.path'))
    templatefile = pathcfg.get('vox_sounds.template')
    vox_data_path = os.path.join(DIST_DIR, pathcfg.get('vox_data'))

    DATA_DIR = os.path.join(DIST_DIR, 'data')
    os_utils.ensureDirExists(DATA_DIR)
    with log.info('Parsing lexicon...'):
        lexicon = ParseLexiconText('lexicon.txt')

    phrases=[]
    phrasesByID = {}
    broked = False
    for filename in config.get('phrasefiles', ['announcements.txt', 'voxwords.txt']):
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

    overrides = config.get('overrides', {})
    for phrase in phrases:
        if phrase.id in overrides:
            phrase.fromOverrides(overrides.get(phrase.id))
        phrase_voices = list(voices)
        # If it has a path, it's being manually specified.
        if '/' in phrase.id:
            phrase.filename = phrase.id + '.ogg'
            phrase_voices = [default_voice]
            soundsToKeep.add(os.path.abspath(os.path.join(DIST_DIR, phrase.filename)))
        else:
            phrase.filename = ''+NUVOX_SOUND
            if phrase.hasFlag(EPhraseFlags.OLD_VOX):
                phrase_voices = [default_voice]
                phrase.filename = PREEX_SOUND.format(ID=phrase.id)
                for voice in ['fem', 'mas']:
                    phrase.files[voice] = FileData()
                    phrase.files[voice].filename = phrase.filename
                    phrase.files[voice].checksum = ''
                    phrase.files[voice].duration = phrase.override_duration or -1
                    phrase.files[voice].size     = phrase.override_size or -1
                    #voice_assignments[voice].append(phrase)
                soundsToKeep.add(os.path.abspath(os.path.join(DIST_DIR, phrase.filename)))
                continue

        if phrase.hasFlag(EPhraseFlags.SFX):
            phrase_voices = [sfx_voice]

        if not phrase.hasFlag(EPhraseFlags.OLD_VOX):
            log.info('%s - %r', phrase.id, [x.assigned_sex for x in phrase_voices])
            for v in phrase_voices:
                voice_assignments[v.assigned_sex].append(phrase)
                #phrase.files[v.assigned_sex] = fd
    #sys.exit(1)
    for voice in all_voices:
        print(voice.ID, voice.assigned_sex)
        DumpLexiconScript(voice.FESTIVAL_VOICE_ID, lexicon.values(), 'tmp/VOXdict.lisp')
        for phrase in voice_assignments[voice.assigned_sex]:
            GenerateForWord(phrase, voice, soundsToKeep, args)
            sexes=set()
            for vk, fd in phrase.files.items():
                soundsToKeep.add(os.path.abspath(os.path.join(DIST_DIR, fd.filename)))

    jenv = jinja2.Environment(loader=jinja2.FileSystemLoader(['./templates']))
    jenv.add_extension('jinja2.ext.do') # {% do ... %}
    templ = jenv.get_template(templatefile)
    with log.info('Writing sound list to %s...', vox_sounds_path):
        os_utils.ensureDirExists(os.path.dirname(vox_sounds_path))
        assetcache={}
        sound2id={}
        with open(vox_sounds_path, 'w') as f:
            sexes = {
                'fem': [],
                'mas': [],
                'default': [],
                #'sfx': [],
            }
            for p in phrases:
                for k in p.files.keys():
                    assetcache[p.getAssetKey(k)] = p.files[k].filename
                    sound2id[p.files[k].filename] = p.getAssetKey(k)
                if p.hasFlag(EPhraseFlags.NOT_VOX):
                    continue
                for k in p.files.keys():
                    if p.hasFlag(EPhraseFlags.SFX):
                        for sid in ('fem', 'mas'):
                            if p not in sexes[sid]:
                                sexes[sid].append(p)
                    else:
                        sexes[k].append(p)
            f.write(templ.render(
                InitClass=InitClass,
                SEXES=sexes,
                ASSETCACHE=assetcache,
                SOUND2ID=sound2id,
                PHRASES=[p for p in phrases if not p.hasFlag(EPhraseFlags.NOT_VOX)]))
    soundsToKeep.add(os.path.abspath(vox_sounds_path))

    os_utils.ensureDirExists(DATA_DIR)
    with open(os.path.join(DATA_DIR, 'vox_data.json'), 'w') as f:
        data = {
            'version': 2,
            'compiled': time.time(),
            'voices': configured_voices,
            'words': collections.OrderedDict({w.id: w.serialize() for w in phrases if '/' not in w.id}),
        }
        json.dump(data, f, indent=2)
    soundsToKeep.add(os.path.abspath(os.path.join(DATA_DIR, 'vox_data.json')))

    with open('tmp/written.txt', 'w') as f:
        for filename in sorted(soundsToKeep):
            f.write(f'{filename}\n')

    for root, _, files in os.walk(DIST_DIR, topdown=False):
        for name in files:
            filename = os.path.abspath(os.path.join(root, name))
            if filename not in soundsToKeep:
                log.warning('Removing {0} (no longer defined)'.format(filename))
                os.remove(filename)

if __name__ == '__main__':
    main()
