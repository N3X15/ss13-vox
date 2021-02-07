from pathlib import Path
from typing import List, Dict, Optional

from ss13vox.daemon.gameserver import VOXGameServer

from ruamel.yaml import YAML
yaml = YAML(typ='rt')

class DaemonConfig:
    def __init__(self) -> None:
        self.address: str = '127.0.0.1'
        self.port: int = 8080
        self.baseurl: Optional[str] = None

        self.gameservers: Dict[str, VOXGameServer] = {}

        self.otf_dir: Path = Path('.otf')
        self.tmp_dir: Path = self.otf_dir / 'tmp'
        self.sounds_dir: Path = self.tmp_dir / 'sounds'

        self.limits: dict = {}

    @classmethod
    def load(cls, filename: str) -> 'DaemonConfig':
        cfg = cls()
        with Path(filename).open('r') as f:
            cfg.deserialize(yaml.load(f))
        return cfg

    def serialize(self) -> dict:
        return {
            'http': {
                'address': self.address,
                'port':    self.port,
                'baseurl': self.baseurl,
            },
            'gameservers': {k: v.serialize() for k, v in self.gameservers.items()},
            'storage': {
                'work': str(self.otf_dir),
                'tmp': str(self.tmp_dir),
                'sounds': str(self.sounds_dir),
            },
            'limits': self.limits
        }

    def saveTo(self, filename: str) -> None:
        with Path(filename).open('w') as f:
            yaml.indent()
            yaml.dump(self.serialize(), f)

    def deserialize(self, data: dict) -> None:
        self.address = data['http']['address']
        self.port = int(data['http']['port'])
        self.baseurl = data['http'].get('baseurl', f'http://{self.address}:{self.port}/announcement/listen')

        self.gameservers = {}
        for k,v in data['gameservers'].items():
            self.gameservers[k] = gs =  VOXGameServer()
            gs.id = k
            gs.deserialize(v)

        self.otf_dir = Path(data['storage']['work'])
        self.tmp_dir = Path(data['storage']['tmp'])
        self.sounds_dir = Path(data['storage']['sounds'])

        self.limits = data['limits']
