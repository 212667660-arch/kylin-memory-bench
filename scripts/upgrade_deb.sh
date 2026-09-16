#!/usr/bin/env bash
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
bash "$SCRIPT_DIR/install_deb.sh" "$@"
