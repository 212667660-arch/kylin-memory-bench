#!/usr/bin/env bash
set -eu

if [ "$#" -ne 1 ]; then
  printf 'usage: %s PATH_TO_DEB\n' "$0" >&2
  exit 2
fi
PACKAGE_PATH=$1
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SUDO_TIMEOUT="${KMB_SUDO_TIMEOUT:-8}"
PACKAGE_WAIT="${KMB_PACKAGE_WAIT:-60}"
if [ ! -f "$PACKAGE_PATH" ]; then
  printf 'package not found: %s\n' "$PACKAGE_PATH" >&2
  exit 2
fi
if ! command -v dpkg >/dev/null 2>&1; then
  printf '%s\n' 'dpkg is required; run this script on openKylin or another Debian system.' >&2
  exit 2
fi
dpkg_rc=0
kare_success=0
if [ "$(id -u)" -eq 0 ]; then
  dpkg_log="$(mktemp)"
  set +e
  dpkg -i "$PACKAGE_PATH" 2>&1 | tee "$dpkg_log"
  dpkg_rc="${PIPESTATUS[0]}"
  set -e
  if grep -Eq 'status = 0, errinfo = .*安装成功|status = 0, errinfo = .*success' "$dpkg_log"; then
    kare_success=1
  fi
  rm -f "$dpkg_log"
else
  if ! timeout --signal=TERM --kill-after=2s "${SUDO_TIMEOUT}s" sudo -n dpkg -i "$PACKAGE_PATH"; then
    printf '%s\n' 'non-interactive sudo is unavailable; run as root or authenticate with sudo before retrying.' >&2
    exit 1
  fi
fi
if [ "$dpkg_rc" -ne 0 ] && [ "$kare_success" -ne 1 ]; then
  printf 'dpkg install failed with exit code %s.\n' "$dpkg_rc" >&2
  exit "$dpkg_rc"
fi

# KARE's dpkg wrapper can report success before its shadow payload and package
# database become visible. Wait for an authoritative installed state.
deadline=$((SECONDS + PACKAGE_WAIT))
while :; do
  status="$(dpkg-query -W -f='${Package}\t${Version}\t${Status}\n' kylin-memory-bench 2>/dev/null || true)"
  if [ -n "$status" ] && printf '%s\n' "$status" | grep -q 'install ok installed'; then
    printf '%s\n' "$status"
    exit 0
  fi
  state="$(dpkg -s kylin-memory-bench 2>/dev/null | awk -F': ' '/^Status:/{print $2; exit}' || true)"
  if [ "$state" = 'install ok installed' ]; then
    version="$(dpkg -s kylin-memory-bench 2>/dev/null | awk -F': ' '/^Version:/{print $2; exit}' || true)"
    printf 'kylin-memory-bench\t%s\tStatus: install ok installed\n' "${version:-unknown}"
    exit 0
  fi
  if [ "$kare_success" -eq 1 ]; then
    if [ -x /usr/bin/kmb ] && [ -f /usr/share/kylin-memory-bench/kmb/__init__.py ]; then
      printf 'KARE reported installation success and payload is present.\n'
      exit 0
    fi
    kare_upper="$(bash "$SCRIPT_DIR/kare_namespace.sh" --upper 2>/dev/null || true)"
    if [ -n "$kare_upper" ] && [ -x "$kare_upper/usr/bin/kmb" ] && \
      [ -f "$kare_upper/usr/share/kylin-memory-bench/kmb/__init__.py" ]; then
      printf 'KARE reported installation success and upper payload is present.\n'
      exit 0
    fi
    kare_pid="$(bash "$SCRIPT_DIR/kare_namespace.sh" --find 2>/dev/null || true)"
    if [ -n "$kare_pid" ] && nsenter -t "$kare_pid" -m -- test -x /usr/bin/kmb && \
      nsenter -t "$kare_pid" -m -- test -f /usr/share/kylin-memory-bench/kmb/__init__.py; then
      printf 'KARE reported installation success and session payload is present.\n'
      exit 0
    fi
  fi
  if [ "$SECONDS" -ge "$deadline" ]; then
    break
  fi
  sleep 1
done
printf 'dpkg did not report kylin-memory-bench as installed within %ss.\n' "$PACKAGE_WAIT" >&2
exit 1
