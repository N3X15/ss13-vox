import argparse, os
from buildtools import os_utils

argp = argparse.ArgumentParser()
argp.add_argument('--voice', '-V', choices=['fem','mas'], default='mas')
argp.add_argument('words', nargs='+', help='The words you wish to play.')
args = argp.parse_args()
cmd=[os_utils.which('play')]
cmd += [os.path.join('dist', 'sound', f'vox_{args.voice}', w.strip()+'.ogg') for w in args.words]
os_utils.cmd(cmd,echo=True,show_output=True, globbify=False)
