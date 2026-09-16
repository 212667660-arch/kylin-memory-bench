#!/usr/bin/env bash
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
export TMPDIR="${TMPDIR:-$ROOT/.tmp-pip}"
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-$ROOT/.pip-cache}"
mkdir -p "$TMPDIR" "$PIP_CACHE_DIR"
PYTHON_BIN=python3
if [ "$#" -ge 1 ]; then
  PYTHON_BIN="$1"
elif ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  PYTHON_BIN=python
fi
VENV_DIR="$ROOT/.kmb-venv"

if ! "$PYTHON_BIN" -m venv --system-site-packages "$VENV_DIR"; then
  # Some minimal openKylin images ship venv without ensurepip. Keep the
  # environment isolated, then bootstrap pip from the official PyPA endpoint.
  rm -rf -- "$VENV_DIR"
  "$PYTHON_BIN" -m venv --system-site-packages --without-pip "$VENV_DIR"
fi
VENV_PYTHON="$VENV_DIR/bin/python"
if [ ! -x "$VENV_PYTHON" ]; then
  printf 'virtualenv Python not found at %s\n' "$VENV_PYTHON" >&2
  exit 2
fi

if ! "$VENV_PYTHON" -m pip --version >/dev/null 2>&1; then
  BOOTSTRAP_URL="${KMB_PIP_BOOTSTRAP_URL:-https://bootstrap.pypa.io/get-pip.py}"
  BOOTSTRAP_SCRIPT="$TMPDIR/get-pip.py"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$BOOTSTRAP_URL" -o "$BOOTSTRAP_SCRIPT"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$BOOTSTRAP_SCRIPT" "$BOOTSTRAP_URL"
  else
    printf 'pip is unavailable and neither curl nor wget can fetch %s\n' "$BOOTSTRAP_URL" >&2
    exit 2
  fi
  "$VENV_PYTHON" "$BOOTSTRAP_SCRIPT" --disable-pip-version-check --no-warn-script-location
fi

# KMB_OFFLINE_WHEELHOUSE enables a fully offline dependency install when the
# wheelhouse was prepared for the target openKylin architecture in advance.
if ! "$VENV_PYTHON" -c 'import yaml' >/dev/null 2>&1; then
  if [ -n "${KMB_OFFLINE_WHEELHOUSE:-}" ]; then
    if [ ! -d "$KMB_OFFLINE_WHEELHOUSE" ]; then
      printf 'offline wheelhouse does not exist: %s\n' "$KMB_OFFLINE_WHEELHOUSE" >&2
      exit 2
    fi
    "$VENV_PYTHON" -m pip install --no-index --find-links "$KMB_OFFLINE_WHEELHOUSE" "PyYAML>=6.0"
  else
    "$VENV_PYTHON" -m pip install "PyYAML>=6.0"
  fi
fi

if ! "$VENV_PYTHON" -c 'import setuptools' >/dev/null 2>&1; then
  "$VENV_PYTHON" -m pip install "setuptools>=61"
fi

# Prefer the modern package build, then fall back to legacy setuptools for old openKylin images.
if ! "$VENV_PYTHON" -m pip install --no-deps --no-build-isolation "$ROOT"; then
  "$VENV_PYTHON" "$ROOT/setup.py" install
fi
"$VENV_PYTHON" "$ROOT/scripts/env_probe.py" --json
printf 'installed environment: %s\n' "$VENV_DIR"
