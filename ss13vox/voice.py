from typing import List
from enum import IntEnum, IntFlag, Enum


# All available Festival voices:
# 'rab_diphone'
# These are the nitech-made ARCTIC voice, tut on how to install:
# http://ubuntuforums.org/showthread.php?t=751169 ("Installing the enhanced Nitech HTS voices" section)
# 'nitech_us_bdl_arctic_hts'
# 'nitech_us_jmk_arctic_hts'
# 'nitech_us_awb_arctic_hts'
# 'nitech_us_slt_arctic_hts'  # less bored US female
# 'nitech_us_clb_arctic_hts' # DEFAULT, bored US female (occasionally comes up with british pronunciations?!)
# 'nitech_us_rms_arctic_hts'

class EVoiceSex(Enum):
    MASCULINE = 'mas'
    FEMININE = 'fem'
    SFX = 'sfx'

class VoiceRegistry(object):
    ALL = {}

    @staticmethod
    def Register(cls) -> None:
        VoiceRegistry.ALL[cls.ID] = cls

    @staticmethod
    def Get(vid: str) -> 'Voice':
        return VoiceRegistry.ALL[vid]()

class Voice(object):
    #: Unique ID of the voice, used for config.
    ID: str = ''
    #: Used to determine if voice goes in vox_fem or vox_mas, also in idiot checks.
    SEX: EVoiceSex = EVoiceSex.MASCULINE
    #: Voice ID used with Festival.
    FESTIVAL_VOICE_ID: str = ''
    #: The phoneset used with the lexicon. Usually empty (default DMU phoneset)
    PHONESET: str = ''

    def __init__(self):
        self.assigned_sex: str = '' #e.g. fem, mas, default
        self.chorus:bool = True
        self.phaser:bool = True

    def genSoxArgs(self, args) -> List[str]:
        '''
        Generates arguments fed to SoX's command line.

        See the SoX(1) manpage for more information.
        '''
        # Standard SOX transformations used on all voices:
        sox_args = []
        if self.chorus:
            sox_args += [
                # Chorus adds harmonics, which makes it sound like multiple people are talking at once.
                # It also removes some of the monotone, and makes the voice sound more "natural".
                'chorus', '0.7', '0.9', '55', '0.4', '0.25', '2', '-t',
            ]
        if self.phaser:
            sox_args += [
                # Phaser distorts the sound a bit, making it sound more "digital" and "spacey"
                'phaser', '0.9', '0.85', '4', '0.23', '1.3', '-s',
            ]
        sox_args += [
            # Attenuate bass
            'bass', '-40',
            # Pass frequencies above whatever this is
            'highpass', '22', 'highpass', '22',
            # Dynamic range compression
            'compand', '0.01,1', '-90,-90,-70,-70,-60,-20,0,0', '-5', '-20',
            # Add some fake hallway echos
            # Good with stretch, otherwise sounds like bees.
            'echos', '0.3', '0.5', '100', '0.25', '10', '0.25',
            # Normalize volume
            'norm',

        ]
        return sox_args

    def serialize(self) -> dict:
        return {
            'id': self.ID,
            'sex': self.SEX.value,
            'festvox_id': self.FESTIVAL_VOICE_ID,
            'phoneset': self.PHONESET
        }

class USRMSMale(Voice):
    '''
    RMS US Male: Sounds a bit like DECTalk (Stephen Hawking).  Uses US pronunciations.
    '''
    ID = 'us-rms'
    SEX = EVoiceSex.MASCULINE
    FESTIVAL_VOICE_ID = 'nitech_us_rms_arctic_hts'
    def genSoxArgs(self, args) -> List[str]:
        sox_args = [
            # Drop pitch a bit.
            'pitch', '-200',
            # Starts the gravelly sound, lowers pitch a bit.
            'stretch', '1.1',

            # This was supposed to make it sound like the HL VOX by increasing the gravelly
            #  quality by "gating" the incoming stream, but it interferes with the voice's
            #  synth wave and causes problems like noise spikes and dead spots.
            #'synth', 'sine', 'amod', '55'
        ]
        return sox_args + super().genSoxArgs(args)
