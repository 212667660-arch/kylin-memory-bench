#!/usr/bin/env python3
"""Export KylinBot brain.db.memories to kmb_evidence JSONL.

Read-only translation of Agent-owned memory rows. Does NOT invent
memory_write/update/suppress from suite checks.

Typical DB path (guest): ~/.kylinbot/workspace/memory/brain.db
Override: --db or env KYLINBOT_BRAIN_DB
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

SENSITIVE = re.compile(r"(otp|token|password|secret|api[_-]?key|一次性|验证码|密码|口令)", re.I)

SOURCE = "process"  # agent-owned observable; NOT model_native_memory


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact_value(value: str) -> str:
    text = str(value) if value is not None else ""
    if SENSITIVE.search(text):
        digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:12]
        return "[redacted sha256:%s len=%d]" % (digest, len(text))
    return text[:240]


def default_db_path() -> Path:
    env = os.environ.get("KYLINBOT_BRAIN_DB")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".kylinbot" / "workspace" / "memory" / "brain.db"


def load_memories(db_path: Path) -> list:
    if not db_path.is_file():
        raise FileNotFoundError("KylinBot brain.db not found: %s" % db_path)
    conn = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, key, content, category, created_at, updated_at "
            "FROM memories ORDER BY COALESCE(created_at, updated_at), key"
        )
        rows = cur.fetchall()
    finally:
        conn.close()
    return rows


def event(case_id: str, kind: str, data: dict, step: int) -> dict:
    payload = {
        "case_id": case_id,
        "kind": kind,
        "data": data,
        "step": step,
        "timestamp": utc_now(),
        "source": SOURCE,
        "evidence_class": "wrapper_operation" if kind.startswith("memory") or kind == "action" else "wrapper_observation",
    }
    return payload


def export_case(case: dict, memories: list, include_all_keys: bool = False) -> list:
    """Translate DB rows + case user/query turns into JSONL events.

    This command is a read-only database snapshot exporter. It does not drive
    KylinBot and therefore must not claim that a memory was written during the
    current case. Only exact keys queried by the case are exposed as observed
    recalls; unrelated historical rows are excluded to prevent cross-case
    contamination.
    """
    case_id = str(case.get("id") or case.get("case_id") or "unknown")
    events = []
    step = 0
    db_by_key = {}
    for row in memories:
        # id, key, content, category, created_at, updated_at
        key = row[1]
        db_by_key[key] = row

    for turn in case.get("turns") or []:
        user = str(turn.get("user") or "")
        step += 1
        events.append(event(case_id, "user_message", {"text": user}, step, ))
        # mark as runner-known input text, not agent memory
        events[-1]["source"] = "runner"

    # Observed recall only for exact case query keys. A snapshot cannot prove
    # when a row was written, so it never emits memory_write/memory_update.
    db_by_key = {row[1]: row for row in memories}
    step = 200
    for turn in case.get("turns") or []:
        query = turn.get("query")
        if not query:
            # try parse "What is X" style
            user = str(turn.get("user") or "")
            m = re.search(r"(?:what\s+is|which|recall)\s+(?:my\s+)?([A-Za-z0-9_.-]+)", user, re.I)
            if not m:
                continue
            key = m.group(1)
        else:
            key = str(query.get("key") or "")
        if not key:
            continue
        step += 1
        hit = key in db_by_key
        value = redact_value(db_by_key[key][2]) if hit else None
        events.append(event(case_id, "memory_recall", {
            "key": key,
            "value": value,
            "hit": hit,
            "state_observed": True,
            "agent_owned": True,
            "snapshot_only": True,
            "source_note": "snapshot observation from brain.db; no current-case write timing",
        }, step))

    return events


def run_command_stdin() -> int:
    """CommandAgent protocol: stdin case JSON → stdout JSONL."""
    raw = sys.stdin.read()
    if not raw.strip():
        print("empty case on stdin", file=sys.stderr)
        return 2
    case = json.loads(raw)
    db = default_db_path()
    try:
        memories = load_memories(db)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        # still emit user_message so runner records empty agent memory honestly
        memories = []
    events = export_case(case, memories)
    for e in events:
        sys.stdout.write(json.dumps(e, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Export KylinBot brain.db.memories to kmb_evidence JSONL")
    parser.add_argument("--db", default="", help="path to brain.db (default: KYLINBOT_BRAIN_DB or ~/.kylinbot/workspace/memory/brain.db)")
    parser.add_argument("--case", default="", help="optional case JSON file; if set, write JSONL to stdout for that case")
    parser.add_argument("--case-id", default="kylinbot-export", help="case_id when not reading case file")
    parser.add_argument("--out", default="", help="write JSONL to this file instead of stdout")
    args = parser.parse_args(argv)

    if args.db:
        os.environ["KYLINBOT_BRAIN_DB"] = args.db
    if args.case:
        # CLI file mode still useful for manual gate dumps
        case = json.loads(Path(args.case).read_text(encoding="utf-8"))
        memories = load_memories(default_db_path())
        events = export_case(case, memories)
        text = "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
            print("wrote %s events=%d" % (args.out, len(events)), file=sys.stderr)
        else:
            sys.stdout.write(text)
        return 0

    # no --case: emit a redacted snapshot action rather than inventing writes.
    memories = load_memories(default_db_path())
    case = {"id": args.case_id, "turns": []}
    events = export_case(case, [])
    for index, (_id, key, content, category, created_at, updated_at) in enumerate(memories, 1):
        events.append(event(args.case_id, "action", {
            "tool": "memory_snapshot",
            "key": key,
            "value": redact_value(content),
            "category": category,
            "created_at": created_at,
            "updated_at": updated_at,
            "row_id": _id,
            "state_observed": True,
            "agent_owned": True,
            "snapshot_only": True,
        }, 100 + index))
    text = "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print("wrote %s events=%d" % (args.out, len(events)), file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_command_stdin() if not any(a.startswith("--") for a in sys.argv[1:]) else main())
