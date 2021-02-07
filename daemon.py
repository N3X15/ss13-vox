import os, string, random, json, hashlib, uuid, datetime, shutil, collections
from pathlib import Path
from typing import Dict, Any, List, Optional

from jinja2 import Environment
from jinja2 import FileSystemLoader
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import NotFound
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.routing import Map
from werkzeug.routing import Rule
from werkzeug.urls import url_parse
from werkzeug.utils import redirect
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response

import logging
if not os.path.isdir('logs'):
    os.makedirs('logs')
logging.basicConfig(filename='logs/daemon.log',
                    filemode='w',
                    #encoding='utf-8', 3.9
                    level=logging.INFO)
log = logging.getLogger(__name__)

from ruamel.yaml import YAML
yaml = YAML(typ='safe')

from ss13vox.runtime import VOXRuntime
from ss13vox.phrase import Phrase
from ss13vox.utils import generate_preshared_key
from ss13vox.daemon.config import DaemonConfig
from ss13vox.daemon.gameserver import VOXGameServer
from ss13vox.daemon.phraseref import PhraseRef

DAEMON_YML = Path.cwd() / 'daemon.yml'
OTF_DIR = Path('.otf') / 'tmp' / 'sounds'
OTF_TMP_DIR = OTF_DIR / 'tmp'
GENERATED_SOUND_DIR = Path('.otf') / 'tmp' / 'sounds'

# Order of operations:
#  Auth:
#  1. GET /auth/server, response is random challenge token
#  2. POST /auth/server with response and gsid, response is session key and limits
#  New Announcement:
#  1. GS: POST /announcement/new with gsid, auth, ckey and phrase
#  2. OTF responds with CDN URI

class WZService:
    def __init__(self) -> None:
        self.url_map: Map = None

    def render_template(self, template_name, **context):
        t = self.jinja_env.get_template(template_name)
        return Response(t.render(context), mimetype="text/html")

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, f"handle_{endpoint}")(request, **values)
        except NotFound:
            return self.error_404()
        except HTTPException as e:
            return e

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

class JinjaMixin:
    def __init__(self) -> None:
        self.template_path: Path = None
        self.jinja_env: Environment = None

    def setupJinja(self, tmpl_dir) -> None:
        self.template_path = tmpl_dir
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_path), autoescape=True
        )


