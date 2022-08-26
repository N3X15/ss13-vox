import click
import logging
import os
import re
import sys
from pathlib import Path
from typing import Callable, FrozenSet, List, Optional, Set
from urllib.parse import urlparse

try:
	import apt
except:
	print('Please run `apt install python3-apt`!')
	sys.exit(1)

try:
	from buildtools import http, os_utils
	from buildtools.bt_logging import IndentLogger
except:
	print('pybuildtools not detected! Please run `python3 -m poetry install && sudo poetry run python setup.py`.')
	sys.exit(1)

SCRIPT_DIR = Path(__file__).parent

# Updated Apr 6 2022 for Ubuntu 20.04.4
REQUIRED_PACKAGES: Set[str] = {
	# Festival stuff
	'festival',

	# Lexicons
	'festlex-cmu',
	'festlex-poslex',
	'festlex-oald',

	# Voices
	'festvox-don',
	#'festvox-ellpc11k',
	'festvox-en1',
	'festvox-kallpc16k',
	'festvox-kdlpc16k',
	'festvox-rablpc16k',
	'festvox-us-slt-hts',
	'festvox-us1',
	'festvox-us2',
	'festvox-us3',

	# Needed by festival
	'libestools2.5',
	'unzip',

	# Voice speech dev stuff
	'flite',
	'flite-dev',

	# For our own nefarious purposes.
	'sox',
	'libsox-fmt-all',
	'vorbis-tools', #oggenc
	'ffmpeg',

	# It's 2022. I would like to use Python 3.10 but it is still not widely adopted yet.
	'python3.9'
}

# These should still work, for now.
NITECH_VOICES: Set[str] = {
	'http://hts.sp.nitech.ac.jp/archives/2.1/festvox_nitech_us_awb_arctic_hts-2.1.tar.bz2',
	'http://hts.sp.nitech.ac.jp/archives/2.1/festvox_nitech_us_bdl_arctic_hts-2.1.tar.bz2',
	'http://hts.sp.nitech.ac.jp/archives/2.1/festvox_nitech_us_clb_arctic_hts-2.1.tar.bz2',
	'http://hts.sp.nitech.ac.jp/archives/2.1/festvox_nitech_us_rms_arctic_hts-2.1.tar.bz2',
	'http://hts.sp.nitech.ac.jp/archives/2.1/festvox_nitech_us_slt_arctic_hts-2.1.tar.bz2',
	#'http://dl.dropbox.com/u/1845335/release/cmu_us_slt_arctic_hts.tar.gz', # Better but broken
	'http://hts.sp.nitech.ac.jp/archives/2.1/festvox_nitech_us_jmk_arctic_hts-2.1.tar.bz2',
	'http://hts.sp.nitech.ac.jp/archives/1.1.1/cmu_us_kal_com_hts.tar.gz',
	'http://hts.sp.nitech.ac.jp/archives/1.1.1/cstr_us_ked_timit_hts.tar.gz',
}

log=IndentLogger(logging.getLogger(__name__))

def InstallPackages():
	global REQUIRED_PACKAGES
	with log.info('Checking system packages...'):
		cache = apt.Cache()

		num_changes = 0
		with cache.actiongroup():
			for pkg in REQUIRED_PACKAGES:
				if not cache.has_key(pkg):
					log.critical('UNKNOWN APT PACKAGE {}!'.format(pkg))
					sys.exit(1)
				package = cache[pkg]
				if not package.is_installed:
					package.mark_install()
					num_changes += 1
		if num_changes == 0:
			log.info('No changes required, skipping.')
			return

		cache.commit(apt.progress.text.AcquireProgress(),
			apt.progress.base.InstallProgress())

