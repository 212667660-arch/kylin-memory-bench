"""OpenClaw CLI adapter with USER.md/MEMORY.md and SQLite deltas."""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import BenchmarkCase, EvidenceEvent
from .base import AgentCommandError, case_keys, extract_text, invoke_command, memory_events_from_diff, preflight_command, process_event, recall_from_snapshot
from .sqlite_memory import SQLiteMemorySnapshot, TextMemorySnapshot, diff_snapshots


class OpenClawAdapter:
    name = "openclaw"

    def __init__(self, home: Optional[Path] = None, timeout: float = 180.0):
        self.home = Path(home or os.environ.get("KMB_AGENT_HOME") or Path.home()).expanduser()
        self.sqlite_path = self.home / ".openclaw/agents/main/agent/openclaw-agent.sqlite"
        self.memory_paths = [self.home / ".openclaw/workspace/USER.md", self.home / ".openclaw/workspace/MEMORY.md"]
        self.timeout = float(timeout)
        self.session_prefix = uuid.uuid4().hex[:12]

    def describe(self) -> Dict[str, Any]:
        return {
            "adapter": type(self).__name__,
            "agent": self.name,
            "memory_observability": "agent_memory_files_and_index",
            "evidence_mode": "agent_memory_observed",
            "memory_paths": [str(self.sqlite_path)] + [str(path) for path in self.memory_paths],
            "native_memory_capability": "not_claimed",
        }

    def preflight(self) -> Dict[str, Any]:
        checks = [
            {
                "name": "memory_store",
                "status": "ready" if any(path.is_file() for path in self.memory_paths + [self.sqlite_path]) else "blocked",
                "paths": [str(path) for path in self.memory_paths + [self.sqlite_path]],
                "reason": "workspace or index available" if any(path.is_file() for path in self.memory_paths + [self.sqlite_path]) else "OpenClaw workspace or index not found",
            },
            preflight_command(["openclaw"], "OpenClaw"),
        ]
        blocked = next((item for item in checks if item["status"] != "ready"), None)
        return {
            "agent": self.name,
            "status": "blocked" if blocked else "ready",
            "checks": checks,
            "reason": blocked.get("reason") if blocked else "read-only preflight passed",
        }

    def _snapshot(self) -> Dict[str, Dict[str, Any]]:
        snapshot = TextMemorySnapshot(self.memory_paths).snapshot()
        if self.sqlite_path.is_file():
            snapshot.update(SQLiteMemorySnapshot(self.sqlite_path, tables=("transcript_events", "memory_index_chunk_recall_metadata")).snapshot())
        return snapshot

    def run(self, case: BenchmarkCase) -> List[EvidenceEvent]:
        if not any(path.is_file() for path in self.memory_paths) and not self.sqlite_path.is_file():
            raise FileNotFoundError("OpenClaw workspace or index not found under %s" % (self.home / ".openclaw"))
        keys = case_keys(case)
        events: List[EvidenceEvent] = []
        for step, turn in enumerate(case.turns, 1):
            user = str(turn.get("user") or "")
            events.append(EvidenceEvent("user_message", {"text": user}, step, source="runner"))
            before = self._snapshot()
            command = ["openclaw", "agent"]
            if os.environ.get("KMB_OPENCLAW_LOCAL") == "1":
                command.append("--local")
            command.extend([
                "--session-key", "kmb-%s-%s" % (self.session_prefix, case.id),
                "-m", user, "--json",
            ])
            env = os.environ.copy()
            env["HOME"] = str(self.home)
            raw = invoke_command(command, self.timeout, env=env)
            answer = extract_text(raw)
            if not answer.strip():
                raise AgentCommandError("OpenClaw response has no observable assistant payload", category="not_observable")
            after = self._snapshot()
            events.extend(memory_events_from_diff(diff_snapshots(before, after), step, keys))
            query = turn.get("query") or {}
            if query.get("key"):
                events.append(recall_from_snapshot(after, str(query["key"]), step))
            events.append(process_event("assistant_message", {
                "text": answer,
                "source_note": "OpenClaw CLI JSON stdout observed after current turn",
            }, step))
        return events
