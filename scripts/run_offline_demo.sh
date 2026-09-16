#!/usr/bin/env bash
# Offline, credential-free end-to-end demo for reviewers.
# Uses only deterministic reference/flawed agents — no cloud API keys.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT="${1:-runs/offline-demo}"
PYTHON="${PYTHON:-python}"

echo "== KylinMemoryBench offline demo =="
echo "workspace: $ROOT"
echo "output:    $OUT"

echo
echo "[1/6] unit tests"
"$PYTHON" -m unittest discover -s tests -q

echo
echo "[2/6] validate suites"
"$PYTHON" -m kmb.cli validate --strict --suite suites/core-zh.yaml
"$PYTHON" -m kmb.cli validate --strict --suite suites/adversarial/core.yaml
"$PYTHON" -m kmb.cli validate --strict --suite suites/core-zh-expanded.yaml

echo
echo "[3/6] compare reference vs flawed (six-capability core)"
"$PYTHON" -m kmb.cli compare \
  --agents configs/agent-reference.yaml configs/agent-flawed.yaml \
  --suite suites/core-zh.yaml \
  --out "$OUT/core-compare" \
  --run-id offline-demo-core \
  --seed 42 --retries 0 --timeout 30

echo
echo "[4/6] compare on expanded suite"
"$PYTHON" -m kmb.cli compare \
  --agents configs/agent-reference.yaml configs/agent-flawed.yaml \
  --suite suites/core-zh-expanded.yaml \
  --out "$OUT/expanded-compare" \
  --run-id offline-demo-expanded \
  --seed 42 --retries 0 --timeout 30

echo
echo "[5/6] strict verify"
"$PYTHON" scripts/verify_run.py "$OUT/core-compare/reference" --strict
"$PYTHON" scripts/verify_run.py "$OUT/core-compare/flawed" --strict
"$PYTHON" scripts/verify_run.py "$OUT/expanded-compare/reference" --strict
"$PYTHON" scripts/verify_run.py "$OUT/expanded-compare/flawed" --strict

echo
echo "[6/6] open reports"
echo "HTML:  $OUT/core-compare/comparison.html"
echo "Radar: $OUT/core-compare/reference/radar.svg"
echo
echo "Boundary: reference/flawed are offline simulated baselines (source=simulated)."
echo "They validate the benchmark pipeline, not cloud model native memory."
echo "Done."
