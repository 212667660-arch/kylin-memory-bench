#!/usr/bin/env bash
set -u

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
OUT="${1:-$ROOT/runs/openkylin-validation/real-run}"
mkdir -p "$OUT"
cd "$ROOT"
PYTHON_BIN="${KMB_PYTHON:-$ROOT/.kmb-venv/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then PYTHON_BIN=python3; fi
overall=0

run_step() {
  name="$1"; shift
  set +e
  "$@" >"$OUT/$name.stdout.log" 2>"$OUT/$name.stderr.log"
  code=$?
  set -e
  printf '%s\t%s\n' "$name" "$code" | tee -a "$OUT/exit-codes.tsv"
  if [ "$code" -ne 0 ]; then overall=1; fi
  return 0
}

run_step os-release bash -c 'cat /etc/os-release'
run_step uname uname -a
run_step python-version "$PYTHON_BIN" --version
run_step pip-version "$PYTHON_BIN" -m pip --version
run_step install bash scripts/install_local.sh python3
export KMB_PYTHON="$ROOT/.kmb-venv/bin/python"
run_step env-probe "$KMB_PYTHON" scripts/env_probe.py --require-openkylin --json
run_step validate "$KMB_PYTHON" -m kmb.cli validate --strict --suite suites/core-zh.yaml
run_step compare "$KMB_PYTHON" -m kmb.cli compare --agents configs/agent-grok.yaml configs/agent-deepseek.yaml --suite suites/core-zh.yaml --out "$OUT/real-compare" --run-id openkylin-validation --seed 42 --retries 1 --timeout "${KMB_TIMEOUT:-180}"
run_step verify-grok "$KMB_PYTHON" scripts/verify_run.py "$OUT/real-compare/grok-api" --strict
run_step verify-deepseek "$KMB_PYTHON" scripts/verify_run.py "$OUT/real-compare/deepseek-api" --strict
run_step uninstall bash scripts/uninstall_local.sh
printf 'validation output: %s\n' "$OUT"
exit "$overall"
