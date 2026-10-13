"""Real KylinBot CLI adapter backed by the Agent's brain.db."""
from __future__ import annotations

import os
import shlex
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.kylinbot_command_agent import run_case

from ..models import BenchmarkCase, EvidenceEvent
from .base import preflight_command
from ..agent_registry import resolve_agent_executable


class KylinBotAdapter:
    name = "kylinbot"

    def __init__(self, db_path: Optional[Path] = None, timeout: float = 120.0, home: Optional[Path] = None):
        self.home = Path(home or os.environ.get("KMB_AGENT_HOME") or Path.home()).expanduser()
        self.db_path = Path(db_path or self.home / ".kylinbot/workspace/memory/brain.db").expanduser()
        self.timeout = float(timeout)

    def describe(self) -> Dict[str, Any]:
        return {
            "adapter": type(self).__name__,
            "agent": self.name,
            "memory_observability": "agent_storage_delta",
            "evidence_mode": "agent_memory_observed",
            "memory_paths": [str(self.db_path)],
            "native_memory_capability": "not_claimed",
        }

    def preflight(self) -> Dict[str, Any]:
        command = self._command()
        checks = [
            {
                "name": "memory_store",
                "status": "ready" if self.db_path.is_file() else "blocked",
                "path": str(self.db_path),
                "reason": "brain.db available" if self.db_path.is_file() else "KylinBot brain.db not found",
            },
            preflight_command(command, "KylinBot"),
        ]
        blocked = next((item for item in checks if item["status"] != "ready"), None)
        return {
            "agent": self.name,
            "status": "blocked" if blocked else "ready",
            "checks": checks,
            "reason": blocked.get("reason") if blocked else "read-only preflight passed",
        }

    def _command(self) -> List[str]:
        command = shlex.split(os.environ.get("KYLINBOT_COMMAND", "kylin-bot"))
        if command:
            command[0] = resolve_agent_executable(command[0], self.home) or command[0]
        return command

    def run(self, case: BenchmarkCase) -> List[EvidenceEvent]:
        raw_events = run_case(asdict(case), command=self._command(), db_path=self.db_path, timeout=self.timeout, home=self.home)
        events: List[EvidenceEvent] = []
        for raw in raw_events:
            events.append(EvidenceEvent(
                kind=str(raw["kind"]),
                data=dict(raw.get("data") or {}),
                step=int(raw.get("step", 0)),
                timestamp=str(raw.get("timestamp") or ""),
                source=str(raw.get("source") or raw.get("data", {}).get("source") or "process"),
                evidence_class=str(raw.get("evidence_class") or raw.get("data", {}).get("evidence_class") or ""),
            ))
        return events
