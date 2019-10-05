from typing import List, Optional, Dict
from enum import IntFlag

__ALL__ = ['EPhraseFlags', 'Phrase', 'ParsePhraseListFrom']

class EPhraseFlags(IntFlag):
    NONE     = 0
    OLD_VOX  = 1 # AKA preexisting
    SFX      = 2
    NOT_VOX  = 4 # Not used in VOX announcements (meaning stuff that doesn't go in sound/vox_fem/)

class Phrase(object):
    def __init__(self):
        #: Unique ID of the phrase. _honk, ass, voxtest, etc.
        self.id: str = ''
        #: Word count. Not entirely accurate since some phrases use multiple words to work around festival fuckups.
        self.wordlen: int = 0
        #: Textual representation of the phrase, as fed to festival. SFX phrases use this as the filename.
        self.phrase: str = ''
        #: Parsed representation of the phrase.  None in SFX.
        self.parsed_phrase: Optional[List[str]] = None
        #: Output filename.
        self.filename: str = ''
        #: Any comments before this line.
        self.comments_before: List[str] = []
        self.flags: EPhraseFlags = EPhraseFlags.NONE
        # What voices we were built with
        self.voices: List[str] = []
        #: Output filename.
        self.files: Dict[str, str] = {}

        #: File in which this phrase was defined.
        self.deffile: str = ''
        #: Line in which this phrase was defined.
        self.defline: int = 0

    def parsePhrase(self, phrase: str) -> None:
        self.phrase = phrase
        # sound/ai/announcement_16.ogg = ...
        if '/' in self.id:
            self.flags |= EPhraseFlags.NOT_VOX

        # _honk = @samples/bikehorn.wav
        if self.phrase.startswith('@'):
            self.parsed_phrase = None
            self.flags |= EPhraseFlags.SFX
            self.phrase = self.phrase[1:]

        self.parsed_phrase = self.phrase.split(' ')
        self.wordlen = len(self.parsed_phrase)

    def hasFlag(self, flag: EPhraseFlags) -> bool:
        '''
        Convenient shortcut.
        '''
        return (self.flags & flag) == flag

    def serialize(self) -> dict:
        o = {
            'wordlen':  self.wordlen,
            'files': self.files,
            'flags': [x.name.lower().replace('_', '-') for x in list(EPhraseFlags) if x.value > 0 and (self.flags & x) == x]
        }
        if self.flags & EPhraseFlags.SFX:
            o['input-filename'] = self.phrase
        else:
            o['phrase'] = self.parsed_phrase
        return o

def ParsePhraseListFrom(filename: str) -> List[Phrase]:
    phrases = []
    comments_before = []
    with open(filename, 'r') as f:
        ln = 0
        for line in f:
            ln += 1
            if line.startswith("#"):
                comments_before += [line[1:]]
                continue
            if line.strip() == '':
                comments_before = []
                continue
            if '=' in line:
                (wordfile, phrase) = line.split('=', maxsplit=1)
                p = Phrase()
                p.deffile = filename
                p.defline = ln
                p.id = wordfile.strip()
                p.parsePhrase(phrase.strip())
                p.comments_before = comments_before
                comments_before = []
                phrases += [p]
            elif line != '' and ' ' not in line and len(line) > 0:
                p = Phrase()
                p.deffile = filename
                p.defline = ln
                p.id = line.strip()
                p.parsePhrase(p.id)
                p.comments_before = comments_before
                comments_before = []
                phrases += [p]
    return phrases
