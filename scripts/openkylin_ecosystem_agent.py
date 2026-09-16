#!/usr/bin/env python3
"""openKylin ecosystem process agent (local stand-in for KylinBot / kylin-agent).

Contract: CommandAgent protocol — stdin one BenchmarkCase JSON,
stdout one EvidenceEvent JSON per line.

This is a real subprocess adapter (not an in-process deterministic class).
On openKylin the same command can point at a native agent binary/wrapper
that emits the same JSONL evidence protocol.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def emit(kind: str, data: Dict[str, Any], step: int, source: str = "process") -> None:
    payload = {
        "case_id": CASE_ID,
        "kind": kind,
        "data": data,
        "step": step,
        "timestamp": utc_now(),
        "source": source,
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        print("empty case on stdin", file=sys.stderr)
        return 2
    case = json.loads(raw)
    global CASE_ID
    CASE_ID = str(case.get("id") or case.get("case_id") or "")
    memory: Dict[str, Any] = {}
    turns = case.get("turns") or []
    for step, turn in enumerate(turns, 1):
        user = str(turn.get("user", ""))
        emit("user_message", {"text": user}, step)
        mem = turn.get("memory")
        if mem is None and user.lower().startswith("remember ") and "=" in user:
            key, value = user[9:].split("=", 1)
            mem = {"op": "write", "key": key.strip(), "value": value.strip(), "persist": True}
        if mem:
            op = str(mem.get("op", "write"))
            key = str(mem.get("key"))
            value = mem.get("value")
            persist = bool(mem.get("persist", True))
            if op in ("write", "update") and persist:
                old = memory.get(key)
                memory[key] = value
                kind = "memory_update" if op == "update" and old is not None else "memory_write"
                emit(kind, {"key": key, "value": value, "old_value": old, "persist": True}, step)
            else:
                emit("memory_suppress", {"key": key, "value": value, "persist": False}, step)
        query = turn.get("query")
        if query:
            key = str(query.get("key"))
            value = memory.get(key)
            emit("memory_recall", {"key": key, "value": value, "hit": value is not None}, step)
            text = "I don't know." if value is None else str(value)
            emit("assistant_message", {"text": text}, step)
        action = turn.get("action")
        if action:
            tool = str(action.get("tool", "action"))
            path = action.get("path")
            source_key = action.get("path_from_memory")
            if source_key:
                path = memory.get(str(source_key))
            emit("action", {"tool": tool, "path": path, "source_key": source_key}, step)
            emit("assistant_message", {"text": "action completed" if path else "action failed"}, step)
    return 0


CASE_ID = ""

if __name__ == "__main__":
    raise SystemExit(main())
