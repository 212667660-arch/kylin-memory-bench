#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# A root lifecycle shell can be outside KARE's overlay namespace. Re-exec the
# verifier in the session namespace only when the local command is absent.
if { ! command -v kmb >/dev/null 2>&1 || \
     [ ! -f /usr/share/kylin-memory-bench/tests/smoke_test.py ] || \
     [ ! -f /usr/share/kylin-memory-bench/scripts/verify_run.py ]; } && \
   [ "${KMB_IN_NAMESPACE:-0}" != "1" ]; then
  kare_upper="$(bash "$SCRIPT_DIR/kare_namespace.sh" --upper 2>/dev/null || true)"
  if [ -n "$kare_upper" ]; then
    export KMB_IN_NAMESPACE=1
    export KMB_HOME="$kare_upper/usr/share/kylin-memory-bench"
    export PYTHONPATH="$KMB_HOME${PYTHONPATH:+:$PYTHONPATH}"
    export PATH="$kare_upper/usr/bin:$PATH"
  fi
  kare_pid="$(bash "$SCRIPT_DIR/kare_namespace.sh" --find 2>/dev/null || true)"
  if [ -z "${KMB_HOME:-}" ] && [ -n "$kare_pid" ]; then
    exec nsenter -t "$kare_pid" -m -- env KMB_IN_NAMESPACE=1 bash "$0" "$@"
  fi
fi

if ! command -v kmb >/dev/null 2>&1; then
  printf '%s\n' 'kmb is not installed or not on PATH.' >&2
  exit 2
fi
KMB_HOME="${KMB_HOME:-/usr/share/kylin-memory-bench}"
# Package verification must not create untracked __pycache__ files that make
# an otherwise successful KARE uninstall look like a payload residue.
export PYTHONDONTWRITEBYTECODE=1
OUT="${1:-${TMPDIR:-/tmp}/kmb-deb-verify-$(date +%Y%m%d%H%M%S)}"
mkdir -p "$OUT"

# openKylin KARE may expose the shadow payload a few seconds after dpkg
# reports success. Wait for the files this verifier actually needs so a
# transient mount race becomes an explicit failure instead of a false pass.
PAYLOAD_WAIT="${KMB_PAYLOAD_WAIT:-60}"
deadline=$((SECONDS + PAYLOAD_WAIT))
while [ ! -f "$KMB_HOME/tests/smoke_test.py" ] || [ ! -f "$KMB_HOME/scripts/verify_run.py" ]; do
  if [ "$SECONDS" -ge "$deadline" ]; then
    printf 'installed payload is not ready: %s\n' "$KMB_HOME" >&2
    exit 1
  fi
  sleep 1
done

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$KMB_HOME${PYTHONPATH:+:$PYTHONPATH}" KMB_HOME="$KMB_HOME" \
  /usr/bin/python3 -m unittest discover -s "$KMB_HOME/tests" -p 'smoke_test.py' -v | tee "$OUT/package-smoke-tests.log"
kmb validate --strict --suite "$KMB_HOME/suites/core-zh.yaml" | tee "$OUT/validate.json"
kmb compare \
  --agents "$KMB_HOME/configs/agent-reference.yaml" "$KMB_HOME/configs/agent-flawed.yaml" \
  --suite "$KMB_HOME/suites/core-zh.yaml" \
  --out "$OUT/smoke-compare" --run-id deb-smoke --seed 42 --retries 0 --timeout 30 \
  | tee "$OUT/compare.json"
/usr/bin/python3 "$KMB_HOME/scripts/verify_run.py" "$OUT/smoke-compare/reference" --strict | tee "$OUT/verify-reference.json"
/usr/bin/python3 "$KMB_HOME/scripts/verify_run.py" "$OUT/smoke-compare/flawed" --strict | tee "$OUT/verify-flawed.json"
printf 'deb smoke evidence: %s\n' "$OUT"
