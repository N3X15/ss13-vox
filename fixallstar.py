import hashlib
from pathlib import Path
from shlex import shlex
from ss13vox.voice import USRMSMale, USSLTFemale, Voice, VoiceRegistry
from ss13vox.runtime import VOXRuntime
from ss13vox.phrase import Phrase
from buildtools import log, os_utils

SOX = os_utils.assertWhich('sox')

phrases = []
i = 0
runtime: VOXRuntime = VOXRuntime()
runtime.loadConfig()
runtime.initialize()
voice = VoiceRegistry.Get(USSLTFemale.ID)
with open('wordlists/heynow.txt', 'r') as f:
    for line in f:
        phrase = line.strip()
        if len(phrase) > 0:
            pmd5 = hashlib.md5(phrase.encode()).hexdigest()
            filename = Path('tmp') / 'allstar' / f'{pmd5}.ogg'
            if not filename.parent.is_dir():
                filename.parent.mkdir(parents=True)
            if not filename.is_file():
                p = Phrase()
                p.phrase = phrase
                p.parsed_phrase = phrase.split(' ')
                p.wordlen = len(p.parsed_phrase)
                runtime.createSoundFromPhrase(p, voice, str(filename))
            phrases += [filename]

cmd = [SOX]+[str(x) for x in phrases]+['allstar.mp3']
os_utils.cmd(cmd, echo=True, show_output=True)
