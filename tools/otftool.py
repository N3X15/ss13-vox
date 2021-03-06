import sys
from pathlib import Path
import argparse
from enum import IntEnum

from ruamel.yaml import YAML
yaml = YAML(typ='rt')

sys.path.insert(0, '.')

from ss13vox.daemon.config import DaemonConfig
from ss13vox.daemon.gameserver import VOXGameServer
from ss13vox.utils import generate_preshared_key

DAEMON_YML = Path.cwd() / 'daemon.yml'
OTF_DIR = Path('.otf')
OTF_TMP_DIR = OTF_DIR / 'tmp'
GENERATED_SOUND_DIR = OTF_TMP_DIR / 'sounds'

def main():
    argp = argparse.ArgumentParser('otftool.py')

    subp = argp.add_subparsers()

    _handle_gameserver(subp)
    _handle_init_cmd(subp)

    args = argp.parse_args()

    if not hasattr(args, 'cmd') or getattr(args, 'cmd') is None:
        argp.print_help()
        return
    args.cmd(args)

def _handle_init_cmd(subp):
    p = subp.add_parser('init')
    p.add_argument('--baseurl', type=str, default=None)
    p.add_argument('--sounds-dir', type=str, default=GENERATED_SOUND_DIR)
    p.add_argument('--address', type=str, default='127.0.0.1')
    p.add_argument('--port', type=int, default=8080)
    p.add_argument('--gameservers', type=str, nargs='+', default=['main'], help='List of gameserver IDs to create')
    p.set_defaults(cmd=cmd_init)
def cmd_init(args: argparse.Namespace) -> None:
    with open(DAEMON_YML, 'w') as f:
        f.write('# VOX On-The-Fly Daemon Config\n')
        f.write('\n')
        f.write('# Werkzeug REST service configuration\n')
        f.write('http:\n')
        f.write('    # Leave this set to 127.0.0.1 unless your gameserver is on a different machine.\n')
        f.write('    # If you set this to 0.0.0.0, anyone can access the daemon. You don\'t want that.\n')
        f.write(f'    address: {args.address}\n')
        f.write('\n')
        f.write('    # Change this to an available TCP port.\n')
        f.write(f'    port: {args.port}\n')
        f.write('\n')
        f.write('    # Public URL base that clients should connect to for downloading soundfiles.\n')
        f.write('    # You need to point storage.sounds to wherever this is on the filesystem, or make a symlink.\n')
        f.write('    # Should be managed by nginx/lighttpd/apache\n')
        f.write('    #baseurl: http://hostname.domain.tld:port/path/to/sounds\n')
        f.write('    # Example: Lighttpd serving files over TLS on subdomain voxotf.nexisonline.net, port 443 (HTTPS default)\n')
        f.write('    #baseurl: https://voxotf.nexisonline.net/sounds\n')
        baseurl = args.baseurl or f'http://{args.address}:{args.port}/announcement/listen'
        f.write(f'    baseurl: {baseurl}\n')
        f.write('\n')
        f.write('# Game server config.\n')
        f.write('gameservers:\n')
        for srvid in args.gameservers:
            psk = generate_preshared_key()
            f.write(f'    # A server we refer to as "{srvid}". You can rename it to anything that can be used as a directory name on your OS.\n')
            f.write(f'    {srvid}:\n')
            f.write('        # Pre-shared secret key. You can re-generate with `python tools/gen-secret-key.py <gameserver id>`\n')
            f.write('        # REMEMBER TO GENERATE A NEW VOX.CFG IF THIS CHANGES!\n')
            f.write(f'        secret: {psk}\n')
        f.write('  # You can add additional servers here, with the same format.\n')
        f.write('  #test: ...\n')
        f.write('\n')
        f.write('storage:\n')
        f.write('    # Where various generated, but permanent files live.\n')
        f.write(f'    work: {OTF_DIR}\n')
        f.write('    # Where temporary generated sounds and files live. Deleted and rebuilt at startup.\n')
        f.write(f'    tmp: {OTF_TMP_DIR}\n')
        f.write('    # Where generated sounds live. Deleted and rebuilt at startup.\n')
        f.write(f'    #sounds: {GENERATED_SOUND_DIR}\n')
        f.write(f'    sounds: {args.sounds_dir}\n')
        f.write('\n')
        f.write('limits:\n')
        f.write('    nwords: {min: 1, max: 25}\n')
        f.write('    wordlen: {max: 50}\n')
        f.write('    phraselen: {min: 1, max: 140}\n')
    print('Wrote daemon.yml.')

