#!/bin/sh
set -u
PUBKEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFFr6SCBClVFetU7WA0sfTDnuIIjhe9nAso7zaZzBkRK codex-openkylin-vm'
PORT=2222
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
touch "$HOME/.ssh/authorized_keys"
grep -qxF "$PUBKEY" "$HOME/.ssh/authorized_keys" || printf '%s\n' "$PUBKEY" >> "$HOME/.ssh/authorized_keys"
chmod 600 "$HOME/.ssh/authorized_keys"
HOSTKEY="$HOME/.ssh/ssh_host_ed25519_key"
CONFIG="$HOME/.ssh/sshd_config_vm"
LOG="$HOME/.ssh/sshd_vm_${PORT}.log"
PIDFILE="$HOME/.ssh/sshd_vm_${PORT}.pid"
if [ ! -f "$HOSTKEY" ]; then
  /opt/kare/usr/bin/ssh-keygen -t ed25519 -f "$HOSTKEY" -N '' -q 2>/dev/null || ssh-keygen -t ed25519 -f "$HOSTKEY" -N '' -q 2>/dev/null || true
fi
cat > "$CONFIG" <<EOF
Port ${PORT}
ListenAddress 0.0.0.0
HostKey ${HOSTKEY}
PidFile ${PIDFILE}
AuthorizedKeysFile %h/.ssh/authorized_keys
PasswordAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication no
UsePAM no
PermitRootLogin no
AllowUsers $(whoami)
Subsystem sftp internal-sftp
EOF
{
  echo "config=$CONFIG"
  echo "hostkey=$HOSTKEY"
  echo '=== config test ==='
  /opt/kare/usr/sbin/sshd -t -f "$CONFIG"
  echo "config_test_exit=$?"
  echo '=== start ==='
  if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo 'already running'
  else
    /opt/kare/usr/sbin/sshd -f "$CONFIG" -E "$LOG"
    echo "start_exit=$?"
  fi
  sleep 1
  echo '=== process ==='
  ps aux | grep '[s]shd' || true
  echo '=== ports ==='
  ss -lntp || true
  echo '=== log ==='
  cat "$LOG" 2>&1 || true
} > /tmp/codex_start_user_ssh.txt 2>&1
