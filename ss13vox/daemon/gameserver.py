import collections, random, string
from pathlib import Path
from typing import Dict, List, Optional

from ss13vox.daemon.phraseref import PhraseRef

class VOXGameServer:
    def __init__(self) -> None:
        self.id: str = ''
        self.secret_key: str = ''
        self.session_key: str = ''
        self.basepath: Path = None
        self.phrases: Dict[str, PhraseRef] = {}
        self.phrase_pool: collections.deque[str] = collections.deque()

    def loadFrom(self, config: dict) -> None:
        self.deserialize(config['gameservers'][self.id])

    def deserialize(self, data: dict) -> None:
        self.secret_key = data['secret']

    def generateSecretKey(self) -> None:
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        self.secret_key = ''.join(random.choice(chars) for x in range(64))
        
    def generateSessionKey(self) -> None:
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        self.session_key = ''.join(random.choice(chars) for x in range(64))

    def serialize(self) -> dict:
        return {
            'secret': self.secret_key
        }

    def addPhrase(self, phrase: PhraseRef) -> None:
        if (len(self.phrase_pool) + 1) > 50:
            oldpid = self.phrase_pool.popleft()
            self.phrases[oldpid].remove()
            del self.phrases[oldpid]
        self.phrases[phrase.phrase]=phrase
        self.phrase_pool.append(phrase.phrase)

    def getPhrase(self, phrase: str) -> Optional[PhraseRef]:
        if phrase in self.phrases:
            return self.phrases[phrase]
        return None
