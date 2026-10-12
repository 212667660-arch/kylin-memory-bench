#!/usr/bin/env python3
"""Single-command, credential-free official acceptance orchestration."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from kmb.paths import runtime_root

ROOT = runtime_root()
OFFLINE_PAIRS = (
    ("core-compare", "suites/core-zh.yaml", "offline-demo-core", "reference", "kylinbot-process"),
    ("expanded-compare", "suites/core-zh-expanded.yaml", "offline-demo-expanded", "reference", "kylinbot-process"),
    ("adversarial-compare", "suites/adversarial/extended.yaml", "offline-demo-adversarial", "reference", "kylinbot-process"),
    ("flawed-contrast", "suites/core-zh.yaml", "offline-demo-flawed", "reference", "flawed"),
)


@dataclass
class AcceptanceResult:
    exit_code: int
    status: str
    summary: Dict[str, Any]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run(command: List[str], cwd: Path, log_path: Path) -> Dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "$ " + " ".join(command) + "\n\nSTDOUT\n" + completed.stdout + "\nSTDERR\n" + completed.stderr,
        encoding="utf-8",
    )
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
        "log": str(log_path),
    }


def _strict_verify(out: Path, agent: str, step: int) -> Dict[str, Any]:
    run_dir = out / agent
    result = _run(
        [sys.executable, "scripts/verify_run.py", str(run_dir), "--strict"],
        ROOT,
        out.parent / "logs" / (out.name + "-%s-verify-%d.log" % (agent, step)),
    )
    if result["exit_code"] == 0:
        payload = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
        if payload.get("score_valid") is not True:
            result["exit_code"] = 3
            result["reason"] = "structured evidence is valid, but the Agent run has an invalid score"
    return result


def _scan_secrets(root: Path) -> bool:
    markers = ("sk-", "api_key=", "authorization: bearer", "OPENAI_API_KEY=")
    values = [value for key, value in os.environ.items() if "KEY" in key and value]
    for path in root.rglob("*"):
        if not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        if any(marker in content for marker in markers):
            # api_key_env is a safe metadata field; only flag concrete values or
            # authorization headers, not the name of an environment variable.
            if "api_key=" in content or "authorization: bearer" in content:
                return True
            if any(value.lower() in content for value in values if len(value) > 8):
                return True
    return False


def _artifact_index(out: Path) -> Dict[str, Any]:
    files: List[Dict[str, Any]] = []
    for path in sorted(out.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "artifacts.json" or path.name.startswith("acceptance-summary."):
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append({"path": str(path.relative_to(out)), "sha256": digest, "bytes": path.stat().st_size})
    by_name = {item["path"]: item for item in files}
    return {
        "files": files,
        "comparison_html": str(out / "core-compare" / "comparison.html") if (out / "core-compare" / "comparison.html").exists() else "",
        "core_result": str(out / "core-compare" / "reference" / "result.json") if (out / "core-compare" / "reference" / "result.json").exists() else "",
        "file_count": len(files),
        "indexed_names": sorted(by_name),
    }


def _write_reports(out: Path, summary: Dict[str, Any]) -> None:
    (out / "acceptance-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# KylinMemoryBench 官方验收摘要",
        "",
        "- 状态：**%s**" % summary["status"],
        "- 模式：`%s`" % summary["mode"],
        "- 用户主路径：一条命令启动验收，打开生成的 HTML 报告",
        "- 用户步骤数：%d" % summary["user_steps"],
        "- 秘密写入：`%s`" % summary["secrets_written"],
        "",
        "## 结果",
        "",
        "| 项目 | 状态 | 退出码 |",
        "|---|---|---:|",
    ]
    for item in summary.get("checks", []):
        lines.append("| `%s` | %s | %s |" % (item.get("name", ""), item.get("status", ""), item.get("exit_code", "")))
    lines.extend(["", "## 证据边界", "", "- offline/process 结果只证明可复核的系统级行为，不证明模型原生长期记忆。", "- PDF-12 桌面视频和项目级 LICENSE 按用户要求未纳入本轮。", "", "## 产物", ""])
    for path in summary.get("artifacts", {}).get("files", []):
        lines.append("- `%s` (sha256 `%s`)" % (path["path"], path["sha256"]))
    (out / "acceptance-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    body = "".join("<tr><th>%s</th><td>%s</td><td>%s</td></tr>" % (html.escape(str(item.get("name", ""))), html.escape(str(item.get("status", ""))), item.get("exit_code", "")) for item in summary.get("checks", []))
    page = "<!doctype html><html lang=\"zh-CN\"><meta charset=\"utf-8\"><title>官方验收摘要</title><style>body{font-family:system-ui,sans-serif;margin:2rem;color:#17202a}table{border-collapse:collapse}th,td{border:1px solid #ccd;padding:.4rem .6rem;text-align:left}code{font-size:.85em}</style><h1>KylinMemoryBench 官方验收摘要</h1><p>状态：<strong>%s</strong>；模式：<code>%s</code>；用户步骤：%d</p><table><tr><th>检查</th><th>状态</th><th>退出码</th></tr>%s</table><p>桌面视频和项目级 LICENSE 按用户要求未纳入本轮。</p></html>" % (html.escape(summary["status"]), html.escape(summary["mode"]), summary["user_steps"], body)
    (out / "acceptance-summary.html").write_text(page, encoding="utf-8")


def _offline(out: Path) -> AcceptanceResult:
    out.mkdir(parents=True, exist_ok=True)
    checks: List[Dict[str, Any]] = []
    commands: List[Dict[str, Any]] = []
    validated_suites = set()
    for index, (name, suite, run_id, agent_a, agent_b) in enumerate(OFFLINE_PAIRS, 1):
        destination = out / name
        if suite not in validated_suites:
            validation = _run(
                [sys.executable, "-m", "kmb.cli", "validate", "--strict", "--suite", suite],
                ROOT,
                out / "logs" / ("validate-" + suite.replace("/", "-") + ".log"),
            )
            commands.append(validation)
            checks.append({"name": "validate:" + suite, "status": "pass" if validation["exit_code"] == 0 else "fail", "exit_code": validation["exit_code"], "log": validation["log"]})
            validated_suites.add(suite)
            if validation["exit_code"] != 0:
                continue
        command = [
            sys.executable,
            "-m",
            "kmb.cli",
            "compare",
            "--agents",
            "configs/agent-%s.yaml" % agent_a,
            "configs/agent-%s.yaml" % agent_b,
            "--suite",
            suite,
            "--out",
            str(destination),
            "--run-id",
            run_id,
            "--seed",
            "42",
            "--retries",
            "0",
            "--timeout",
            "30",
        ]
        result = _run(command, ROOT, out / "logs" / (name + ".log"))
        commands.append(result)
        checks.append({"name": name + ":compare", "status": "pass" if result["exit_code"] == 0 else "fail", "exit_code": result["exit_code"], "log": result["log"]})
        if result["exit_code"] != 0:
            continue
        for agent in (agent_a, agent_b):
            verification = _strict_verify(destination, agent, index)
            commands.append(verification)
            checks.append({"name": name + ":verify:" + agent, "status": "pass" if verification["exit_code"] == 0 else "fail", "exit_code": verification["exit_code"], "log": verification["log"]})
    (out / "commands.json").write_text(json.dumps(commands, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary: Dict[str, Any] = {
        "generated_at": _now(),
        "status": "pass" if checks and all(item["exit_code"] == 0 for item in checks) else "invalid",
        "mode": "offline",
        "user_steps": 2,
        "secrets_written": _scan_secrets(out),
        "checks": checks,
        "commands": commands,
        "artifacts": _artifact_index(out),
        "deferred": ["PDF-12", "LICENSE"],
        "boundary": "offline/process results are system-level evidence, not native model memory",
    }
    (out / "artifacts.json").write_text(json.dumps(summary["artifacts"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary["secrets_written"] = _scan_secrets(out)
    _write_reports(out, summary)
    (out / "acceptance-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return AcceptanceResult(0 if summary["status"] == "pass" and not summary["secrets_written"] else 3, summary["status"], summary)


def _installed(out: Path, agent_a: Optional[str], agent_b: Optional[str], repeats: int = 1) -> AcceptanceResult:
    from kmb.agent_registry import discover_agents, profiles_to_dicts
    from scripts.official_repeat import run_official_repeat

    profiles = discover_agents(ROOT)
    runnable = [profile.id for profile in profiles if profile.runnable]
    selected = [value for value in (agent_a, agent_b) if value] or runnable[:2]
    if len(selected) != 2 or len(set(selected)) != 2:
        summary = {
            "generated_at": _now(), "status": "blocked", "mode": "installed", "user_steps": 2,
            "secrets_written": False, "checks": [{"name": "agent-preflight", "status": "blocked", "exit_code": 2}],
            "agents": profiles_to_dicts(profiles), "deferred": ["PDF-12", "LICENSE"],
            "reason": "需要两个已安装且能提供结构化证据的可运行 Agent；未下载或安装任何 Agent。",
            "artifacts": {},
        }
        out.mkdir(parents=True, exist_ok=True)
        (out / "acceptance-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _write_reports(out, summary)
        return AcceptanceResult(2, "blocked", summary)
    try:
        metadata = run_official_repeat(
            selected,
            out / "official-repeat",
            repeats=max(1, int(repeats)),
        )
    except Exception as exc:
        summary = {"generated_at": _now(), "status": "blocked", "mode": "installed", "user_steps": 2, "secrets_written": False, "checks": [{"name": "agent-preflight", "status": "blocked", "exit_code": 2}], "agents": profiles_to_dicts(profiles), "reason": str(exc), "deferred": ["PDF-12", "LICENSE"], "artifacts": {}}
        out.mkdir(parents=True, exist_ok=True)
        (out / "acceptance-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _write_reports(out, summary)
        return AcceptanceResult(2, "blocked", summary)
    repeat_status = metadata.get("status")
    acceptance_status = "pass" if repeat_status == "completed" else "invalid" if repeat_status == "partial" else "blocked"
    repeat_exit = 0 if repeat_status == "completed" else 3 if repeat_status == "partial" else 2
    summary = {"generated_at": _now(), "status": acceptance_status, "mode": "installed", "user_steps": 2, "secrets_written": _scan_secrets(out), "checks": [{"name": "installed-agent-repeat", "status": acceptance_status, "exit_code": repeat_exit}], "agents": profiles_to_dicts(profiles), "official_repeat": metadata, "deferred": ["PDF-12", "LICENSE"], "artifacts": _artifact_index(out), "boundary": "installed Agent results remain limited to observed evidence"}
    out.mkdir(parents=True, exist_ok=True)
    (out / "commands.json").write_text(json.dumps([], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "artifacts.json").write_text(json.dumps(summary["artifacts"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_reports(out, summary)
    summary["artifacts"] = _artifact_index(out)
    (out / "acceptance-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return AcceptanceResult(repeat_exit if not summary["secrets_written"] else 3, summary["status"], summary)


def run_official_acceptance(out: Path | str, mode: str = "offline", agent_a: Optional[str] = None, agent_b: Optional[str] = None, repeats: int = 1) -> AcceptanceResult:
    destination = Path(out).resolve()
    if mode == "offline":
        return _offline(destination)
    if mode == "installed":
        return _installed(destination, agent_a, agent_b, repeats=repeats)
    return AcceptanceResult(4, "error", {"generated_at": _now(), "status": "error", "mode": mode, "reason": "mode must be offline or installed"})


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the official KylinMemoryBench acceptance path")
    parser.add_argument("--out", default="runs/official-acceptance")
    parser.add_argument("--mode", choices=("offline", "installed"), default="offline")
    parser.add_argument("--agent-a", default=None)
    parser.add_argument("--agent-b", default=None)
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args(list(argv) if argv is not None else None)
    result = run_official_acceptance(args.out, args.mode, args.agent_a, args.agent_b, args.repeats)
    print(json.dumps({"status": result.status, "exit_code": result.exit_code, "out": str(Path(args.out).resolve())}, ensure_ascii=False))
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
