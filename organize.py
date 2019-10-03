import collections
from typing import List, Dict
from buildtools import log
from ss13vox.phrase import Phrase, EPhraseFlags, ParsePhraseListFrom
from ss13vox.pronunciation import Pronunciation, DumpLexiconScript, ParseLexiconText

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
def organizeFile(filename: str) -> None:
    phrases: Dict[EPhraseFlags, List[Phrase]] = collections.OrderedDict({
        EPhraseFlags.OLD_VOX: [],
        #EPhraseFlags.NOT_VOX: [],
        EPhraseFlags.SFX:     [],
        EPhraseFlags.NONE:    [],
    })
    phrasesByID = {}
    for p in ParsePhraseListFrom(filename):
        if p.id in phrasesByID:
            log.warning('Skipping duplicate %s...', p.id)
            continue
        assignTo = EPhraseFlags.NONE
        if p.hasFlag(EPhraseFlags.SFX):
            assignTo = EPhraseFlags.SFX
        elif p.id in OLD_SFX:
            assignTo = EPhraseFlags.OLD_VOX
        phrasesByID[p.id] = p
        phrases[assignTo] += [p]

    #phrases.sort(key=lambda x: x.id)
    with open(filename+'.sorted', 'w') as w:
        for section, sectionPhrases in phrases.items():
            w.write(f'\n############\n## {section.name}\n############\n\n')
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

organizeFile('voxwords.txt')