def InstallHTS():
	with log.info('Installing Nitech HTS voices:'):
		HTS_TMP_DIR = Path('hts_tmp')
		HTS_TMP_DIR.mkdir(parents=True, exist_ok=True)
		with os_utils.Chdir('hts_tmp'):
			for uri in NITECH_VOICES:
				#os_utils.cmd(['wget','-c',uri], echo=True, show_output=True, critical=True)
				http.DownloadFile(uri, os.path.basename(urlparse(uri).path))
			for filename in os.listdir('.'):
				if os.path.isdir(filename): continue
				os_utils.cmd(['tar', 'xvf', filename], echo=True, show_output=False, critical=True)
			if not os.path.isdir('/usr/share/festival/voices/us'):
				os.makedirs('/usr/share/festival/voices/us')
			if not os.path.isdir('/usr/share/festival/voices/us/cmu_us_slt_arctic_hts'):
				os.makedirs('/usr/share/festival/voices/us/cmu_us_slt_arctic_hts')
			os_utils.copytree('cmu_us_slt_arctic_hts/', '/usr/share/festival/voices/us/cmu_us_slt_arctic_hts/')
			os_utils.copytree('lib/voices/us/', '/usr/share/festival/voices/us/')
			os_utils.copytree('lib/voices/us/', '/usr/share/festival/voices/us/')
			os_utils.single_copy('lib/hts.scm', '/usr/share/festival/hts.scm', as_file=True)

def FixHTS():
	with log.info('Fixing HTS...'):
		fixes = []
		#-(require 'hts)
		#+(require 'hts21compat)
		fixes += [[re.compile(r'\(require \'hts\)'),
			'(require \'hts21compat)']]
		#-(require_module 'hts_engine)
		#+(require_module 'hts21_engine)
		fixes += [[re.compile(r'\(require_module \'hts_engine\)'),
			'(require_module \'hts21_engine)']]
		#-(Parameter.set 'Synth_Method 'HTS)
		#+(Parameter.set 'Synth_Method 'HTS21)
		fixes += [[re.compile(r'\(Parameter.set \'Synth_Method \'HTS\)'),
			'(Parameter.set \'Synth_Method \'HTS21)']]

		files_changed=0
		for root, dirs, files in os.walk('/usr/share/festival/voices/us'):
			for filename in files:
				filename=os.path.join(root,filename)
				if filename.endswith('.scm'):
					fixed_filename=filename+'.fixed'
					changes=0
					with open(filename,'r') as orig:
						with open(fixed_filename,'w') as fixed:
							ln=0
							for line in orig:
								ln+=1
								origline=line
								for expr, replacement in fixes:
									line = expr.sub(replacement,line)
									if line!=origline:
										#print('# {}:{}'.format(filename,ln))
										#print(' -'+origline.strip('\r\n'))
										#print(' +'+line.strip('\r\n'))
										changes+=1
								fixed.write(line)
					if changes > 0:
						#print('Wrote '+fixed_filename)
						os.rename(fixed_filename,filename)
						#print('Renamed '+fixed_filename+' to '+filename)
						log.info(' Fixed {} ({} changes)'.format(filename,changes))
						files_changed+=1

					if os.path.exists(fixed_filename):
						os.remove(fixed_filename)
		log.info('{} files changed.'.format(files_changed))

def do_check(label: str, callback: Callable[[], bool]) -> None:
	click.secho(('  '+label+'...').rjust(80-4), nl=False)
	if callback():
		click.secho('PASS', fg='green')
	else:
		click.secho('FAIL', fg='red')
		sys.exit(1)

CHECK_POSTFIX: List[str] = []
CURRENT_LSB: Optional[str] = None
VALID_RELEASES: FrozenSet[str] = frozenset({
	'focal',
	'jammy'
})

def chk_uid() -> bool:
	return os.getuid() != 0

def get_base_prefix_compat():
    """Get base/real prefix, or sys.prefix if there is none."""
    return getattr(sys, "base_prefix", None) or getattr(sys, "real_prefix", None) or sys.prefix

def chk_venv() -> bool:
	return get_base_prefix_compat() != sys.prefix

def chk_lsb() -> bool:
	try:
		import lsb_release
		lsbdata: dict = {}
		if hasattr(lsb_release, 'get_distro_information'):
			lsbdata = lsb_release.get_distro_information()
		else:
			lsbdata = lsb_release.get_os_release()
		CURRENT_LSB = lsbdata['RELEASE']
		return CURRENT_LSB in VALID_RELEASES
	except:
		return False

def main():
	print('This script will set up your Ubuntu system for building VOX phrases.')
	with log.info('Sanity checks:'):
		do_check('Running as root', chk_uid)
		do_check('Checking Ubuntu release (LSB)', chk_lsb)
		do_check('Running in virtualenv (poetry shell)', chk_venv)

	InstallPackages()
	InstallHTS()
	FixHTS()

	log.info('Done!')

if __name__ == '__main__':
	main()
