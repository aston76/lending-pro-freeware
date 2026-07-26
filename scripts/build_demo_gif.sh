#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="docs/screenshots/demo.gif"
WORK="$(mktemp -d -t gifbuild)"
trap 'rm -rf "$WORK"' EXIT
W=980
H=612
HOLD=1.8
FPS=18
FRAMES=(dashboard-demo collections loans payments client-detail settings)
N=${#FRAMES[@]}
LIST="$WORK/inputs.txt"
: > "$LIST"
for ((i=0; i<N; i++)); do
  ffmpeg -y -i "docs/screenshots/${FRAMES[$i]}.png" -vf "scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1" -frames:v 1 "$WORK/f10.png" >/dev/null 2>&1
  echo "file '$WORK/f10.png'" >> "$LIST"
  echo "duration $HOLD" >> "$LIST"
done
echo "file '$WORK/f$((N-1)).png'" >> "$LIST"
ffmpeg -y -f concat -safe 0 -i "$LIST" -vf "fps=${FPS},split[s0][s1];[s0]palettegen=max_colors=256:stats_mode=diff[p];[s1][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle" -loop 0 "$OUT" >/dev/null 2>&1
ls -lh "$OUT"
