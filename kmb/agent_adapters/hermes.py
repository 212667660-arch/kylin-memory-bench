"""Hermes process adapter with conservative state.db memory-event parsing."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import BenchmarkCase, EvidenceEvent
from .base import (
    AgentCommandError,
    case_keys,
    classify_error,
    configured_command,
    extract_text,
    invoke_command,
    memory_events_from_diff,
    preflight_command,
    process_event,
    recall_from_snapshot,
)
from .sqlite_memory import SQLiteMemorySnapshot, diff_snapshots


class HermesAdapter:
    name = "hermes"

    def __init__(self, state_path: Optional[Path] = None, timeout: float = 180.0, home: Optional[Path] = None):
        home = Path(home or os.environ.get("KMB_AGENT_HOME") or Path.home()).expanduser()
        self.home = home
        self.state_path = Path(state_path or home / ".hermes/state.db").expanduser()
        self.timeout = float(timeout)

    def describe(self) -> Dict[str, Any]:
        return {
            "adapter": type(self).__name__,
            "agent": self.name,
            "memory_observability": "agent_messages_memory_events",
            "evidence_mode": "agent_memory_observed",
            "memory_paths": [str(self.state_path)],
            "native_memory_capability": "not_claimed",
        }

    def _command(self) -> List[str]:
        home = self.home
        default_executable = home / ".kylin-agent-runtime/agent-runtime/venv/bin/hermes"
        if not default_executable.is_file():
            default_executable = Path("hermes")
        return configured_command(
            "HERMES_COMMAND",
            str(default_executable),
            ("chat", "--quiet", "--source", "tool", "--query"),
        )

    def preflight(self) -> Dict[str, Any]:
        checks = [
            {
                "name": "memory_store",
                "status": "ready" if self.state_path.is_file() else "blocked",
                "path": str(self.state_path),
                "reason": "state.db available" if self.state_path.is_file() else "Hermes state.db not found",
            },
            preflight_command(self._command(), "Hermes"),
        ]
        blocked = next((item for item in checks if item["status"] != "ready"), None)
        return {
            "agent": self.name,
            "status": "blocked" if blocked else "ready",
            "checks": checks,
            "reason": blocked.get("reason") if blocked else "read-only preflight passed",
        }

    def _memory_changes(self, before: Dict[str, Dict[str, Any]], after: Dict[str, Dict[str, Any]], step: int, keys: List[str]) -> List[EvidenceEvent]:
        changes = diff_snapshots(before, after)
        marked = [
            change for change in changes
            if re.search(r"memory|remember|recall|记住|记忆", str(change.get("content", "")), re.I)
        ]
        return memory_events_from_diff(marked, step, keys)

    @staticmethod
    def _check_provider_output(raw: str) -> None:
        """Catch Hermes provider failures that are printed with exit code 0."""
        text = str(raw or "")
        explicit_failure = re.search(
            r"(?:api call failed|all models failed).*?(?:http\s+[45]\d\d|billing|quota|balance|credential|余额)",
            text,
            re.I | re.S,
        )
        if not explicit_failure:
            return
        raise AgentCommandError(
            "Hermes provider call failed: %s" % text[-8192:].strip(),
            category=classify_error(RuntimeError(text)),
            returncode=0,
            stdout_tail=text[-8192:],
        )

    def run(self, case: BenchmarkCase) -> List[EvidenceEvent]:
        if not self.state_path.is_file():
            raise FileNotFoundError("Hermes state.db not found: %s" % self.state_path)
        store = SQLiteMemorySnapshot(self.state_path, tables=("messages",))
        keys = case_keys(case)
        events: List[EvidenceEvent] = []
        for step, turn in enumerate(case.turns, 1):
            user = str(turn.get("user") or "")
            events.append(EvidenceEvent("user_message", {"text": user}, step, source="runner"))
            before = store.snapshot()
            command = self._command() + [user]
            env = os.environ.copy()
            env["HOME"] = str(self.home)
            env["KMB_AGENT_HOME"] = str(self.home)
            raw = invoke_command(command, self.timeout, env=env)
            self._check_provider_output(raw)
            answer = extract_text(raw)
            after = store.snapshot()
            events.extend(self._memory_changes(before, after, step, keys))
            query = turn.get("query") or {}
            if query.get("key"):
                events.append(recall_from_snapshot(after, str(query["key"]), step))
            events.append(process_event("assistant_message", {
                "text": answer,
                "source_note": "Hermes CLI stdout observed after current turn",
            }, step))
        return events
