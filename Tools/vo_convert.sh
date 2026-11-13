#!/bin/bash
# ElevenLabs mp3 -> game wav: 48 kHz mono 16-bit, loudness -18 LUFS, 30 ms fade-in, trailing silence trimmed.
# usage: vo_convert.sh <in_dir_with_mp3> <out_dir>
in=$1; out=$2; mkdir -p "$out"
for f in "$in"/*.mp3; do
  b=$(basename "$f" .mp3)
  ffmpeg -loglevel error -y -i "$f" -af "afade=t=in:d=0.03,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse,loudnorm=I=-18:TP=-1.5:LRA=7" -ar 48000 -ac 1 -sample_fmt s16 "$out/$b.wav"
done
