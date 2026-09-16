#!/usr/bin/env bash
set -eu

if [ "$#" -lt 2 ]; then
  printf 'usage: %s AGENT_A_CONFIG AGENT_B_CONFIG [SUITE] [OUT]\n' "$0" >&2
  exit 2
fi
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
PYTHON_BIN="${KMB_PYTHON:-}"
if [ -z "$PYTHON_BIN" ] && [ -x "$ROOT/.kmb-venv/bin/python" ]; then PYTHON_BIN="$ROOT/.kmb-venv/bin/python"; fi
if [ -z "$PYTHON_BIN" ]; then PYTHON_BIN=python3; fi
if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then PYTHON_BIN=python; fi
AGENT_A="$1"
AGENT_B="$2"
SUITE="suites/core-zh.yaml"
OUT="runs/acceptance-script"
TIMEOUT="${KMB_TIMEOUT:-180}"
if [ "$#" -ge 3 ]; then SUITE="$3"; fi
if [ "$#" -ge 4 ]; then OUT="$4"; fi

for CONFIG in "$AGENT_A" "$AGENT_B"; do
  TYPE=$("$PYTHON_BIN" -c 'import sys,yaml; p=yaml.safe_load(open(sys.argv[1], encoding="utf-8")); print(str(p.get("type", "")).lower())' "$CONFIG")
  case "$TYPE" in
    command|replay|http|openai|openai_compatible) ;;
    memory_controller) printf 'notice: %s is wrapper-assisted; report it as system-level behavior, not native model memory\n' "$CONFIG" >&2 ;;
    memory_disabled) printf 'notice: %s is a real-backend no-memory baseline; report it separately from wrapper-assisted/native memory\n' "$CONFIG" >&2 ;;
    *) printf 'formal acceptance requires a non-deterministic external adapter; got %s for %s\n' "$TYPE" "$CONFIG" >&2; exit 2 ;;
  esac
done

"$PYTHON_BIN" scripts/env_probe.py --require-openkylin --json
"$PYTHON_BIN" -m kmb.cli validate --strict --suite "$SUITE"
"$PYTHON_BIN" -m kmb.cli compare --agents "$AGENT_A" "$AGENT_B" --suite "$SUITE" --out "$OUT" --run-id acceptance-script --seed 42 --retries 1 --timeout "$TIMEOUT"
"$PYTHON_BIN" scripts/verify_run.py "$OUT/$("$PYTHON_BIN" -c 'import sys,yaml; p=yaml.safe_load(open(sys.argv[1], encoding="utf-8")); print(p["name"])' "$AGENT_A")" --strict
"$PYTHON_BIN" scripts/verify_run.py "$OUT/$("$PYTHON_BIN" -c 'import sys,yaml; p=yaml.safe_load(open(sys.argv[1], encoding="utf-8")); print(p["name"])' "$AGENT_B")" --strict
printf 'acceptance artifacts: %s\n' "$ROOT/$OUT"
