import collections, random, string, uuid
from pathlib import Path
from typing import Dict, List, Optional

from ss13vox.daemon.phraseref import PhraseRef
from ss13vox.phrase import Phrase

class VOXGameServer:
    def __init__(self, gsid: str='') -> None:
        self.id: str = gsid
        self.secret_key: str = ''
        self.session_key: str = ''
        self.basepath: Path = None
        self.baseurl: str = None
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

    def addPhrase(self, voice: str, phrase: Phrase) -> PhraseRef:
        if (len(self.phrase_pool) + 1) > 50:
            oldpid = self.phrase_pool.popleft()
            self.phrases[oldpid].remove()
            del self.phrases[oldpid]
        pk: str = voice+phrase.phrase

        sid = str(uuid.uuid4())
        path = self.basepath / f'{sid}.ogg'
        url = f'{self.baseurl}/{sid}.ogg'
        pr = PhraseRef(sid, path, url)

        self.phrases[pk]=pr
        self.phrase_pool.append(pk)

        return pr

    def getPhrase(self, voice: str, phrase: str) -> Optional[PhraseRef]:
        pk: str = voice+phrase
        if pk in self.phrases:
            return self.phrases[pk]
        return None
