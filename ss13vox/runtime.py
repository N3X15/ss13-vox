import os
from typing import Dict, List, Optional
from buildtools import os_utils
from buildtools.config import YAMLConfig, BaseConfig

from ss13vox.voice import Voice, VoiceRegistry, SFXVoice, USSLTFemale, EVoiceSex
from ss13vox.pronunciation import Pronunciation, DumpLexiconScript, ParseLexiconText

class Runtime(object):
    def __init__(self) -> None:
        self.voices: List = []
        self.vox_sounds_path: str = ''
        self.templatefile: str = ''
        self.config: BaseConfig = BaseConfig()
        self.pathcfg: BaseConfig = BaseConfig()
        self.voice_assignments: Dict[str, List[str]] = {}
        self.all_voices: List[Voice] = []
        self.default_voice: Voice = None
        self.sfx_voice: SFXVoice = SFXVoice()
        self.configured_voices: Dict[str, dict] = {}
        self.lexicon: Dict[str, Pronunciation] = {}

        self.cwd = os.getcwd()
        self.tmp_dir = os.path.join(self.cwd, 'tmp')
        self.dist_dir = os.path.join(self.cwd, 'dist')
        self.data_dir = os.path.join(self.cwd, 'data')
        self.preex_sound = os.path.join(self.cwd, 'sound', 'vox', '{ID}.wav')
        self.nuvox_sound = os.path.join(self.cwd, 'sound', 'vox_{SEX}', '{ID}.wav')
        self.vox_sounds_path = ''
        self.templatefile = ''
        self.vox_data_path = ''

    def LoadConfig(self, config_yml_path: str = 'config.yml', paths_yml_path: str = 'paths.yml') -> None:
        self.config.cfg = YAMLConfig(config_yml_path)
        self.pathcfg.cfg = YAMLConfig(paths_yml_path).cfg[self.config.get('codebase', 'vg')]
        self.lexicon = self.ParseLexiconText('lexicon.txt')

    def Initialize(self) -> None:
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
            self.configured_voices[sexID] = voice.serialize()
        self.voice_assignments[self.sfx_voice.assigned_sex] = []
        self.all_voices += [self.sfx_voice]
        self.configured_voices[self.sfx_voice.assigned_sex] = self.sfx_voice.serialize()
