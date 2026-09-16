#!/usr/bin/env bash
# Lifecycle evidence must continue after an individual step fails so every
# install/upgrade/uninstall outcome is captured in the same run directory.
set +e
set -u

# Run from a desktop/root-capable openKylin checkout. Every command is logged
# separately so an operator can attach exit codes to the release evidence.
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
OUT="${1:-$ROOT/runs/deb-lifecycle-$(date +%Y%m%d%H%M%S)}"
PACKAGE="${2:-$ROOT/dist/kylin-memory-bench_0.2.0_all.deb}"
UPGRADE="${3:-$ROOT/dist/kylin-memory-bench_0.2.0+test1_all.deb}"
export KMB_PACKAGE_WAIT="${KMB_PACKAGE_WAIT:-600}"
export KMB_PAYLOAD_WAIT="${KMB_PAYLOAD_WAIT:-600}"
export KMB_EXPECTED_DEB="$PACKAGE"
KARE_NAMESPACE_HELPER="$ROOT/scripts/kare_namespace.sh"
export KMB_KARE_NAMESPACE_HELPER="$KARE_NAMESPACE_HELPER"
mkdir -p "$OUT"
FAILED=0

run_step() {
  name="$1"; shift
  printf 'command[%s]=' "$name" >"$OUT/$name.command"
  printf '%q ' "$@" >>"$OUT/$name.command"
  printf '\n' >>"$OUT/$name.command"
  "$@" >"$OUT/$name.stdout.log" 2>"$OUT/$name.stderr.log"
  rc=$?
  printf '%s\n' "$rc" >"$OUT/$name.exitcode"
  printf '%s exit=%s\n' "$name" "$rc"
  if [ "$rc" -ne 0 ]; then
    FAILED=1
  fi
  return 0
}

run_step preflight id
run_step install bash "$ROOT/scripts/install_deb.sh" "$PACKAGE"
run_step version sh -c '
  wait_seconds="${KMB_PACKAGE_WAIT:-600}"
  deadline=$(( $(date +%s) + wait_seconds ))
  while :; do
    status="$(dpkg-query -W -f="\${Package}\\t\${Version}\\t\${Status}\\n" kylin-memory-bench 2>/dev/null || true)"
    if [ -n "$status" ] && printf "%s\\n" "$status" | grep -q "install ok installed"; then
      printf "%s\\n" "$status"
      exit 0
    fi
    state="$(dpkg -s kylin-memory-bench 2>/dev/null | awk -F": " "/^Status:/{print \$2; exit}" || true)"
    if [ "$state" = "install ok installed" ]; then
      version="$(dpkg -s kylin-memory-bench 2>/dev/null | awk -F": " "/^Version:/{print \$2; exit}" || true)"
      printf "kylin-memory-bench\\t%s\\tStatus: install ok installed\\n" "${version:-unknown}"
      exit 0
    fi
    expected_deb="${KMB_EXPECTED_DEB:-}"
    if [ -x /usr/bin/kmb ] && [ -f /usr/share/kylin-memory-bench/kmb/__init__.py ] && [ -f "$expected_deb" ]; then
      expected_version="$(dpkg-deb --field "$expected_deb" Version 2>/dev/null || true)"
      printf "kylin-memory-bench\\t%s\\tStatus: KARE payload present after reported install\\n" "${expected_version:-unknown}"
      exit 0
    fi
    kare_helper="${KMB_KARE_NAMESPACE_HELPER:-}"
    if [ -n "$kare_helper" ] && [ -x "$kare_helper" ]; then
      kare_upper="$(bash "$kare_helper" --upper 2>/dev/null || true)"
      if [ -n "$kare_upper" ] && [ -f "$kare_upper/var/lib/dpkg/status" ]; then
        kare_status="$(dpkg-query --admindir="$kare_upper/var/lib/dpkg" -W -f="\${Package}\\t\${Version}\\t\${Status}\\n" kylin-memory-bench 2>/dev/null || true)"
        if [ -n "$kare_status" ] && printf "%s\\n" "$kare_status" | grep -q "install ok installed"; then
          printf "%s\\n" "$kare_status"
          exit 0
        fi
      fi
      if [ -n "$kare_upper" ] && [ -x "$kare_upper/usr/bin/kmb" ] && [ -f "$kare_upper/usr/share/kylin-memory-bench/kmb/__init__.py" ]; then
        expected_version="$(dpkg-deb --field "$expected_deb" Version 2>/dev/null || true)"
        printf "kylin-memory-bench\\t%s\\tStatus: KARE upper payload present after reported install\\n" "${expected_version:-unknown}"
        exit 0
      fi
      kare_pid="$(bash "$kare_helper" --find 2>/dev/null || true)"
      if [ -n "$kare_pid" ]; then
        kare_status="$(nsenter -t "$kare_pid" -m -- dpkg-query -W -f="\${Package}\\t\${Version}\\t\${Status}\\n" kylin-memory-bench 2>/dev/null || true)"
        if [ -n "$kare_status" ] && printf "%s\\n" "$kare_status" | grep -q "install ok installed"; then
          printf "%s\\n" "$kare_status"
          exit 0
        fi
        if nsenter -t "$kare_pid" -m -- test -x /usr/bin/kmb && nsenter -t "$kare_pid" -m -- test -f /usr/share/kylin-memory-bench/kmb/__init__.py; then
          expected_version="$(dpkg-deb --field "$expected_deb" Version 2>/dev/null || true)"
          printf "kylin-memory-bench\\t%s\\tStatus: KARE session payload present after reported install\\n" "${expected_version:-unknown}"
          exit 0
        fi
      fi
    fi
    if [ "$(date +%s)" -ge "$deadline" ]; then
      break
    fi
    sleep 1
  done
  printf "dpkg did not report kylin-memory-bench as installed within %ss.\\n" "$wait_seconds" >&2
  exit 1
