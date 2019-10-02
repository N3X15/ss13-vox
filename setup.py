print('This script will set up your Ubuntu system for building VOX phrases.')
#print('This assumes you are running on Ubuntu as root (run with sudo).')

import os, re, sys, logging, shutil
import apt

script_dir = os.path.dirname(os.path.realpath(__file__))

from buildtools import *
from buildtools import os_utils, bt_logging
from buildtools.wrapper import Git
from buildtools.bt_logging import IndentLogger

REQUIRED_PACKAGES = [
	# Festival stuff
	'festival','festlex-cmu','festlex-poslex','festlex-oald','libestools2.5','unzip',

	# For our own nefarious purposes.
	'sox',
	'libsox-fmt-all',
	'vorbis-tools', #oggenc
	'ffmpeg',

	# It's 2019
	'python3.6'
]

NITECH_VOICES = [
	'http://hts.sp.nitech.ac.jp/archives/2.1/festvox_nitech_us_awb_arctic_hts-2.1.tar.bz2',
	'http://hts.sp.nitech.ac.jp/archives/2.1/festvox_nitech_us_bdl_arctic_hts-2.1.tar.bz2',
	'http://hts.sp.nitech.ac.jp/archives/2.1/festvox_nitech_us_clb_arctic_hts-2.1.tar.bz2',
	'http://hts.sp.nitech.ac.jp/archives/2.1/festvox_nitech_us_rms_arctic_hts-2.1.tar.bz2',
	'http://hts.sp.nitech.ac.jp/archives/2.1/festvox_nitech_us_slt_arctic_hts-2.1.tar.bz2',
	#'http://dl.dropbox.com/u/1845335/release/cmu_us_slt_arctic_hts.tar.gz', # Better but broken
	'http://hts.sp.nitech.ac.jp/archives/2.1/festvox_nitech_us_jmk_arctic_hts-2.1.tar.bz2',
	'http://hts.sp.nitech.ac.jp/archives/1.1.1/cmu_us_kal_com_hts.tar.gz',
	'http://hts.sp.nitech.ac.jp/archives/1.1.1/cstr_us_ked_timit_hts.tar.gz',
]

log=None
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
		if not os.path.isdir('hts_tmp'):
			os.makedirs('hts_tmp')
		with Chdir('hts_tmp'):
			for uri in NITECH_VOICES:
				cmd(['wget','-c',uri], echo=True, show_output=True, critical=True)
			for filename in os.listdir('.'):
				if os.path.isdir(filename): continue
				cmd(['tar', 'xvf', filename], echo=True, show_output=False, critical=True)
			if not os.path.isdir('/usr/share/festival/voices/us'):
				os.makedirs('/usr/share/festival/voices/us')
			if not os.path.isdir('/usr/share/festival/voices/us/cmu_us_slt_arctic_hts'):
				os.makedirs('/usr/share/festival/voices/us/cmu_us_slt_arctic_hts')
			os_utils.copytree('cmu_us_slt_arctic_hts/', '/usr/share/festival/voices/us/cmu_us_slt_arctic_hts/')
			os_utils.copytree('lib/voices/us/', '/usr/share/festival/voices/us/')
			os_utils.copytree('lib/voices/us/', '/usr/share/festival/voices/us/')
			shutil.copy2('lib/hts.scm', '/usr/share/festival/hts.scm')

def fix_HTS():
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



logFormatter = logging.Formatter(fmt='%(asctime)s [%(levelname)-8s]: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')  # , level=logging.INFO, filename='crashlog.log', filemode='a+')
log = logging.getLogger()
log.setLevel(logging.INFO)

#fileHandler = logging.handlers.RotatingFileHandler(os.path.join(LOGPATH, 'crash.log'), maxBytes=1024 * 1024 * 50, backupCount=0)  # 50MB
#fileHandler.setFormatter(logFormatter)
#log.addHandler(fileHandler)

log = IndentLogger(log)
bt_logging.log = log
# consoleHandler = logging.StreamHandler()
# consoleHandler.setFormatter(logFormatter)
# log.addHandler(consoleHandler)

with log.info('Permissions check:'):
	if os.getuid() != 0:
		log.critical('This script is required to be run as root. Example:')
		log.critical('$ sudo python setup.py')
		sys.exit(1)
	else:
		log.info('I am root.')

InstallPackages()
InstallHTS()
fix_HTS()
