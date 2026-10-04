#!/usr/bin/env python3
"""Run repeat batches against already-installed Agents in disposable homes."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import sqlite3
import sys
import tempfile
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.aggregate_repeats import aggregate_repeat_runs
from scripts.verify_run import verify_run

AGENT_DIRS = {"kylinbot": ".kylinbot", "openclaw": ".openclaw", "hermes": ".hermes"}
IGNORED_DIRS = {"cache", "caches", "logs", "node_modules", "__pycache__", "tmp", "temp", ".cache"}
OPENCLAW_STATE_ROOTS = {
    "transcript_events", "memory_index_chunk_recall_metadata", "memory_index_chunks",
    "memory_index_chunk_provenance", "memory_index_sources", "memory_index_meta",
    "memory_index_state", "memory_entry_origins", "session_transcript_fts",
    "memory_index_chunks_fts", "memory_index_paths_fts",
}


def _copy_agent_tree(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise FileNotFoundError("Agent home data directory is missing: %s" % source.name)
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.is_symlink() or item.name in IGNORED_DIRS:
            continue
        target = destination / item.name
        if item.is_dir():
            _copy_agent_tree(item, target)
        elif item.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            if item.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
                _backup_sqlite(item, target)
            else:
                shutil.copy2(str(item), str(target))


def _backup_sqlite(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_uri = "file:%s?mode=ro" % source.resolve().as_posix()
    source_connection = sqlite3.connect(source_uri, uri=True)
    target_connection = sqlite3.connect(str(destination))
    try:
        source_connection.backup(target_connection)
    finally:
        target_connection.close()
        source_connection.close()


def _clear_tables(database: Path, tables: Iterable[str], required: Iterable[str] = ()) -> None:
    if not database.is_file():
        raise FileNotFoundError("isolated memory database was not copied")
    connection = sqlite3.connect(str(database))
    try:
        available = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        missing = set(required) - available
        if missing:
            raise ValueError("isolated Agent database schema is unsupported: %s" % ", ".join(sorted(missing)))
        for table in tables:
            if table in available:
                safe_table = table.replace('"', '""')
                connection.execute('DELETE FROM "%s"' % safe_table)
        connection.commit()
    finally:
        connection.close()


def _clear_openclaw_state(database: Path) -> None:
    """Clear copied memory/transcript rows and every FK-dependent row."""
    if not database.is_file():
        return
    connection = sqlite3.connect(str(database))
    try:
        rows = connection.execute("SELECT name, sql FROM sqlite_master WHERE type='table'").fetchall()
        table_sql = {name: sql or "" for name, sql in rows}
        target = set(OPENCLAW_STATE_ROOTS).intersection(table_sql)
        changed = True
        while changed:
            changed = False
            for table in table_sql:
                if table in target or table.startswith("sqlite_"):
                    continue
                for foreign_key in connection.execute('PRAGMA foreign_key_list("%s")' % table.replace('"', '""')):
                    if foreign_key[2] in target:
                        target.add(table)
                        changed = True
                        break
        connection.execute("PRAGMA foreign_keys=OFF")
        for table in sorted(target):
            if table_sql.get(table, "").lstrip().upper().startswith("CREATE VIRTUAL TABLE"):
                safe_table = table.replace('"', '""')
                connection.execute('DELETE FROM "%s"' % safe_table)
        for table in sorted(target):
            if table_sql.get(table, "").lstrip().upper().startswith("CREATE VIRTUAL TABLE"):
                continue
            safe_table = table.replace('"', '""')
            connection.execute('DELETE FROM "%s"' % safe_table)
        connection.commit()
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise ValueError("isolated OpenClaw database contains foreign-key violations after clearing")
    finally:
        connection.close()


def prepare_agent_home(agent_id: str, source_home: Path | str, isolated_home: Path | str) -> Path:
    """Copy one Agent's config into a private HOME and clear copied memory rows."""
    if agent_id not in AGENT_DIRS:
        raise ValueError("unsupported Agent for isolated repeat: %s" % agent_id)
    source = Path(source_home).expanduser()
    destination = Path(isolated_home).expanduser()
    destination.mkdir(parents=True, exist_ok=False)
    os.chmod(str(destination), 0o700)
    source_agent = source / AGENT_DIRS[agent_id]
    target_agent = destination / AGENT_DIRS[agent_id]
    _copy_agent_tree(source_agent, target_agent)
    if agent_id == "kylinbot":
        _clear_tables(target_agent / "workspace/memory/brain.db", ("memories",), required=("memories",))
    elif agent_id == "hermes":
        _clear_tables(target_agent / "state.db", ("messages",), required=("messages",))
    else:
        for name in ("USER.md", "MEMORY.md"):
            (target_agent / "workspace" / name).unlink(missing_ok=True)
        database = target_agent / "agents/main/agent/openclaw-agent.sqlite"
        if database.is_file():
            _clear_openclaw_state(database)
    return destination


