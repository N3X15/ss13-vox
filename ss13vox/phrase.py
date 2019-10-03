from typing import List, Optional
from enum import IntFlag

__ALL__ = ['EPhraseFlags', 'Phrase', 'ParsePhraseListFrom']

class EPhraseFlags(IntFlag):
    NONE     = 0
    OLD_VOX  = 1 # AKA preexisting
    SFX      = 2
    NOT_VOX  = 4 # Not used in VOX announcements (meaning stuff that doesn't go in sound/vox_fem/)

class Phrase(object):
    def __init__(self):
        self.id: str = ''
        self.wordlen: int = 0
        self.phrase: str = ''
        self.parsed_phrase: Optional[List[str]] = None
        self.filename: str = ''
        self.comments_before: List[str] = []
        self.flags: EPhraseFlags = EPhraseFlags.NONE

        self.deffile: str = ''
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

    def hasFlag(self, flag: EPhraseFlags) -> bool:
        return (self.flags & flag) == flag

    def serialize(self) -> dict:
        o = {
            'wordlen':  self.wordlen,
            'filename': self.filename,
            'flags': [x.name.lower().replace('_', '-') for x in list(EPhraseFlags) if x.value > 0 and (self.flags & x) == x]
        }
        if self.flags & EPhraseFlags.SFX:
            o['input-filename'] = self.phrase
        else:
            o['phrase'] = self.parsed_phrase

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
