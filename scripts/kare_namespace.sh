#!/usr/bin/env bash
set -eu

# KARE exposes installed payloads through the mount namespace used by the
# SSH/session container.  Root lifecycle commands may run in the host
# namespace, so locate a session namespace only when it can actually see kmb.
kmb_namespace_pid() {
  command -v nsenter >/dev/null 2>&1 || return 1
  command -v pgrep >/dev/null 2>&1 || return 1

  for pid in $(pgrep -f '/usr/sbin/sshd|sshd:' 2>/dev/null || true) $(pgrep -x tini 2>/dev/null || true); do
    [ -r "/proc/$pid/ns/mnt" ] || continue
    if timeout --signal=TERM --kill-after=1s 5s \
      nsenter -t "$pid" -m -- /bin/sh -c 'test -x /usr/bin/kmb' 2>/dev/null; then
      printf '%s\n' "$pid"
      return 0
    fi
  done
  return 1
}

kmb_upper_root() {
  for root in /opt/kare-applications/shadow/upper /opt/kare/shadow/upper; do
    if [ -f "$root/usr/bin/kmb" ] || [ -d "$root/usr/share/kylin-memory-bench" ]; then
      printf '%s\n' "$root"
      return 0
    fi
  done
  return 1
}

kmb_namespace_exec() {
  if [ "$#" -eq 0 ]; then
    printf '%s\n' 'usage: kare_namespace.sh --exec COMMAND [ARGS...]' >&2
    return 2
  fi
  local pid
  pid="$(kmb_namespace_pid || true)"
  if [ -n "$pid" ]; then
    exec nsenter -t "$pid" -m -- "$@"
  fi
  printf '%s\n' 'KARE session mount namespace with /usr/bin/kmb was not found.' >&2
  return 1
}

case "${1:-}" in
  --find)
    kmb_namespace_pid
    ;;
  --upper)
    kmb_upper_root
    ;;
  --exec)
    shift
    kmb_namespace_exec "$@"
    ;;
  *)
    printf '%s\n' "usage: $0 --find | --upper | --exec COMMAND [ARGS...]" >&2
    exit 2
    ;;
esac
