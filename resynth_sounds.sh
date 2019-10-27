#!/bin/bash
# This shell file permits you to resynthesize purely synth sounds.

# Used in '.' - 0.5s of silence, mono
sox -c 1 -n samples/fullpause.ogg trim 0 0.5
# Used in ',' - 0.25s of silence, mono
sox -c 1 -n samples/halfpause.ogg trim 0 0.25