def _sanitize_isolation_paths(output: Path, homes: Dict[str, Path]) -> None:
    replacements = [(str(path), "<isolated-agent-home>") for path in homes.values()]
    for file_path in output.rglob("*"):
        if not file_path.is_file() or file_path.stat().st_size > 16 * 1024 * 1024:
            continue
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            continue
        updated = content
        for source, target in replacements:
            updated = updated.replace(source, target).replace(source.replace("\\", "/"), target)
        if updated != content:
            file_path.write_text(updated, encoding="utf-8")


def _copy_run_files(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("result.json", "evidence.jsonl"):
        path = source / name
        if path.is_file():
            shutil.copy2(str(path), str(destination / name))


def _write_summary(output: Path, payload: Dict[str, Any]) -> None:
    (output / "repeat-summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# 官方稳定性重复批次", "", "- 状态：`%s`" % payload["status"], "- Agent：%s" % ", ".join(payload["agents"]), "- 重复次数：%d" % payload["repeats"], "- seed：%d；固定套件：`%s`" % (payload["seed"], payload["suite"]), "", "## 分 Agent 汇总", "", "| Agent | 批次 | 执行成功率 | 有效分数率 | Overall 均值 | 标准差 | 来源 |", "|---|---:|---:|---:|---:|---:|---|"]
    for agent, summary in payload.get("aggregates", {}).items():
        overall = summary.get("overall", {})
        lines.append("| %s | %s | %s%% | %s%% | %s | %s | %s |" % (agent, summary.get("batch_count"), summary.get("execution_success_rate"), summary.get("score_valid_rate_percent"), overall.get("mean"), overall.get("stdev"), summary.get("source")))
        lines.extend(["", "### %s 六维与失败分类" % agent, "", "| 指标 | 均值 | 标准差 | 最小 | 最大 |", "|---|---:|---:|---:|---:|"])
        for dimension, stats in summary.get("dimensions", {}).items():
            lines.append("| %s | %s | %s | %s | %s |" % (dimension, stats.get("mean"), stats.get("stdev"), stats.get("min"), stats.get("max")))
        lines.append("\n失败类型：`%s`" % json.dumps(summary.get("failure_types", {}), ensure_ascii=False))
    lines.extend(["", "## 运行批次", ""])
    for record in payload.get("batches", []):
        lines.append("- `%s`: %s; strict=%s; score_valid=%s" % (record["run"], record["status"], record.get("strict_valid"), record.get("score_valid")))
        if record.get("reason"):
            lines.append("  - %s" % record["reason"])
    lines.extend(["", "每次重复使用临时 HOME 和空白记忆状态副本；原 Agent HOME 不作写入。失败批次保留，不以历史记忆补分。native memory 结论只依赖明确导出的原生事件。", ""])
    (output / "repeat-summary.md").write_text("\n".join(lines), encoding="utf-8")


def _blocked_aggregate(agent: str, root: Path) -> Dict[str, Any]:
    """Return a machine-readable aggregate when no runnable batch exists."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runs_root": str(root),
        "agent": agent,
        "batch_count": 0,
        "valid_batch_count": 0,
        "strict_invalid_count": 0,
        "score_valid_count": 0,
        "score_valid_rate": 0.0,
        "score_valid_rate_percent": 0.0,
        "execution_success_count": 0,
        "execution_failure_count": 0,
        "execution_success_rate": 0.0,
        "execution_failure_rate": 0.0,
        "success_rate": 0.0,
        "behavioral_case_count": 0,
        "behavioral_pass_count": 0,
        "behavioral_case_pass_rate": 0.0,
        "overall": {"count": 0, "mean": None, "stdev": None, "min": None, "max": None},
        "dimensions": {},
        "latency_ms": {"count": 0, "mean": None, "stdev": None, "min": None, "max": None},
        "failure_counts": {},
        "failure_types": {"blocked": 1},
        "source": "simulated",
        "source_counts": {},
        "runs": [],
        "observability": {"mode": ["blocked"], "native_memory_events": 0, "disclaimer": "Agent 未运行，不能从阻断状态推断能力或分数。"},
    }


def run_official_repeat(
    agents: List[str],
    out: Path | str,
    repeats: int = 3,
    suite: str = "suites/quick.yaml",
    seed: int = 42,
    timeout: float = 180.0,
    source_home: Optional[Path | str] = None,
) -> Dict[str, Any]:
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if len(agents) != 2 or len(set(agents)) != 2:
        raise ValueError("official repeat requires exactly two distinct Agents")
    destination = Path(out).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError("output directory is not empty; choose a new run directory")
    destination.mkdir(parents=True, exist_ok=True)
    original_home = Path(source_home or Path.home()).expanduser()
    batches: List[Dict[str, Any]] = []
    for repeat_index in range(1, repeats + 1):
        repeat_name = "repeat-%02d" % repeat_index
        repeat_root = destination / repeat_name
        repeat_root.mkdir()
        per_agent_root = destination / "agents"
        for agent in agents:
            (per_agent_root / agent / repeat_name).mkdir(parents=True, exist_ok=True)
        batch: Dict[str, Any] = {"run": repeat_name, "status": "blocked", "strict_valid": False, "score_valid": False}
        with tempfile.TemporaryDirectory(prefix="kmb-isolated-repeat-") as temp_root:
            temp_root_path = Path(temp_root)
            homes: Dict[str, Path] = {}
            try:
                for agent in agents:
                    home = temp_root_path / agent
                    prepare_agent_home(agent, original_home, home)
                    homes[agent] = home
                from kmb.quick_compare import QuickCompareOptions, run_quick_compare

                old_local = os.environ.get("KMB_OPENCLAW_LOCAL")
                os.environ["KMB_OPENCLAW_LOCAL"] = "1"
                hermes = original_home / ".kylin-agent-runtime/agent-runtime/venv/bin/hermes"
                old_hermes = os.environ.get("HERMES_COMMAND")
                if hermes.is_file() and "hermes" in agents:
                    os.environ["HERMES_COMMAND"] = str(hermes)
                try:
                    metadata = run_quick_compare(
                        QuickCompareOptions(agent_ids=agents, out_dir=str(repeat_root / "quick-compare"), seed=seed, retries=1, timeout=timeout, agent_homes={key: str(value) for key, value in homes.items()}, suite=suite),
                        root=ROOT,
                    )
                finally:
                    if old_local is None:
                        os.environ.pop("KMB_OPENCLAW_LOCAL", None)
                    else:
                        os.environ["KMB_OPENCLAW_LOCAL"] = old_local
                    if old_hermes is None:
                        os.environ.pop("HERMES_COMMAND", None)
                    else:
                        os.environ["HERMES_COMMAND"] = old_hermes
                _sanitize_isolation_paths(repeat_root, homes)
                agent_results = {}
                for agent in agents:
                    source = repeat_root / "quick-compare" / agent
                    valid = verify_run(str(source), strict=True)
                    result = json.loads((source / "result.json").read_text(encoding="utf-8"))
                    _copy_run_files(source, per_agent_root / agent / repeat_name)
                    agent_results[agent] = {"strict_valid": True, "score_valid": result.get("score_valid") is True, "overall": result.get("overall"), "evidence_events": valid["evidence_events"], "run_id": valid.get("run_id"), "agent_version": (result.get("discovery") or {}).get("version") or "unknown"}
                all_scores_valid = all(item["score_valid"] for item in agent_results.values())
                batch.update({"status": "completed" if all_scores_valid else "invalid_score", "strict_valid": True, "score_valid": all_scores_valid, "agents": agent_results, "run_id": metadata.get("run_id")})
            except Exception as exc:
                batch.update({"status": "blocked", "reason": "%s: %s" % (type(exc).__name__, str(exc))})
                _sanitize_isolation_paths(repeat_root, homes)
        batches.append(batch)
        (repeat_root / "batch.json").write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    aggregates = {}
    for agent in agents:
        root = destination / "agents" / agent
        has_result = any((path / "result.json").is_file() and (path / "evidence.jsonl").is_file() for path in root.glob("repeat-*") if path.is_dir())
        if has_result:
            aggregates[agent] = aggregate_repeat_runs(root, output_path=root / "summary.json")
        else:
            aggregates[agent] = _blocked_aggregate(agent, root)
            (root / "summary.json").write_text(json.dumps(aggregates[agent], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = "completed" if batches and all(batch["status"] == "completed" for batch in batches) else ("partial" if any(batch.get("strict_valid") for batch in batches) else "blocked")
    suite_path = Path(suite)
    if not suite_path.is_absolute():
        suite_path = ROOT / suite_path
    scorer_path = ROOT / "kmb/scoring.py"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "agents": agents,
        "repeats": repeats,
        "suite": suite,
        "seed": seed,
        "timeout": timeout,
        "suite_sha256": hashlib.sha256(suite_path.read_bytes()).hexdigest() if suite_path.is_file() else None,
        "scorer_sha256": hashlib.sha256(scorer_path.read_bytes()).hexdigest() if scorer_path.is_file() else None,
        "scorer_version": "sha256:%s" % hashlib.sha256(scorer_path.read_bytes()).hexdigest()[:16] if scorer_path.is_file() else "unknown",
        "environment": {"platform": platform.platform(), "python": sys.version.split()[0], "architecture": platform.machine()},
        "isolation": "disposable per-Agent HOME cloned from config and cleared Agent memory tables",
        "original_home_modified": False,
        "batches": batches,
        "aggregates": aggregates,
        "disclaimer": "System-level Agent behavior; native model memory is not claimed without native state events.",
    }
    _write_summary(destination, payload)
    return payload


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run isolated repeat batches against already-installed Agents")
    parser.add_argument("--agents", nargs=2, required=True)
    parser.add_argument("--suite", default="suites/quick.yaml")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--isolated-home", action="store_true", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        summary = run_official_repeat(args.agents, args.out, args.repeats, args.suite, args.seed, args.timeout)
    except Exception as exc:
        print("official repeat failed: %s" % exc, file=sys.stderr)
        return 4
    print(json.dumps({"status": summary["status"], "agents": summary["agents"], "repeats": summary["repeats"], "out": str(Path(args.out).resolve())}, ensure_ascii=False))
    return 0 if summary["status"] == "completed" else 3 if summary["status"] == "partial" else 2


if __name__ == "__main__":
    raise SystemExit(main())
