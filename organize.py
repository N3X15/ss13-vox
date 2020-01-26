import collections
from typing import List, Dict
from buildtools import log
from ss13vox.phrase import Phrase, EPhraseFlags, ParsePhraseListFrom
from ss13vox.pronunciation import Pronunciation, DumpLexiconScript, ParseLexiconText

def organizeFile(filename: str, sort_sections: bool = False) -> None:
    phrases: Dict[str, List[Phrase]] = collections.OrderedDict({
        #EPhraseFlags.OLD_VOX.name: [],
        #EPhraseFlags.NOT_VOX: [],
        #EPhraseFlags.SFX.name:     [],
    })
    phrasesByID = {}
    for p in ParsePhraseListFrom(filename):
        if p.id.lower() in phrasesByID:
            log.warning('Skipping duplicate %s...', p.id)
            continue
        assignTo = ''
        if p.hasFlag(EPhraseFlags.SFX):
            assignTo = EPhraseFlags.SFX.name
        elif p.hasFlag(EPhraseFlags.OLD_VOX):
            assignTo = EPhraseFlags.OLD_VOX.name
        else:
            assignTo = p.category
        phrasesByID[p.id.lower()] = p
        if assignTo not in phrases:
            phrases[assignTo] = []
        phrases[assignTo] += [p]

    if sort_sections:
        newPhOD = collections.OrderedDict()
        for k in sorted(phrases.keys()):
            newPhOD[k]=phrases[k]
        phrases=newPhOD
    with open(filename+'.sorted', 'w') as w:
        divider_len = max([len(x) for x in phrases.keys()])+4
        divider = '#'*divider_len
        for section, sectionPhrases in phrases.items():
            if section != '':
                w.write(f'\n{divider}\n## {section}\n{divider}\n\n')
            for phrase in sorted(sectionPhrases, key=lambda x: x.id):
                for comm in phrase.comments_before:
                    comm = comm.rstrip()
                    w.write(f'#{comm}\n')
                key = phrase.id
                value = phrase.phrase
                if phrase.hasFlag(EPhraseFlags.SFX):
                    w.write(f'{key.lower()} = @{value}\n')
                else:
                    if key != value:
                        w.write(f'{key.lower()} = {value}\n')
                    else:
                        w.write(f'{key.lower()}\n')

organizeFile('wordlists/common.txt')
organizeFile('wordlists/vg/chemistry.txt')
organizeFile('wordlists/vg/mining.txt')
organizeFile('wordlists/vg/misc.txt')
organizeFile('wordlists/vg/antags.txt', sort_sections=True)
