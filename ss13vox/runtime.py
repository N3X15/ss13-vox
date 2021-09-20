import os, json
from typing import Dict, List, Optional
from pathlib import Path
import tempfile

from buildtools import os_utils
from buildtools.config import YAMLConfig, BaseConfig

from ss13vox.consts import RECOMPRESS_ARGS, PRE_SOX_ARGS
from ss13vox.utils import md5sum, generate_random_string
from ss13vox.voice import Voice, VoiceRegistry, SFXVoice, USSLTFemale, EVoiceSex
from ss13vox.phrase import Phrase, EPhraseFlags, ParsePhraseListFrom, FileData
from ss13vox.pronunciation import Pronunciation, DumpLexiconScript, ParseLexiconText

import logging
log = logging.getLogger(__name__)

class VOXCommandExecutionFailed(Exception):
    pass

class VOXRuntime(object):
    def __init__(self) -> None:
        self.voices: List = []
        self.vox_sounds_path: str = ''
        self.templatefile: str = ''
        self.config: BaseConfig = BaseConfig()
        self.pathcfg: BaseConfig = BaseConfig()
        self.voice_assignments: Dict[str, List[str]] = {}
        self.voice_genders: Dict[str, Voice]
        self.all_voices: List[Voice] = []
        self.default_voice: Voice = None
        self.sfx_voice: SFXVoice = SFXVoice()
        self.configured_voices: Dict[str, dict] = {}
        self.lexicon: Dict[str, Pronunciation] = {}
        self.voice_genders: Dict[str, Voice] = {}

        self.cwd = os.getcwd()
        self.tmp_dir = os.path.join(self.cwd, 'tmp')
        self.dist_dir = os.path.join(self.cwd, 'dist')
        self.data_dir = os.path.join(self.cwd, 'data')
        self.preex_sound = os.path.join(self.cwd, 'sound', 'vox', '{ID}.wav')
        self.nuvox_sound = os.path.join(self.cwd, 'sound', 'vox_{SEX}', '{ID}.wav')
        self.vox_sounds_path = ''
        self.templatefile = ''
        self.vox_data_path = ''

    def loadConfig(self, config_yml_path: str = 'config.yml', paths_yml_path: str = 'paths.yml') -> None:
        self.config.cfg = YAMLConfig(config_yml_path)
        self.pathcfg.cfg = YAMLConfig(paths_yml_path).cfg[self.config.get('codebase', 'vg')]
        self.lexicon = ParseLexiconText('lexicon.txt')

    def initialize(self) -> None:
        self.preex_sound = self.pathcfg.get('sound.old-vox', os.path.join(self.cwd, 'sound', 'vox', '{ID}.wav'))
        self.nuvox_sound = self.pathcfg.get('sound.new-vox', os.path.join(self.cwd, 'sound', 'vox_{SEX}', '{ID}.wav'))
        self.vox_sounds_path = os.path.join(self.dist_dir, self.pathcfg.get('vox_sounds.path'))
        self.templatefile = self.pathcfg.get('vox_sounds.template')
        self.vox_data_path = os.path.join(self.dist_dir, self.pathcfg.get('vox_data'))

        self.default_voice = VoiceRegistry.Get(USSLTFemale.ID)

        os_utils.ensureDirExists(self.tmp_dir)
        os_utils.ensureDirExists(self.data_dir)

        for sexID, voiceid in self.config.get('voices', {'fem': USSLTFemale.ID}).items():
            voice = VoiceRegistry.Get(voiceid)
            assert sexID != ''
            voice.assigned_sex = sexID
            if sexID in ('fem', 'mas'):
                sex = EVoiceSex(sexID)
                assert voice.SEX == sex
                self.voices += [voice]
            elif sexID == 'default':
                default_voice = voice
            self.voice_assignments[voice.assigned_sex] = []
            self.all_voices += [voice]
            self.voice_genders[voice.assigned_sex] = voice
            self.configured_voices[sexID] = voice.serialize()
        self.voice_assignments[self.sfx_voice.assigned_sex] = []
        self.all_voices += [self.sfx_voice]
        self.voice_genders['sfx'] = self.sfx_voice
        self.configured_voices[self.sfx_voice.assigned_sex] = self.sfx_voice.serialize()

    def getVoiceByGCode(self, code: str) -> Voice:
        return self.voice_genders[code]

    def generateDictionaryLisp(self, voice: Voice, filename: str) -> None:
        # DumpLexiconScript(voice.FESTIVAL_VOICE_ID, lexicon.values(), 'tmp/VOXdict.lisp')
        DumpLexiconScript(voice.FESTIVAL_VOICE_ID, self.lexicon.values(), filename)

    def createSoundFromPhrase(self, phrase: Phrase, voice: Voice, filename: str, quiet: bool=False) -> FileData:
        '''
        This method is for creating sounds arbitrarily (for use in daemon.py).
        '''
        dict_lisp: Path
        phrasefile: Path
        sox_wav: Path
        soxpre_wav: Path
        word_wav: Path
        encoded_ogg: Path

        fdata = FileData()
        fdata.voice = voice.ID
        fdata.filename = filename

        files_to_clean = set()

        def getAndRegisterRandomName(ext) -> Path:
            fn = Path(self.tmp_dir) / (generate_random_string(32)+ext)
            files_to_clean.add(fn)
            return fn

        dict_lisp = getAndRegisterRandomName('.lisp') # 'tmp/VOXdict.lisp'
        phrasefile = getAndRegisterRandomName('.txt') # phrasefile
        sox_wav = getAndRegisterRandomName('.wav') # 'tmp/VOX-sox-word.wav'
        soxpre_wav = getAndRegisterRandomName('.wav') # 'tmp/VOX-soxpre-word.wav'
        word_wav = getAndRegisterRandomName('.wav') # 'tmp/VOX-word.wav'
        encoded_ogg = getAndRegisterRandomName('.ogg') # 'tmp/VOX-encoded.ogg'

        for f in files_to_clean:
            if f.is_file():
                f.unlink()
            #print(str(f))

        try:
            #print(dict_lisp.read_text())

            if not quiet:
                log.info('Generating {0} for {1} ({2!r})'.format(filename, voice.ID, phrase.phrase))
            text2wave = None
            if phrase.hasFlag(EPhraseFlags.SFX):
                text2wave = ['ffmpeg', '-i', phrase.phrase, str(word_wav)]
            else:
                self.generateDictionaryLisp(voice, str(dict_lisp))
                text2wave = ['text2wave']
                if dict_lisp.is_file():
                    text2wave += ['-eval', str(dict_lisp)]
                if phrase.hasFlag(EPhraseFlags.SING):
                    text2wave += ['-mode', 'singing', str(phrase.phrase)]
                else:
                    with open(phrasefile, 'w') as wf:
                        wf.write(phrase.phrase)
                    text2wave += [str(phrasefile)]
                text2wave += ['-o', str(word_wav)]

            cmds = []
            cmds += [(text2wave, str(word_wav))]
            if not phrase.hasFlag(EPhraseFlags.NO_PROCESS) or not phrase.hasFlag(EPhraseFlags.NO_TRIM):
                cmds += [(['sox', str(word_wav), str(soxpre_wav)] + PRE_SOX_ARGS.split(' '), str(soxpre_wav))]
            if not phrase.hasFlag(EPhraseFlags.NO_PROCESS):
                cmds += [(['sox', cmds[-1][1], str(sox_wav)] + voice.genSoxArgs(None), str(sox_wav))]
            cmds += [(['oggenc', cmds[-1][1], '-o', str(encoded_ogg)], str(encoded_ogg))]
            cmds += [(['ffmpeg', '-i', str(encoded_ogg)]+RECOMPRESS_ARGS+[filename], filename)]
            for command_spec in cmds:
                (command, cfn) = command_spec
                with os_utils.TimeExecution(command[0]):
                    os_utils.cmd(command, echo=False, critical=True, show_output=command[0] in ('text2wave',))

            command = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', filename]
            with os_utils.TimeExecution(command[0]):
                captured = os_utils.cmd_out(command, echo=False, critical=True)
                fdata.fromJSON(json.loads(captured))
                fdata.checksum = md5sum(filename)
                if (not phrase.hasFlag(EPhraseFlags.SFX)) and fdata.duration > 10.0:
                    fdata.duration -= 10.0

            for command_spec in cmds:
                (command, cfn) = command_spec
                if not os.path.isfile(cfn):
                    log.error("File '{0}' doesn't exist, command '{1}' probably failed!".format(cfn, command))
                    raise VOXCommandExecutionFailed
        finally:
            for f in files_to_clean:
                if f.is_file():
                    f.unlink()