VoiceRegistry.Register(USRMSMale)

class ScotAWBMale(Voice):
    '''
    AWB Scottish Male: Sounds a bit like DECTalk (Stephen Hawking).  Uses US pronunciations.
    '''
    ID = 'scot-awb'
    SEX = EVoiceSex.MASCULINE
    FESTIVAL_VOICE_ID = 'nitech_us_awb_arctic_hts'
    def genSoxArgs(self, args) -> List[str]:
        sox_args = [
            # Drop pitch a bit.
            #'pitch', '-200',
            # Starts the gravelly sound, lowers pitch a bit.
            #'stretch', '1.1',

            # This was supposed to make it sound like the HL VOX by increasing the gravelly
            #  quality by "gating" the incoming stream, but it interferes with the voice's
            #  synth wave and causes problems like noise spikes and dead spots.
            #'synth', 'sine', 'amod', '55'
        ]
        return sox_args + super().genSoxArgs(args)
VoiceRegistry.Register(ScotAWBMale)

"""
BROKEN - Uses MRPA phoneset.

class RabDiphoneMale(Voice):
    '''
    RAB Diphone Male: British DECTalk, kinda.
    '''
    ID = 'rab-diphone'
    SEX = EVoiceSex.MASCULINE
    FESTIVAL_VOICE_ID = 'rab_diphone'
    def genSoxArgs(self, args) -> List[str]:
        sox_args = [
            # Drop pitch a bit.
            #'pitch', '-200',
            # Starts the gravelly sound, lowers pitch a bit.
            #'stretch', '1.1',
            'stretch', '1.2',

            # This was supposed to make it sound like the HL VOX by increasing the gravelly
            #  quality by "gating" the incoming stream, but it interferes with the voice's
            #  synth wave and causes problems like noise spikes and dead spots.
            #'synth', 'sine', 'amod', '55'
        ]
        return sox_args + super().genSoxArgs(args)
VoiceRegistry.Register(RabDiphoneMale)
"""

class USSLTFemale(Voice):
    '''
    SLT US Female: More midwestern voice, talks faster, but buggy and occasionally drops into British.

    Needs work, gravellation of voice is wrong.
    '''
    ID = 'us-slt'
    SEX = EVoiceSex.FEMININE
    FESTIVAL_VOICE_ID = 'nitech_us_slt_arctic_hts'
    def genSoxArgs(self, args) -> List[str]:
        sox_args = [
            # Starts the gravelly sound, lowers pitch a bit.
            'stretch', '1.1',
        ]
        return sox_args + super().genSoxArgs(args)
VoiceRegistry.Register(USSLTFemale)

class USCLBFemale(Voice):
    '''
    CLB US Female: The /vg/station original vox_fem voice. Enunciates clearly, practically no bugs.
    '''
    ID = 'us-clb'
    SEX = EVoiceSex.FEMININE
    FESTIVAL_VOICE_ID = 'nitech_us_clb_arctic_hts'
    def genSoxArgs(self, args) -> List[str]:
        sox_args = [
            # Starts the gravelly sound, lowers pitch a bit.
            'stretch', '1.1',
        ]
        return sox_args + super().genSoxArgs(args)
VoiceRegistry.Register(USCLBFemale)

class SFXVoice(Voice):
    '''
    Voice used for SFX. Not usable otherwise.
    '''
    ID = 'sfx'
    SEX = EVoiceSex.SFX
    FESTIVAL_VOICE_ID = None
    def __init__(self):
        super().__init__()
        self.assigned_sex = 'sfx'
        self.chorus = self.phaser = False

    def genSoxArgs(self, args) -> List[str]:
        # Just echos and DRC
        return super().genSoxArgs(args)
#VoiceRegistry.Register(NullVoice)
