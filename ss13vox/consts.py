# Direct from TG's PR (https://github.com/tgstation/tgstation/pull/36492)
# May bump up quality and rate slightly...
RECOMPRESS_ARGS = [
    # Audio Codec
    '-c:a',     'libvorbis',
    # Force to mono (should already be, since festival outputs mono...)
    '-ac',      '1',
    # Sampling rate in Hz. TG uses 16kHz.
    '-ar',      '16000',
    # Audio quality [0,9]. TG uses 0.
    '-q:a',     '0',
    # Playback speed
    '-speed',   '0',
    # Number of threads to use.  This works OK on my laptop, but you may need fewer
    # Now specified in -j.
    #'-threads', '8',
    # Force overwrite
    '-y']

# Have to do the trimming seperately.
PRE_SOX_ARGS = 'trim 0 -0.1'  # Trim off last 0.2s.
