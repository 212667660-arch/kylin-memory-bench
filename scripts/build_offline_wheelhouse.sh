#!/usr/bin/env bash
set -eu

# Prepare dependencies on the same architecture and Python ABI as the target.
# This script may use the network; the resulting wheelhouse can be copied to an
# isolated openKylin host and consumed through KMB_OFFLINE_WHEELHOUSE.
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
OUT="${1:-$ROOT/dist/offline-wheelhouse}"
PYTHON_BIN="${2:-python3}"
mkdir -p "$OUT"

"$PYTHON_BIN" -m pip download --dest "$OUT" "PyYAML>=6.0"
"$PYTHON_BIN" -m pip wheel --no-deps --wheel-dir "$OUT" "$ROOT"
printf 'offline wheelhouse prepared: %s\n' "$OUT"
