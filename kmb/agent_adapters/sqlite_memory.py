"""Read-only, bounded snapshots for Agent SQLite state."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from scripts.export_kylinbot_evidence import redact_value


def _bounded(value: Any, limit: int = 800) -> str:
    return redact_value(str(value)[:limit])


def _first(row: Mapping[str, Any], names: Iterable[str]) -> str:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return str(value)
    return ""


class SQLiteMemorySnapshot:
    """Snapshot likely memory/message tables without mutating the database."""

    def __init__(self, path: Path, tables: Iterable[str] = ("memories", "messages"), max_rows: int = 2000):
        self.path = Path(path).expanduser()
        self.tables = tuple(str(table) for table in tables)
        self.max_rows = int(max_rows)

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        if not self.path.is_file():
            raise FileNotFoundError("Agent SQLite state not found: %s" % self.path)
        uri = "file:%s?mode=ro" % self.path.resolve().as_posix()
        connection = sqlite3.connect(uri, uri=True)
        try:
            available = {
                str(row[0])
                for row in connection.execute("select name from sqlite_master where type='table'")
            }
            snapshot: Dict[str, Dict[str, Any]] = {}
            for table in self.tables:
                if table not in available:
                    continue
                columns = [str(row[1]) for row in connection.execute("pragma table_info(%s)" % table)]
                if not columns:
                    continue
                quoted = ", ".join('"%s"' % column.replace('"', '""') for column in columns)
                rows = connection.execute("select %s from \"%s\" limit ?" % (quoted, table), (self.max_rows,))
                for values in rows:
                    raw = dict(zip(columns, values))
                    row_id = _first(raw, ("id", "uuid", "message_id", "event_id"))
                    content = _first(raw, ("content", "text", "message", "body", "value", "data"))
                    key = _first(raw, ("key", "memory_key", "name", "fact_key"))
                    identity_source = row_id or json.dumps(raw, sort_keys=True, ensure_ascii=False, default=str)
                    identity = "%s:%s" % (table, hashlib.sha256(identity_source.encode("utf-8", "replace")).hexdigest()[:20])
                    snapshot[identity] = {
                        "id": identity,
                        "table": table,
                        "key": _bounded(key, 160),
                        "content": _bounded(content),
                        "updated_at": _bounded(_first(raw, ("updated_at", "created_at", "timestamp", "ts")), 80),
                    }
            return snapshot
        finally:
            connection.close()


def diff_snapshots(before: Mapping[str, Mapping[str, Any]], after: Mapping[str, Mapping[str, Any]]) -> List[Dict[str, Any]]:
    changes: List[Dict[str, Any]] = []
    for identity in sorted(after):
        current = dict(after[identity])
        previous = dict(before[identity]) if identity in before else None
        if previous == current:
            continue
        current["operation"] = "update" if previous is not None else "write"
        current["old_content"] = previous.get("content") if previous else None
        changes.append(current)
    return changes


class TextMemorySnapshot:
    """Line-oriented snapshot for OpenClaw USER.md/MEMORY.md files."""

    def __init__(self, paths: Iterable[Path], max_lines: int = 5000):
        self.paths = [Path(path).expanduser() for path in paths]
        self.max_lines = int(max_lines)

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        snapshot: Dict[str, Dict[str, Any]] = {}
        for path in self.paths:
            if not path.is_file():
                continue
            for index, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines()[: self.max_lines], 1):
                text = line.strip()
                if not text:
                    continue
                identity = "%s:%d" % (path.as_posix(), index)
                snapshot[identity] = {
                    "id": identity,
                    "table": path.name,
                    "key": "",
                    "content": _bounded(text),
                    "updated_at": "",
                }
        return snapshot
