#!/usr/bin/env bash
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
PYTHON_BIN="${KMB_PYTHON:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN=python
fi
"$PYTHON_BIN" -m kmb.cli compare \
  --agents configs/agent-reference.yaml configs/agent-flawed.yaml \
  --suite suites/core-zh.yaml \
  --out runs/demo
printf '报告已生成到 %s/runs/demo\n' "$ROOT"
