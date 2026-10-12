#!/usr/bin/env python3
"""Drive KylinBot one case at a time and export agent-owned evidence.

Unlike the read-only snapshot exporter, this adapter invokes the guest
``kylin-bot agent`` CLI for every turn, reusing one temporary session state
file. Memory events are limited to brain.db rows that changed after that
turn; pre-existing history is never attributed to the case.
"""
from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.export_kylinbot_evidence import (
    default_db_path,
    event,
    load_memories,
    redact_value,
)


class AgentCommandError(RuntimeError):
    """Structured KylinBot command failure consumed by the benchmark runner."""

    def __init__(self, message: str, *, category: str = "runtime_error", returncode: int | None = None, stdout_tail: str = "", stderr_tail: str = "") -> None:
        self.category = category
        self.returncode = returncode
        self.stdout_tail = stdout_tail
        self.stderr_tail = stderr_tail
        super().__init__(message)


def _tail(value: str, limit: int = 8192) -> str:
    value = str(value or "")
    return value if len(value) <= limit else value[-limit:]


def _classify_command_detail(detail: str) -> str:
    text = str(detail or "").lower()
    if any(token in text for token in ("billing", "quota", "payment", "insufficient credit", "credit balance", "402")):
        return "billing_error"
    if any(token in text for token in ("api key", "apikey", "credential", "unauthorized", "forbidden", "401", "403", "authentication")):
        return "credential_error"
    if any(token in text for token in ("not found", "no such file", "missing", "brain.db")):
        return "missing_input"
    if any(token in text for token in ("unsupported", "not supported", "tool unavailable", "action unavailable")):
        return "unsupported_action"
    return "runtime_error"


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
LOG_LINE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T[^ ]+\s+(?:TRACE|DEBUG|INFO|WARN|ERROR)\b")


def parse_agent_output(raw: str) -> str:
    """Return the response portion after KylinBot's timestamped log lines."""
    text = ANSI_RE.sub("", str(raw or "")).replace("\r\n", "\n")
    lines = text.splitlines()
    log_indexes = [index for index, line in enumerate(lines) if LOG_LINE_RE.match(line.strip())]
    start = max(log_indexes) + 1 if log_indexes else 0
    return "\n".join(lines[start:]).strip()


