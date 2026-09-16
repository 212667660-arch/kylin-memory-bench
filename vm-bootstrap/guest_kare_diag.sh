#!/bin/sh
{
  echo '=== kare files ==='
  ls -l /usr/bin/kare /opt/kare/usr/bin/sshd /opt/kare/usr/bin/ssh-keygen /opt/kare/usr/sbin/ssh-keygen 2>&1 || true
  echo '=== kare type ==='
  file /usr/bin/kare 2>&1 || true
  echo '=== kare help ==='
  /usr/bin/kare --help 2>&1 || true
  echo '=== kare list ==='
  /usr/bin/kare list 2>&1 || true
  echo '=== ssh package files ==='
  find /opt/kare -type f \( -name sshd -o -name ssh-keygen -o -name ssh-keygen.exe \) -ls 2>&1 || true
} > /tmp/codex_kare_diag.txt 2>&1
