from ss13vox.phrase import Phrase, EPhraseFlags, ParsePhraseListFrom
from ss13vox.pronunciation import Pronunciation, DumpLexiconScript, ParseLexiconText

def organizeFile(filename: str) -> None:
    phrases = ParsePhraseListFrom(filename)
    phrases.sort(key=lambda x: x.id)
    with open(filename+'.sorted', 'w') as w:
        for phrase in phrases:
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