def _row_dict(row: Iterable[Any]) -> Dict[str, Any]:
    row_id, key, content, category, created_at, updated_at = row
    return {
        "id": row_id,
        "key": key,
        "content": content,
        "category": category,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def memory_map(db_path: Path) -> Dict[str, Dict[str, Any]]:
    return {str(row[0]): _row_dict(row) for row in load_memories(db_path)}


def diff_memory_rows(before: Mapping[str, Mapping[str, Any]], after: Mapping[str, Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Translate only rows created or changed during the current CLI turn."""
    events: List[Dict[str, Any]] = []
    for row_id in sorted(after):
        current = dict(after[row_id])
        previous = dict(before[row_id]) if row_id in before else None
        if previous is not None and current == previous:
            continue
        kind = "memory_write" if previous is None else "memory_update"
        data = {
            "key": current["key"],
            "value": redact_value(current["content"]),
            "old_value": redact_value(previous["content"]) if previous else None,
            "persist": True,
            "category": current["category"],
            "created_at": current["created_at"],
            "updated_at": current["updated_at"],
            "row_id": current["id"],
            "state_observed": True,
            "agent_owned": True,
            "not_model_native": True,
            "current_case": True,
            "source_note": "brain.db row changed after this KylinBot CLI turn",
        }
        events.append({"kind": kind, "data": data})
    return events


def invoke_turn(command: List[str], message: str, session_file: Path, timeout: float, env: Mapping[str, str]) -> str:
    config_dir = env.get("KMB_AGENT_HOME")
    if config_dir and "--config-dir" not in command:
        command = command + ["--config-dir", str(Path(config_dir).expanduser() / ".kylinbot")]
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
    process_env = dict(env)
    process_env["PYTHONIOENCODING"] = "utf-8"
    process = subprocess.Popen(
        command + ["agent", "--message", message, "--session-state-file", str(session_file)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=process_env,
        start_new_session=os.name != "nt",
        creationflags=creationflags,
    )
    try:
        stdout, stderr = process.communicate(timeout=float(timeout))
    except subprocess.TimeoutExpired as exc:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False)
        else:
            process.kill()
        stdout, stderr = process.communicate()
        raise AgentCommandError(
            "KylinBot agent timed out after %.2fs" % float(timeout),
            category="timeout", returncode=process.returncode,
            stdout_tail=_tail(stdout), stderr_tail=_tail(stderr),
        ) from exc
    stdout, stderr = _tail(stdout), _tail(stderr)
    if process.returncode != 0:
        detail = (stderr or stdout).strip()
        raise AgentCommandError(
            "KylinBot agent exited %d: %s" % (process.returncode, detail),
            category=_classify_command_detail(detail),
            returncode=process.returncode,
            stdout_tail=stdout, stderr_tail=stderr,
        )
    return parse_agent_output(stdout)


def run_case(
    case: Mapping[str, Any],
    *,
    command: List[str] | None = None,
    db_path: Path | None = None,
    session_root: Path | None = None,
    timeout: float = 120.0,
    home: Path | None = None,
) -> List[Dict[str, Any]]:
    case_id = str(case.get("id") or case.get("case_id") or "unknown")
    db = Path(db_path or default_db_path()).expanduser()
    if not db.is_file():
        raise FileNotFoundError("KylinBot brain.db not found: %s" % db)
    executable = command or shlex.split(os.environ.get("KYLINBOT_COMMAND", "kylin-bot"))
    env = os.environ.copy()
    env["KYLINBOT_BRAIN_DB"] = str(db)
    isolated_home = str(Path(home).expanduser()) if home else os.environ.get("KMB_AGENT_HOME")
    if isolated_home:
        env["HOME"] = str(Path(isolated_home).expanduser())
        env["KMB_AGENT_HOME"] = str(Path(isolated_home).expanduser())
    root_owned = session_root is None
    session_context = tempfile.TemporaryDirectory(prefix="kmb-kylinbot-") if root_owned else None
    root = Path(session_context.name) if session_context else Path(session_root)
    root.mkdir(parents=True, exist_ok=True)
    session_file = root / "session.json"
    events: List[Dict[str, Any]] = []
    try:
        for step, turn in enumerate(case.get("turns") or [], 1):
            user = str(turn.get("user") or "")
            if not user:
                continue
            events.append(event(case_id, "user_message", {"text": user}, step))
            events[-1]["source"] = "runner"
            before = memory_map(db)
            answer = invoke_turn(executable, user, session_file, timeout, env)
            after = memory_map(db)
            for item in diff_memory_rows(before, after):
                events.append(event(case_id, item["kind"], item["data"], step))
            query = turn.get("query") or {}
            query_key = str(query.get("key") or "").strip()
            if query_key:
                row = next((item for item in after.values() if item["key"] == query_key), None)
                events.append(event(case_id, "memory_recall", {
                    "key": query_key,
                    "value": redact_value(row["content"]) if row else None,
                    "hit": row is not None,
                    "state_observed": True,
                    "agent_owned": True,
                    "not_model_native": True,
                    "current_case": True,
                    "source_note": "exact key lookup in KylinBot brain.db after this CLI turn",
                }, step))
            events.append(event(case_id, "assistant_message", {
                "text": answer,
                "state_observed": True,
                "agent_owned": True,
                "source_note": "stdout response from KylinBot agent CLI",
            }, step))
    finally:
        if session_context is not None:
            session_context.cleanup()
    return events


def run_command_stdin() -> int:
    import json

    raw = sys.stdin.read()
    if not raw.strip():
        print("empty case on stdin", file=sys.stderr)
        return 2
    try:
        case = json.loads(raw)
        events = run_case(case)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    import json as _json
    for item in events:
        sys.stdout.write(_json.dumps(item, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Drive KylinBot and emit kmb_evidence JSONL")
    parser.add_argument("--command", default=os.environ.get("KYLINBOT_COMMAND", "kylin-bot"))
    parser.add_argument("--db", default=os.environ.get("KYLINBOT_BRAIN_DB", ""))
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args(argv)
    if args.db:
        os.environ["KYLINBOT_BRAIN_DB"] = args.db
    return run_command_stdin()


if __name__ == "__main__":
    raise SystemExit(run_command_stdin() if not any(arg.startswith("--") for arg in sys.argv[1:]) else main())
