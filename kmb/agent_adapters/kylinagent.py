"""KylinAgent adapter with an explicit GUI-only limitation."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import BenchmarkCase, EvidenceEvent


class KylinAgentAdapter:
    name = "kylinagent"

    def __init__(self, home: Optional[Path] = None):
        self.home = Path(home or os.environ.get("KMB_AGENT_HOME") or Path.home()).expanduser()
        self.state_path = self.home / ".kylin-agent-runtime/state.db"
        self.memory_path = self.home / ".kylin-agent-runtime/memory.db"

    def describe(self) -> Dict[str, Any]:
        return {
            "adapter": type(self).__name__,
            "agent": self.name,
            "memory_observability": "gui_or_service_only",
            "evidence_mode": "gui_observed",
            "memory_paths": [str(self.state_path), str(self.memory_path)],
            "native_memory_capability": "not_claimed",
        }

    def preflight(self) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "status": "blocked",
            "checks": [{
                "name": "structured_evidence",
                "status": "blocked",
                "reason": "GUI evidence is not a structured memory/action source",
            }],
            "reason": "GUI evidence is not a structured memory/action source",
        }

    def run(self, case: BenchmarkCase) -> List[EvidenceEvent]:
        del case
        raise RuntimeError(
            "KylinAgent is installed, but no structured conversation API is configured; "
            "GUI evidence cannot be converted into memory events automatically"
        )
