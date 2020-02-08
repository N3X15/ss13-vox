sox $1 tmp/VOX-soxpre-word.wav trim 0 -0.1
sox tmp/VOX-soxpre-word.wav tmp/VOX-sox-word.wav pitch -500 stretch 1.2 synth sine amod 60 chorus 0.7 0.9 55 0.4 0.25 2 -t phaser 0.9 0.85 4 0.23 1.3 -s bass -40 highpass 22 highpass 22 compand 0.01,1 -90,-90,-70,-70,-60,-20,0,0 -5 -20 echos 0.3 0.5 100 0.25 10 0.25 norm
oggenc tmp/VOX-sox-word.wav -o $2
