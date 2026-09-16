#!/usr/bin/env bash
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
python -m kmb.cli compare \
  --agents configs/agent-reference.yaml configs/agent-flawed.yaml \
  --suite suites/core-zh.yaml \
  --out runs/demo
printf '报告已生成到 %s/runs/demo\n' "$ROOT"
