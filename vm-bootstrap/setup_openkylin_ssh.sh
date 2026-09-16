#!/usr/bin/env bash
set -euo pipefail

PUBKEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFFr6SCBClVFetU7WA0sfTDnuIIjhe9nAso7zaZzBkRK codex-openkylin-vm'
USER_SSH_PORT="${KMB_USER_SSH_PORT:-2222}"

say() {
  printf '[openkylin-ssh] %s\n' "$*"
}

ensure_authorized_key() {
  mkdir -p "$HOME/.ssh"
  chmod 700 "$HOME/.ssh"
  touch "$HOME/.ssh/authorized_keys"
  if ! grep -qxF "$PUBKEY" "$HOME/.ssh/authorized_keys"; then
    printf '%s\n' "$PUBKEY" >> "$HOME/.ssh/authorized_keys"
  fi
  chmod 600 "$HOME/.ssh/authorized_keys"
  say "authorized_keys is ready for user: $(whoami)"
}

find_sshd() {
  if command -v sshd >/dev/null 2>&1; then
    command -v sshd
  elif [ -x /usr/sbin/sshd ]; then
    printf '%s\n' /usr/sbin/sshd
  elif [ -x /usr/local/sbin/sshd ]; then
    printf '%s\n' /usr/local/sbin/sshd
  elif [ -x /opt/kare/usr/sbin/sshd ]; then
    # openKylin KARE keeps application binaries in its compatibility layer.
    printf '%s\n' /opt/kare/usr/sbin/sshd
  else
    return 1
  fi
}

install_openssh_server_if_missing() {
  if find_sshd >/dev/null 2>&1; then
    return 0
  fi

  say "openssh-server is missing; installing with sudo."
  say "If sudo asks for a password, enter your openKylin login password."
  sudo apt update
  sudo apt install -y openssh-server
}

start_system_ssh() {
  if ! command -v systemctl >/dev/null 2>&1; then
    return 1
  fi

  say "enabling system SSH service with sudo."
  if sudo systemctl enable --now ssh; then
    say "system SSH service started on port 22."
    return 0
  fi

  if sudo systemctl enable --now sshd; then
    say "system SSH service started on port 22."
    return 0
  fi

  return 1
}

start_user_ssh() {
  local sshd_path config host_key pidfile logfile

  sshd_path="$(find_sshd)"
  config="$HOME/.ssh/sshd_config_vm"
  host_key="$HOME/.ssh/ssh_host_ed25519_key"
  pidfile="$HOME/.ssh/sshd_vm_${USER_SSH_PORT}.pid"
  logfile="$HOME/.ssh/sshd_vm_${USER_SSH_PORT}.log"

  if [ ! -f "$host_key" ]; then
    if command -v ssh-keygen >/dev/null 2>&1; then
      ssh-keygen -t ed25519 -f "$host_key" -N '' -q
    elif command -v kare >/dev/null 2>&1; then
      kare run openssh-server /usr/bin/ssh-keygen -t ed25519 -f "$host_key" -N '' -q
    else
      # The KARE sshd wrapper runs the real openssh tools in its layer.
      return 1
    fi
  fi

  cat > "$config" <<EOF
Port ${USER_SSH_PORT}
ListenAddress 0.0.0.0
HostKey ${host_key}
PidFile ${pidfile}
AuthorizedKeysFile %h/.ssh/authorized_keys
PasswordAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication no
UsePAM no
PermitRootLogin no
AllowUsers $(whoami)
Subsystem sftp internal-sftp
EOF

  if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    say "user SSH service is already running on port ${USER_SSH_PORT}."
    return 0
  fi

  "$sshd_path" -f "$config" -E "$logfile"
  say "user SSH service started on port ${USER_SSH_PORT}."
}

install_user_autostart() {
  local autostart_dir desktop_file
  autostart_dir="$HOME/.config/autostart"
  desktop_file="$autostart_dir/openkylin-user-ssh.desktop"
  mkdir -p "$autostart_dir"
  cat > "$desktop_file" <<EOF
[Desktop Entry]
Type=Application
Name=openKylin SSH (VM)
Exec=$HOME/.local/bin/openkylin-user-ssh-start
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
  mkdir -p "$HOME/.local/bin"
  cat > "$HOME/.local/bin/openkylin-user-ssh-start" <<'EOF'
#!/bin/sh
set -u
PORT="${KMB_USER_SSH_PORT:-2222}"
HOSTKEY="$HOME/.ssh/ssh_host_ed25519_key"
CONFIG="$HOME/.ssh/sshd_config_vm"
LOG="$HOME/.ssh/sshd_vm_${PORT}.log"
PIDFILE="$HOME/.ssh/sshd_vm_${PORT}.pid"
if [ ! -f "$HOSTKEY" ]; then
  if command -v ssh-keygen >/dev/null 2>&1; then
    ssh-keygen -t ed25519 -f "$HOSTKEY" -N '' -q
  else
    exit 1
  fi
fi
if [ ! -f "$CONFIG" ]; then
  cat > "$CONFIG" <<CFG
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
AllowUsers $(id -un)
Subsystem sftp internal-sftp
CFG
fi
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  exit 0
fi
exec /opt/kare/usr/sbin/sshd -f "$CONFIG" -E "$LOG"
EOF
  chmod 700 "$HOME/.local/bin/openkylin-user-ssh-start"
  say "user SSH autostart configured for graphical login."
}

print_result() {
  local ip user
  user="$(whoami)"
  ip="$(hostname -I 2>/dev/null | awk '{print $1}')"

  say "guest user: ${user}"
  say "guest ip: ${ip:-unknown}"
  say "Windows test command for system SSH:"
  printf 'ssh -i "$env:USERPROFILE\\.ssh\\openkylin_vm_ed25519" -o IdentitiesOnly=yes %s@%s\n' "$user" "${ip:-192.168.182.129}"
  say "If port 22 is not open but port ${USER_SSH_PORT} is open, use:"
  printf 'ssh -p %s -i "$env:USERPROFILE\\.ssh\\openkylin_vm_ed25519" -o IdentitiesOnly=yes %s@%s\n' "$USER_SSH_PORT" "$user" "${ip:-192.168.182.129}"
}

main() {
  if [ "${1:-}" = '--start-user-ssh' ]; then
    start_user_ssh
    exit $?
  fi
  ensure_authorized_key
  install_openssh_server_if_missing

  if ! start_system_ssh; then
    say "system SSH did not start; falling back to user-level SSH."
    start_user_ssh
    install_user_autostart
  fi

  print_result
}

main "$@"
