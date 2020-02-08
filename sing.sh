# text2wave -mode singing america1.xml -o america1.wav
text2wave -mode singing $1 -o tmp/VOX-word.wav
./post-process.sh tmp/VOX-word.wav $2
