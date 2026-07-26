#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="docs/screenshots/demo.gif"
WORK="$(mktemp -d -t gifbuild)"
trap 'rm -rf "$WORK"' EXIT

W=720
H=450
HOLD=1.8
XF=0.7
FPS=12
FRAMES=(dashboard-demo loans payments client-detail)
N=${#FRAMES[@]}

for ((i=0; i<N; i++)); do
  ffmpeg -y -loop 1 -i "docs/screenshots/${FRAMES[$i]}.png" -t "$HOLD" \
    -vf "scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1,format=yuv420p" \
    "$WORK/c${i}.mp4" >/dev/null 2>&1
done

CUR="$WORK/c0.mp4"
for ((i=1; i<N; i++)); do
  OFF=$(python3 -c "print(round($i*$HOLD - $i*$XF, 3))")
  ffmpeg -y -i "$CUR" -i "$WORK/c${i}.mp4" \
    -filter_complex "[0:v][1:v]xfade=transition=fade:duration=$XF:offset=$OFF,format=yuv420p" \
    "$WORK/m${i}.mp4" >/dev/null 2>&1
  CUR="$WORK/m${i}.mp4"
done

ffmpeg -y -i "$CUR" -filter_complex "[0:v] fps=${FPS},split[s0][s1];[s0]palettegen=max_colors=128:stats_mode=diff[p];[s1][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle" -loop 0 "$OUT" >/dev/null 2>&1

ls -lh "$OUT"
