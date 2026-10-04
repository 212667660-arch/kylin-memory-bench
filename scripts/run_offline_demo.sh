#!/usr/bin/env bash
# Offline, credential-free end-to-end demo for reviewers.
# Dual agents: deterministic reference + openKylin process adapter (kylinbot-process).
# No cloud API keys. Radar/comparison only after both sides complete evaluation.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT="${1:-runs/offline-demo}"
PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  PYTHON=python
fi

echo "== KylinMemoryBench offline demo (no credentials) =="
echo "workspace: $ROOT"
echo "output:    $OUT"

echo
echo "[1/7] unit tests"
"$PYTHON" -m unittest discover -s tests -q

echo
echo "[2/7] validate suites"
"$PYTHON" -m kmb.cli validate --strict --suite suites/core-zh.yaml
"$PYTHON" -m kmb.cli validate --strict --suite suites/adversarial/core.yaml
"$PYTHON" -m kmb.cli validate --strict --suite suites/core-zh-expanded.yaml
"$PYTHON" -m kmb.cli validate --strict --suite suites/adversarial/extended.yaml

echo
echo "[3/7] compare reference vs kylinbot-process (openKylin process adapter) — core"
"$PYTHON" -m kmb.cli compare \
  --agents configs/agent-reference.yaml configs/agent-kylinbot-process.yaml \
  --suite suites/core-zh.yaml \
  --out "$OUT/core-compare" \
  --run-id offline-demo-core \
  --seed 42 --retries 0 --timeout 30

echo
echo "[4/7] compare on expanded 18-case suite"
"$PYTHON" -m kmb.cli compare \
  --agents configs/agent-reference.yaml configs/agent-kylinbot-process.yaml \
  --suite suites/core-zh-expanded.yaml \
  --out "$OUT/expanded-compare" \
  --run-id offline-demo-expanded \
  --seed 42 --retries 0 --timeout 30

echo
echo "[5/7] compare on adversarial-extended (conflict/similar/noise/sensitive/cross-task)"
"$PYTHON" -m kmb.cli compare \
  --agents configs/agent-reference.yaml configs/agent-kylinbot-process.yaml \
  --suite suites/adversarial/extended.yaml \
  --out "$OUT/adversarial-compare" \
  --run-id offline-demo-adversarial \
  --seed 42 --retries 0 --timeout 30

echo
echo "[6/7] contrast control: reference vs flawed (shows benchmark can separate errors)"
"$PYTHON" -m kmb.cli compare \
  --agents configs/agent-reference.yaml configs/agent-flawed.yaml \
  --suite suites/core-zh.yaml \
  --out "$OUT/flawed-contrast" \
  --run-id offline-demo-flawed \
  --seed 42 --retries 0 --timeout 30

echo
echo "[7/7] strict verify (only valid if both sides produced results)"
for pair in core-compare expanded-compare adversarial-compare flawed-contrast; do
  for agent in reference kylinbot-process flawed; do
    dir="$OUT/$pair/$agent"
    if [ -d "$dir" ]; then
      "$PYTHON" scripts/verify_run.py "$dir" --strict
    fi
  done
done

# Require radar + comparison artifacts before claiming success
for pair in core-compare expanded-compare adversarial-compare; do
  test -f "$OUT/$pair/comparison.html" || { echo "missing comparison.html in $pair"; exit 1; }
  test -f "$OUT/$pair/reference-radar.svg" || { echo "missing reference-radar.svg in $pair"; exit 1; }
  test -f "$OUT/$pair/kylinbot-process-radar.svg" || { echo "missing kylinbot-process-radar.svg in $pair"; exit 1; }
  test -f "$OUT/$pair/reference/result.json" || { echo "missing reference result in $pair"; exit 1; }
  test -f "$OUT/$pair/kylinbot-process/result.json" || { echo "missing process agent result in $pair"; exit 1; }
done

echo
echo "Reports (open in browser):"
echo "  $OUT/core-compare/comparison.html"
echo "  $OUT/expanded-compare/comparison.html"
echo "  $OUT/adversarial-compare/comparison.html"
echo
echo "Agents:"
echo "  reference        — offline deterministic baseline (simulated)"
echo "  kylinbot-process — openKylin ecosystem process adapter (source=process, system-level)"
echo
echo "Boundary: process adapter proves subprocess integration + system-level memory behavior,"
echo "not cloud model native memory. No credentials required."
echo "Done."
