import requests
import hashlib
import json

from enum import Enum
class EVoiceType(Enum):
    FEMININE = 'fem'
    MASCULINE = 'mas'

import logging
log = logging.getLogger(__name__)

class OTFClient:
    def __init__(self, address: str, port: int, srvid: str, secret: str) -> None:
        self.address: str = address
        self.port: int    = port
        self.srvid: str   = srvid
        self.secret: str  = secret

        self.session_key: str = None
        self.limits: dict = {}
        self.ip: str = ''

    @property
    def baseurl(self) -> str:
        return f'http://{self.address}:{self.port}'

    def calcAuth(self, *samples) -> None:
        samples = list(samples)
        samples.insert(0, self.session_key)
        data = b''
        for sample in samples:
            if isinstance(sample, (dict)):
                sample = json.dumps(sample)
            if isinstance(sample, (int, float)):
                sample = str(sample)
            if isinstance(sample, str):
                sample = sample.encode('utf-8')
            data += sample
        return hashlib.md5(self.session_key.encode('utf-8')+sample).hexdigest()

    def get(self, path: str, **kwargs) -> requests.Response:
        return requests.get(f'{self.baseurl}{path}', **kwargs)
    def post(self, path: str, **kwargs) -> requests.Response:
        return requests.post(f'{self.baseurl}{path}', **kwargs)

    def connect(self) -> None:
        res = self.get('/auth/server', params={
            'gsid': self.srvid
        })
        res.raise_for_status()
        challenge : str = res.json()['challenge']

        res = self.post('/auth/server', data={
            'challenge': challenge,
            'gsid':      self.srvid,
            'response':  hashlib.md5((challenge+self.secret).encode('utf-8')).hexdigest(),
        })
        res.raise_for_status()
        data: str = res.json()

        self.ip: str = data['ip']
        self.session_key = data['session']
        self.limits = data['limits']

    def getSoundFromPhrase(self, ckey: str, phrase: str, voice: EVoiceType) -> str:
        data = {
            'auth': self.calcAuth(phrase),
            'phrase': phrase,
            'voice': voice.value,
            'ckey': ckey,
            'gsid': self.srvid,
        }
        res = self.post('/announcement/new', data=data)
        res.raise_for_status()
        data = res.json()
        if data.get('error', False):
            log.error('%s Error: %s', data['source'], data['message'])
            return
        return data['url']

def main():
    from ruamel.yaml import YAML
    import argparse

    argp = argparse.ArgumentParser()
    argp.add_argument('--hostname', '-H', type=str, default='127.0.0.1')
    argp.add_argument('--port', '-p', type=int, default=8080)
    argp.add_argument('--config', '-c', type=str, default='daemon.yml')
    argp.add_argument('gsid', type=str)
    argp.add_argument('voice', choices=['mas', 'fem'])
    argp.add_argument('phrase', type=str)

    args = argp.parse_args()

    with open(args.config, 'r') as f:
        cfg = YAML().load(f)

    secret = cfg['gameservers'][args.gsid]['secret']

    client = OTFClient(args.hostname, args.port, args.gsid, secret)
    client.connect()
    print(client.getSoundFromPhrase('testbot', args.phrase, EVoiceType(args.voice)))

if __name__ == '__main__':
    main()
