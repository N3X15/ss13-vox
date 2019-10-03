from typing import List, Dict, Tuple
from buildtools import log
import re,sys
REGEX_SEARCH_STRINGS = re.compile(r'(\'|")(.*?)(?:\1)')

class Pronunciation(object):
    '''
    Festival can fuck up pronunciation of stuff, but thankfully, we can specify a new set.

    Unfortunately, it's in LISP, which this class will generate for you.
    '''

    #: Convert convert our CMU standard phonemes to whatever the voice we're using needs.
    PHONE_CONVERSIONS: Dict[str, Dict[str, str]] = {
        'mrpa': {
            'ae': 'a',
            'ih': 'i',
        }
    }

    #: DMU phonemes + pau
    VALID_PHONEMES: List[str] = [
        'aa',
        'ae',
        'ah',
        'ao',
        'aw',
        'ay',
        'b',
        'ch',
        'd',
        'dh',
        'eh',
        'er',
        'ey',
        'f',
        'g',
        'hh',
        'ih',
        'iy',
        'jh',
        'k',
        'l',
        'm',
        'n',
        'ng',
        'ow',
        'oy',
        'p',
        'r',
        's',
        'sh',
        't',
        'th',
        'uh',
        'uw',
        'v',
        'w',
        'y',
        'z',
        'zh',
        'pau']

    def __init__(self, phoneset: str = ''):
        self.phoneset: str = phoneset
        self.name: str = ''
        self.type: str = 'n'
        #: (list of phonemes, stress), ...
        self.syllables: List[Tuple[List[str], int]] = []

    def toLisp(self):
        """
        ( "walkers" n ((( w oo ) 1) (( k @ z ) 0)) )
        ( "present" v ((( p r e ) 0) (( z @ n t ) 1)) )
        ( "monument" n ((( m o ) 1) (( n y u ) 0) (( m @ n t ) 0)) )
        """
        lispSyllables = []
        for syllable in self.syllables:
            lispSyllables.append('( ( {0} ) {1} )'.format(' '.join(syllable[0]), syllable[1]))
        return '(lex.add.entry\n\t\'( "{0}" {1} ( {2} ) ))\n'.format(self.name, self.type[0], ' '.join(lispSyllables))

    def parseWord(self, line):
        """
        walkers: noun "w oo" 'k @ z'
        present: verb 'p r e' "z @ n t"
        monument: noun "mo" 'n y u' 'm @ n t'
        """
        global REGEX_SEARCH_STRINGS
        lineChunks = line.split(' ')
        self.name = lineChunks[0].strip(':')
        self.type = lineChunks[1].strip()
        pronunciation = ' '.join(lineChunks[2:])
        for match in REGEX_SEARCH_STRINGS.finditer(pronunciation):
            stressLevel = 0
            if match.group(1) == '"':
                stressLevel = 1
            phonemes = []
            for phoneme in match.group(2).split(' '):
                if phoneme not in self.VALID_PHONEMES:
                    log.error('INVALID PHONEME "{0}" IN LEX ENTRY "{1}"'.format(phoneme, self.name))
                    sys.exit(1)
                if self.phoneset in self.PHONE_CONVERSIONS:
                    phoneset = self.PHONE_CONVERSIONS[self.phoneset]
                    if phoneme in phoneset:
                        phoneme = phoneset[phoneme]
                phonemes += [phoneme]
            self.syllables += [(phonemes, stressLevel)]
        log.info('Parsed {0} as {1}.'.format(pronunciation, repr(self.syllables)))

def DumpLexiconScript(voice: str, pronunciations: List[Pronunciation], filename: str) -> None:
    with open(filename, 'w') as lisp:
        if voice != '':
            lisp.write(f'(voice_{voice})\n')
        for p in sorted(pronunciations, key=lambda x: x.name):
            lisp.write(p.toLisp())

def ParseLexiconText(filename: str, phoneset: str = '') -> Dict[str, Pronunciation]:
    pronunciations = {}
    with open(filename, 'r') as lines:
        for line in lines:
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                p = Pronunciation(phoneset)
                p.parseWord(line)
                pronunciations[p.name] = p
    return pronunciations
