#!/usr/bin/env python3
"""CommandAgent wrapper: KylinBot evidence export on stdin case / stdout JSONL.

Real Agent-owned memory comes from brain.db only.
Not the stand-in scripts/openkylin_ecosystem_agent.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

# allow running from repo root without install
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.export_kylinbot_evidence import run_command_stdin  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run_command_stdin())
