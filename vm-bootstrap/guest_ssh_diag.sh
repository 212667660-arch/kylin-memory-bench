#!/bin/sh
{
  echo "=== PATH ==="
  printf '%s\n' "$PATH"
  echo "=== SSH BINARIES ==="
  for f in /opt/kare/usr/sbin/sshd /opt/kare/lib/systemd/system/ssh.service.bin /usr/sbin/sshd /etc/ssh/sshd_config /etc/default/ssh; do
    echo "--- $f"
    ls -l "$f" 2>&1
    if [ -f "$f" ]; then sed -n '1,160p' "$f"; fi
  done
  echo "=== PACKAGE STATE ==="
  dpkg -s openssh-server 2>&1 || true
  echo "=== SERVICE ==="
  systemctl is-enabled ssh 2>&1 || true
  systemctl is-active ssh 2>&1 || true
  systemctl status ssh --no-pager -l 2>&1 || true
  echo "=== PORTS ==="
  ss -lntp 2>&1 || true
} > /tmp/codex_vm_ssh_diag2.txt 2>&1
