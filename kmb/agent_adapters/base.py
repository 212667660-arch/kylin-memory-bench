"""Shared process, response, and evidence helpers for native Agent adapters."""
from __future__ import annotations

import json
import os
import re
import shlex
import signal
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from ..models import EvidenceEvent
from ..agent_registry import resolve_agent_executable
from .sqlite_memory import diff_snapshots


ERROR_CATEGORIES = {
    "behavior_failure",
    "runtime_error",
    "timeout",
    "credential_error",
    "billing_error",
    "missing_input",
    "not_observable",
    "unsupported_action",
}


class AgentCommandError(RuntimeError):
    """Structured failure raised by a native Agent command."""

    def __init__(
        self,
        message: str,
        *,
        category: str = "runtime_error",
        returncode: Optional[int] = None,
        stdout_tail: str = "",
        stderr_tail: str = "",
    ) -> None:
        self.category = category if category in ERROR_CATEGORIES else "runtime_error"
        self.returncode = returncode
        self.stdout_tail = stdout_tail
        self.stderr_tail = stderr_tail
        super().__init__(message)


def classify_error(exc: BaseException) -> str:
    """Map adapter/process failures to stable benchmark error categories."""
    category = getattr(exc, "category", None)
    if category in ERROR_CATEGORIES:
        return category
    if isinstance(exc, (TimeoutError, subprocess.TimeoutExpired)):
        return "timeout"
    if isinstance(exc, FileNotFoundError):
        return "missing_input"
    text = str(exc or "").lower()
    if any(token in text for token in ("timeout", "timed out", "time out")):
        return "timeout"
    # Billing messages often mention the API key as well. Prefer the more
    # specific provider/account condition so users are not told to replace a
    # valid credential when the actual remedy is topping up the account.
    if any(token in text for token in ("billing", "quota", "payment", "insufficient credit", "credit balance", "402")):
        return "billing_error"
    if any(token in text for token in ("api key", "apikey", "credential", "unauthorized", "forbidden", "401", "403", "authentication")):
        return "credential_error"
    if any(token in text for token in ("not found", "no such file", "missing", "state.db", "brain.db")):
        return "missing_input"
    if any(token in text for token in ("not observable", "gui evidence", "no structured evidence")):
        return "not_observable"
    if any(token in text for token in ("unsupported", "not supported", "tool unavailable", "action unavailable")):
        return "unsupported_action"
    return "runtime_error"


def _tail(value: str, limit: int = 8192) -> str:
    value = str(value or "")
    return value if len(value) <= limit else value[-limit:]


def executable_available(command: Iterable[str]) -> bool:
    """Check the first command component without starting it."""
    parts = list(command)
    if not parts:
        return False
    executable = parts[0]
    path = Path(executable).expanduser()
    return resolve_agent_executable(str(path)) is not None


def preflight_command(command: Iterable[str], label: str = "Agent command") -> Dict[str, Any]:
    parts = list(command)
    available = executable_available(parts)
    return {
        "name": "command",
        "status": "ready" if available else "blocked",
        # Never persist arbitrary command-line arguments: users sometimes
        # place tokens there even though environment references are safer.
        "executable": parts[0] if parts else "",
        "argument_count": max(0, len(parts) - 1),
        "reason": "executable available" if available else "%s executable not found" % label,
    }


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
KEY_RE = re.compile(r"(?:alias|project|workspace|output\s+directory|benchmark)\s*(?:is|=|:)?\s*([A-Za-z0-9_.-]+)", re.I)


def process_event(kind: str, data: Dict[str, Any], step: int) -> EvidenceEvent:
    payload = dict(data)
    payload.setdefault("agent_owned", True)
    payload.setdefault("state_observed", kind.startswith("memory_") or kind == "assistant_message")
    payload.setdefault("not_model_native", True)
    return EvidenceEvent(kind, payload, step, source="process")


def case_keys(case: Any) -> List[str]:
    keys: List[str] = []
    for turn in case.turns if hasattr(case, "turns") else case.get("turns", []):
        query = turn.get("query") or {}
        key = str(query.get("key") or "").strip()
        if key and key not in keys:
            keys.append(key)
    return keys


def infer_key(text: str, known_keys: Iterable[str] = ()) -> str:
    for key in known_keys:
        if key.lower().replace("_", " ") in text.lower() or key.lower() in text.lower():
            return key
    match = KEY_RE.search(text or "")
    if match:
        return match.group(1).strip().lower().replace(" ", "_")
    lowered = (text or "").lower()
    if "benchmark" in lowered and "alias" in lowered:
        return "benchmark_alias"
    if "project" in lowered or "项目" in lowered:
        return "project"
    return "unknown_fact"