def _handle_gameserver(subp):
    gsp = subp.add_parser('gameserver', aliases=['gs'])

    gs_subp = gsp.add_subparsers()

    _handle_gameserver_add(gs_subp)
    _handle_gameserver_dump_cfg(gs_subp)
    _handle_gameserver_regen_key(gs_subp)
    _handle_gameserver_remove(gs_subp)

def _handle_gameserver_add(subp):
    p = subp.add_parser('add', aliases=['new'])
    p.add_argument('gsid', type=str, help='Identifier for the gameserver')
    p.set_defaults(cmd=cmd_gameserver_add)
def cmd_gameserver_add(args: argparse.Namespace) -> None:
    cfg = DaemonConfig.load(DAEMON_YML)
    assert args.gsid not in cfg.gameservers
    gs = VOXGameServer()
    gs.id = args.gsid
    gs.generateSecretKey()
    cfg.gameservers[args.gsid] = gs
    cfg.saveTo(DAEMON_YML)

def _handle_gameserver_dump_cfg(subp):
    p = subp.add_parser('dump-cfg', aliases=['vox.cfg'])
    p.add_argument('gsid', type=str, help='Identifier for the gameserver')
    p.set_defaults(cmd=cmd_gameserver_dump_cfg)
def cmd_gameserver_dump_cfg(args: argparse.Namespace) -> None:
    cfg = DaemonConfig.load(DAEMON_YML)
    assert args.gsid in cfg.gameservers
    gs = cfg.gameservers[args.gsid]

    print('# VOX On-The-Fly Connection Configuration')
    print('# This file is used to configure VOX so that a separate daemon can generate sounds at request.')
    print('#')
    print('# Enable OTF? (yes/no, default=no)')
    print('ENABLED: yes')
    print('# Unique ID of the gameserver. Used for reference.')
    print(f'GSID: {args.gsid}')
    print('# IP address the OTF daemon is on. (default=127.0.0.1)')
    print(f'ADDRESS: {cfg.address}')
    print('# TCP port the OTF daemon is listening on. (default=8080)')
    print(f'PORT: {cfg.port}')
    print('# For security, a secret key is used as a handshake.')
    print(f'SECRET: {gs.secret_key}')

def _handle_gameserver_regen_key(subp):
    p = subp.add_parser('regen-key')
    p.add_argument('gsid', type=str, help='Identifier for the gameserver')
    p.set_defaults(cmd=cmd_gameserver_regen_key)
def cmd_gameserver_regen_key(args: argparse.Namespace) -> None:
    cfg = DaemonConfig.load(DAEMON_YML)
    assert args.gsid in cfg.gameservers
    cfg.gameservers[args.gsid].generateSecretKey()
    cfg.saveTo(DAEMON_YML)

def _handle_gameserver_remove(subp):
    p = subp.add_parser('remove')
    p.add_argument('gsid', type=str, help='Identifier for the gameserver')
    p.set_defaults(cmd=cmd_gameserver_remove)
def cmd_gameserver_remove(args: argparse.Namespace) -> None:
    cfg = DaemonConfig.load(DAEMON_YML)
    assert args.gsid in cfg.gameservers
    del cfg.gameservers[args.gsid]
    cfg.saveTo(DAEMON_YML)

if __name__ == '__main__':
    main()
