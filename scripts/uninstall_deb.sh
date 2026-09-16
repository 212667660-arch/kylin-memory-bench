#!/usr/bin/env bash
set -eu
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SUDO_TIMEOUT="${KMB_SUDO_TIMEOUT:-8}"
PACKAGE_WAIT="${KMB_PACKAGE_WAIT:-60}"

kare_pid=""
kare_upper=""
if [ "${KMB_IN_NAMESPACE:-0}" != "1" ]; then
  kare_pid="$(bash "$SCRIPT_DIR/kare_namespace.sh" --find 2>/dev/null || true)"
  kare_upper="$(bash "$SCRIPT_DIR/kare_namespace.sh" --upper 2>/dev/null || true)"
fi

if ! command -v dpkg >/dev/null 2>&1; then
  printf '%s\n' 'dpkg is required; run this script on openKylin or another Debian system.' >&2
  exit 2
fi
package_is_installed() {
  if dpkg-query -W -f='${db:Status-Status}' kylin-memory-bench 2>/dev/null | grep -qx installed; then
    return 0
  fi
  if dpkg -s kylin-memory-bench 2>/dev/null | grep -q '^Status: install ok installed$'; then
    return 0
  fi
  [ -n "$kare_upper" ] || return 1
  [ -f "$kare_upper/var/lib/dpkg/status" ] || return 1
  dpkg-query --admindir="$kare_upper/var/lib/dpkg" -W -f='${db:Status-Status}' kylin-memory-bench 2>/dev/null | grep -qx installed
}

payload_is_present() {
  if [ -e /usr/bin/kmb ] || [ -e /usr/share/kylin-memory-bench ]; then
    return 0
  fi
  if [ -n "$kare_upper" ] && { [ -e "$kare_upper/usr/bin/kmb" ] || [ -e "$kare_upper/usr/share/kylin-memory-bench" ]; }; then
    return 0
  fi
  [ -n "$kare_pid" ] || return 1
  nsenter -t "$kare_pid" -m -- sh -c \
    '[ -e /usr/bin/kmb ] || [ -e /usr/share/kylin-memory-bench ]'
}

cleanup_tree_bytecode() {
  root="$1"
  [ -n "$root" ] || return 0
  case "$root" in
    /usr/share/kylin-memory-bench|\
    /opt/kare-applications/shadow/upper/usr/share/kylin-memory-bench|\
    /opt/kare/shadow/upper/usr/share/kylin-memory-bench)
      ;;
    *)
      printf 'refusing to clean outside package payload: %s\n' "$root" >&2
      return 2
      ;;
  esac
  [ -d "$root" ] || return 0
  [ ! -L "$root" ] || return 2
  find "$root" -type f -name '*.pyc' -delete
  find "$root" -type d -name '__pycache__' -prune -exec rm -rf -- {} +
  find "$root" -depth -type d -empty -delete
}

cleanup_generated_bytecode() {
  # Verification can create bytecode outside dpkg's manifest. Clean only the
  # package payload in the host/upper views and the known KARE session view.
  cleanup_tree_bytecode /usr/share/kylin-memory-bench || true
  if [ -n "$kare_upper" ]; then
    cleanup_tree_bytecode "$kare_upper/usr/share/kylin-memory-bench" || true
  fi
  if [ -n "$kare_pid" ]; then
    nsenter -t "$kare_pid" -m -- /bin/sh -c '
      root=/usr/share/kylin-memory-bench
      [ -d "$root" ] || exit 0
      [ ! -L "$root" ] || exit 2
      find "$root" -type f -name "*.pyc" -delete
      find "$root" -type d -name "__pycache__" -prune -exec rm -rf -- {} +
      find "$root" -depth -type d -empty -delete
    ' 2>/dev/null || true
  fi
}

installed=0
if package_is_installed || payload_is_present; then
  installed=1
else
  # KARE may publish the package state after the dpkg wrapper returns.
  deadline=$((SECONDS + PACKAGE_WAIT))
  while [ "$SECONDS" -lt "$deadline" ]; do
    if package_is_installed || payload_is_present; then
      installed=1
      break
    fi
    sleep 1
  done
fi
if [ "$installed" -eq 1 ]; then
  cleanup_generated_bytecode
  if [ "$(id -u)" -eq 0 ]; then
    dpkg_log="$(mktemp)"
    set +e
    dpkg -r kylin-memory-bench 2>&1 | tee "$dpkg_log"
    dpkg_rc="${PIPESTATUS[0]}"
    set -e
    if [ "$dpkg_rc" -ne 0 ] && grep -Eq '卸载成功|remove.*success|removal.*success' "$dpkg_log"; then
      dpkg_rc=0
    fi
    rm -f "$dpkg_log"
    if [ "$dpkg_rc" -ne 0 ]; then
      printf 'dpkg removal failed with exit code %s.\n' "$dpkg_rc" >&2
      exit "$dpkg_rc"
    fi
  else
    if ! timeout --signal=TERM --kill-after=2s "${SUDO_TIMEOUT}s" sudo -n dpkg -r kylin-memory-bench; then
      printf '%s\n' 'non-interactive sudo is unavailable; run as root or authenticate with sudo before retrying.' >&2
      exit 1
  fi
  cleanup_generated_bytecode
fi
else
  printf '%s\n' 'kylin-memory-bench is not installed.'
fi
if [ "$installed" -eq 1 ]; then
  deadline=$((SECONDS + PACKAGE_WAIT))
  while [ "$SECONDS" -lt "$deadline" ]; do
    if ! package_is_installed && ! payload_is_present; then
      break
    fi
    sleep 1
  done
fi
if package_is_installed; then
  printf '%s\n' 'package remains installed after removal.' >&2
  exit 1
fi
if [ -e /usr/bin/kmb ] || { [ -n "$kare_upper" ] && [ -e "$kare_upper/usr/bin/kmb" ]; } || { [ -n "$kare_pid" ] && nsenter -t "$kare_pid" -m -- test -e /usr/bin/kmb; }; then
  printf '%s\n' 'kmb command remains on PATH after removal.' >&2
  exit 1
fi
if [ -e /usr/share/kylin-memory-bench ] || { [ -n "$kare_upper" ] && [ -e "$kare_upper/usr/share/kylin-memory-bench" ]; } || { [ -n "$kare_pid" ] && nsenter -t "$kare_pid" -m -- test -e /usr/share/kylin-memory-bench; }; then
  printf '%s\n' 'package payload remains after removal: /usr/share/kylin-memory-bench' >&2
  exit 1
fi
printf '%s\n' 'package removal verified; user-selected result directories are intentionally retained.'
