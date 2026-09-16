#!/usr/bin/env bash
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
VENV_DIR="$ROOT/.kmb-venv"
case "$VENV_DIR" in
  "$ROOT/.kmb-venv") ;;
  *) printf 'refusing to remove path outside the managed project venv: %s\n' "$VENV_DIR" >&2; exit 2 ;;
esac
if [ -d "$VENV_DIR" ]; then
  rm -rf -- "$VENV_DIR"
  printf 'removed environment: %s\n' "$VENV_DIR"
else
  printf 'environment not present: %s\n' "$VENV_DIR"
fi
