#!/usr/bin/env bash
set -u

# Requires an active X11 desktop and ffmpeg. It intentionally records only the
# screen; credentials must be entered before recording or through hidden input.
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
OUT="${1:-$ROOT/runs/desktop-demo}"
DURATION="${2:-300}"
mkdir -p "$OUT"
if [ -z "${DISPLAY:-}" ]; then
  printf '%s\n' 'DISPLAY is not set; run this helper from the openKylin desktop terminal.' >&2
  exit 2
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
  printf '%s\n' 'ffmpeg is required.' >&2
  exit 2
fi
OUTPUT="$OUT/yiheng-openkylin-demo.mp4"
printf 'recording to %s for %ss\n' "$OUTPUT" "$DURATION"
ffmpeg -y -f x11grab -video_size "${KMB_CAPTURE_SIZE:-1280x720}" -framerate 15 -i "${DISPLAY}+0,0" -t "$DURATION" -c:v libx264 -preset veryfast -pix_fmt yuv420p "$OUTPUT"
rc=$?
printf '%s\n' "$rc" >"$OUT/record.exitcode"
if [ "$rc" -eq 0 ] && [ -f "$OUTPUT" ]; then
  sha256sum "$OUTPUT" >"$OUT/sha256.txt"
  ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUTPUT" >"$OUT/media-info.txt" 2>"$OUT/ffprobe.stderr.log" || true
fi
exit "$rc"