class VoxRESTService(WZService, JinjaMixin):
    def __init__(self, config: Dict[str, Any]):
        super().__init__()

        self.config: Dict[str, Any] = config

        self.gameservers: Dict[str, VOXGameServer] = {}

        self.setupJinja(Path.cwd() / "templates")
        #self.jinja_env.filters["hostname"] = get_hostname

        self.url_map = Map(
            [
                Rule("/",                         endpoint="index"),
                Rule("/auth/server",              endpoint="auth_server"),
                Rule("/announcement/new",         endpoint="announcement_new"),
                Rule("/announcement/listen/<id>", endpoint="announcement_listen"),
            ]
        )

        self.runtime = VOXRuntime()
        self.runtime.loadConfig()
        self.runtime.initialize()

        self.baseurl = Path(self.config['http']['baseurl'])
        self.basepath = Path(self.config['storage']['sounds'])

        if self.basepath.is_dir():
            log.info('Clearing sound storage at %s...', self.soundbasepath)

    def handle_index(self) -> Response:
        return Response('This endpoint is not intended for human consumption')

    def jsonify(*args, **kwargs) -> Response:
        return Response(json.dumps(dict(*args, **kwargs), indent=None), mimetype='application/json')

    def handle_auth_server(self, request: Request) -> Response:
        if request.method == 'GET' and 'gsid' in request.form:
            return self.jsonify({'challenge': generate_preshared_key()})

        if request.method == 'POST' and 'response' in request.form and 'gsid' in request.form and 'challenge' in request.form:
            challenge = request.form['challenge']
            gsid = request.form['gsid']
            response  = request.form['response']
            if gsid not in self.gameservers:
                log.info('Failed GS %r login from address %s', gsid, request.remote_addr)
                return Response.make(403, b'Access Denied', {'Content-Type': 'text/html'})

            gss = VOXGameServer(gsid)
            gss.loadFrom(self.config)

            expected = hashlib.md5((challenge+gss.secret_key).decode('utf-8')).hexdigest()
            if response != gss.expected:
                log.info('Failed GS %r login from address %s', gsid, request.remote_addr)
                return Response.make(403, b'Access Denied', {'Content-Type': 'text/html'})

            gss.session_key = generate_preshared_key()
            gss.remote_addr = request.remote_addr

            self.gameservers[gss.id] = gss

            gss.basepath = self.basepath / gss.id
            if gss.basepath.is_dir():
                shutil.rmtree(gss.basepath)
            gss.basepath.mkdir(parents=True)

            log.info('[%s] Successfully logged in from address %s', gss.id, request.remote_addr)
            return self.jsonify({
                'ip':      request.remote_addr,
                'session': gss.session_key,
                'limits':  self.config['limits']
            })

    def handle_announcement_new(self, request: Request) -> Response:
        if request.method == 'POST' and 'a' in request.form and 'p' in request.form and 'v' in request.form and 'c' in request.form and 's' in request.form:
            authkey = request.form['a']
            phrase = request.form['p']
            voice = request.form['v']
            ckey = request.form['c']
            srvid = request.form['s']

            if srvid not in self.gameservers:
                log.error('FAILED AUTH: %s tried to request an announcement as GSS %r, which doesn\'t exist.', request.remote_addr, srvid)
                return Response.make(403, b'Access Denied', {'Content-Type': 'text/html'})

            gss = self.gameservers[srvid]
            if request.form['a'] != hashlib.md5sum((self.session_key+phrase).encode('utf-8')).hexdigest():
                log.error('FAILED AUTH: %r via %r requested phrase %r with voice %r', ckey, request.remote_addr, phrase, voice)
                return Response.make(403, b'Access Denied', {'Content-Type': 'text/html'})

            log.info('[%s]: %s requested phrase %r with voice %r', srvid, ckey, phrase, voice)
            if voice not in ('mas', 'fem'):
                return self.jsonify({'error': True, 'source': 'user', 'message': f'Incorrect voice.'})

            phraselen = len(phrase)
            limit = self.config['limits']['phraselen']['min']
            if phraselen < limit:
                return self.jsonify({'error': True, 'source': 'user', 'message': f'Too few characters. (your phraselen={phraselen}, limits.phraselen.min={limit})'})

            limit = self.config['limits']['phraselen']['max']
            if phraselen > limit:
                return self.jsonify({'error': True, 'source': 'user', 'message': f'Too many characters. (your phraselen={phraselen}, limits.phraselen.max={limit})'})

            p = Phrase()
            p.phrase = phrase
            p.parsed_phrase = phrase.split(' ')
            p.wordlen = len(self.parsed_phrase)
            limit = self.config['limits']['nwords']['min']
            if p.wordlen < limit:
                return self.jsonify({'error': True, 'source': 'user', 'message': f'Too few words. (your wordlen={phrase.wordlen}, limits.nwords.min={limit})'})

            limit = self.config['limits']['nwords']['max']
            if p.wordlen > limit:
                return self.jsonify({'error': True, 'source': 'user', 'message': f'Too many words. (your wordlen={phrase.wordlen}, limits.nwords.max={limit})'})

            wordlens = [len(w) for w in p.parsed_phrase]
            maxwordlen = max(wordlens)

            limit = self.config['limits']['wordlen']['max']
            if maxwordlen > limit:
                return self.jsonify({'error': True, 'source': 'user', 'message': f'A word was too big. (max(len(word), ...)={maxwordlen}, limits.wordlen.max={limit})'})

            pr: PhraseRef = self.gameservers[srvid].getPhrase(voice, phrase)
            if pr is None:
                sid = str(uuid.uuid4())
                path = gss.basepath / f'{sid}.ogg'
                url = f'{gss.baseurl}/{sid}.ogg'
                pr = PhraseRef(sid, path, url)
                self.runtime.createSoundFromPhrase(phrase, self.runtime.getVoiceByGCode(voice), str(path))
                gss.addPhrase(pr)

            return self.jsonify({
                'id': pr.id,
                'url': pr.url,
            })

def main():
    global OTF_DIR, OTF_TMP_DIR, OTF_SOUNDS_DIR
    import argparse

    if not os.path.isfile('daemon.yml'):
        print('Run `python tools/otftool.py init` first, then edit daemon.yml.')
        return

    with open('daemon.yml', 'r') as f:
        cfg = yaml.load(f)
        OTF_DIR = cfg['storage']['work']
        OTF_TMP_DIR = cfg['storage']['tmp']
        GENERATED_SOUND_DIR = cfg['storage']['sounds']

    app = VoxRESTService(cfg)
    from werkzeug.serving import run_simple
    run_simple(cfg['http']['address'], cfg['http']['port'], app, use_debugger=cfg['http'].get('debug', False), use_reloader=False)

if __name__ == '__main__':
    main()