def extract_text(raw: str) -> str:
    """Extract assistant text from plain, JSON, or JSONL CLI output."""
    text = ANSI_RE.sub("", str(raw or "")).replace("\r\n", "\n").strip()
    try:
        return _find_text(json.loads(text)).strip()
    except json.JSONDecodeError:
        pass
    # A CLI may prefix pretty-printed JSON with status lines or emit JSONL.
    # Decode complete records and skip their interior lines so a nested tool
    # object cannot be mistaken for a later assistant response.
    candidates = []
    lines = text.splitlines(keepends=True)
    decoder = json.JSONDecoder()
    index = 0
    structured = False
    while index < len(lines):
        if not lines[index].lstrip().startswith(("{", "[", '"')):
            index += 1
            continue
        structured = True
        remaining = "".join(lines[index:]).lstrip()
        try:
            candidate, end = decoder.raw_decode(remaining)
        except json.JSONDecodeError:
            index += 1
            continue
        candidates.append(candidate)
        index += remaining[:end].count("\n") + 1
    for candidate in reversed(candidates):
        found = _find_text(candidate)
        if found:
            return found.strip()
    return "" if structured else text


def _find_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = [_find_text(item) for item in value]
        return "\n".join(text for text in parts if text)
    if isinstance(value, dict):
        if value.get("role") not in (None, "assistant"):
            return ""
        if value.get("kind") not in (None, "assistant", "assistant_message", "message"):
            return ""
        if "level" in value or value.get("type") in ("tool", "tool_call", "tool_result", "function_call", "reasoning", "thinking", "log", "error"):
            return ""
        for key in ("finalAssistantVisibleText", "finalAssistantRawText", "text", "content", "message", "response", "output", "result", "payloads", "choices", "delta", "data"):
            if key in value:
                found = _find_text(value[key])
                if found:
                    return found
    return ""


def invoke_command(command: List[str], timeout: float, env: Optional[Mapping[str, str]] = None) -> str:
    command = list(command)
    if command:
        command[0] = resolve_agent_executable(command[0], Path(env["HOME"]) if env and env.get("HOME") else None) or command[0]
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=dict(env or os.environ),
        start_new_session=os.name != "nt",
        creationflags=creationflags,
    )

    def terminate_group() -> None:
        if process.poll() is not None:
            return
        try:
            if os.name != "nt":
                os.killpg(process.pid, signal.SIGTERM)
            else:
                # ``taskkill /T`` reaches children/grandchildren when the
                # command was launched without an attached console.
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True,
                    check=False,
                )
        except (OSError, ValueError):
            process.kill()

    try:
        stdout, stderr = process.communicate(timeout=float(timeout))
    except subprocess.TimeoutExpired as exc:
        terminate_group()
        stdout, stderr = process.communicate()
        raise AgentCommandError(
            "Agent command timed out after %.2fs" % float(timeout),
            category="timeout",
            returncode=process.returncode,
            stdout_tail=_tail(stdout),
            stderr_tail=_tail(stderr),
        ) from exc
    if process.returncode != 0:
        stdout, stderr = _tail(stdout), _tail(stderr)
        detail = (stderr or stdout).strip()
        raise AgentCommandError(
            "Agent command exited %d: %s" % (process.returncode, detail),
            category=classify_error(RuntimeError(detail)),
            returncode=process.returncode,
            stdout_tail=stdout,
            stderr_tail=stderr,
        )
    return stdout


def memory_events_from_diff(changes: Iterable[Mapping[str, Any]], step: int, known_keys: Iterable[str]) -> List[EvidenceEvent]:
    events: List[EvidenceEvent] = []
    for change in changes:
        content = str(change.get("content") or "")
        old_content = change.get("old_content")
        key = str(change.get("key") or "") or infer_key(content, known_keys)
        if key == "unknown_fact":
            continue
        kind = "memory_update" if change.get("operation") == "update" else "memory_write"
        events.append(process_event(kind, {
            "key": key,
            "value": content,
            "old_value": old_content,
            "persist": True,
            "row_id": change.get("id"),
            "source_note": "read-only Agent storage delta observed after current CLI turn",
        }, step))
    return events


def recall_from_snapshot(snapshot: Mapping[str, Mapping[str, Any]], key: str, step: int) -> EvidenceEvent:
    lowered = key.lower()
    normalized = lowered.replace("_", " ")
    matches = [
        row for row in snapshot.values()
        if lowered in str(row.get("key", "")).lower()
        or normalized in str(row.get("key", "")).lower().replace("_", " ")
        or lowered in str(row.get("content", "")).lower()
        or normalized in str(row.get("content", "")).lower().replace("_", " ")
    ]
    value = matches[-1].get("content") if matches else None
    return process_event("memory_recall", {
        "key": key,
        "value": value,
        "hit": bool(matches),
        "source_note": "exact/substring lookup in Agent storage after current turn",
    }, step)


def configured_command(env_name: str, default_executable: str, default_args: Iterable[str]) -> List[str]:
    raw = os.environ.get(env_name, "").strip()
    executable = raw or default_executable
    parts = shlex.split(executable)
    return parts + list(default_args)