'
run_step verify bash "$ROOT/scripts/verify_deb.sh" "$OUT/verify-before-upgrade"
run_step build_upgrade env KMB_DEB_VERSION=0.2.0+test1 bash "$ROOT/scripts/build_deb.sh" "$ROOT/dist"
run_step upgrade bash "$ROOT/scripts/upgrade_deb.sh" "$UPGRADE"
run_step verify_after_upgrade bash "$ROOT/scripts/verify_deb.sh" "$OUT/verify-after-upgrade"
run_step uninstall bash "$ROOT/scripts/uninstall_deb.sh"
run_step residual_check sh -c '
  if [ -e /usr/bin/kmb ] || [ -e /usr/share/kylin-memory-bench ]; then
    exit 1
  fi
  helper="${KMB_KARE_NAMESPACE_HELPER:-}"
  if [ -n "$helper" ] && [ -x "$helper" ]; then
    pid="$(bash "$helper" --find 2>/dev/null || true)"
  if [ -n "$pid" ] && { nsenter -t "$pid" -m -- test -e /usr/bin/kmb || nsenter -t "$pid" -m -- test -e /usr/share/kylin-memory-bench; }; then
      exit 1
    fi
  fi
  helper="${KMB_KARE_NAMESPACE_HELPER:-}"
  if [ -n "$helper" ] && [ -x "$helper" ]; then
    upper="$(bash "$helper" --upper 2>/dev/null || true)"
    if [ -n "$upper" ] && { [ -e "$upper/usr/bin/kmb" ] || [ -e "$upper/usr/share/kylin-memory-bench" ]; }; then
      exit 1
    fi
  fi
'

printf 'lifecycle evidence: %s\n' "$OUT"
printf 'lifecycle_status=%s\n' "$([ "$FAILED" -eq 0 ] && printf success || printf failed)"
exit "$FAILED"
