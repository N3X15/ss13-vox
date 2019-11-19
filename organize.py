import collections
from typing import List, Dict
from buildtools import log
from ss13vox.phrase import Phrase, EPhraseFlags, ParsePhraseListFrom
from ss13vox.pronunciation import Pronunciation, DumpLexiconScript, ParseLexiconText

def organizeFile(filename: str) -> None:
    phrases: Dict[str, List[Phrase]] = collections.OrderedDict({
        EPhraseFlags.OLD_VOX.name: [],
        #EPhraseFlags.NOT_VOX: [],
        EPhraseFlags.SFX.name:     [],
    })
    phrasesByID = {}
    for p in ParsePhraseListFrom(filename):
        if p.id in phrasesByID:
            log.warning('Skipping duplicate %s...', p.id)
            continue
        assignTo = ''
        if p.hasFlag(EPhraseFlags.SFX):
            assignTo = EPhraseFlags.SFX.name
        elif p.hasFlag(EPhraseFlags.OLD_VOX):
            assignTo = EPhraseFlags.OLD_VOX.name
        else:
            assignTo = p.category
        phrasesByID[p.id] = p
        if assignTo not in phrases:
            phrases[assignTo] = []
        phrases[assignTo] += [p]

    #phrases.sort(key=lambda x: x.id)
    with open(filename+'.sorted', 'w') as w:
        for section, sectionPhrases in phrases.items():
            if section != '':
                w.write(f'\n############\n## {section}\n############\n\n')
            for phrase in sorted(sectionPhrases, key=lambda x: x.id):
                for comm in phrase.comments_before:
                    comm = comm.rstrip()
                    w.write(f'#{comm}\n')
                key = phrase.id
                value = phrase.phrase
                if phrase.hasFlag(EPhraseFlags.SFX):
                    w.write(f'{key} = @{value}\n')
                else:
                    if key != value:
                        w.write(f'{key} = {value}\n')
                    else:
                        w.write(f'{key}\n')

organizeFile('wordlists/common.txt')
organizeFile('wordlists/vg/chemistry.txt')
organizeFile('wordlists/vg/misc.txt')
