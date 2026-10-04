#!/usr/bin/env python3
"""Build a deterministic, auditable inventory of benchmark-suite coverage."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Union

import yaml


CAPABILITIES = ("retention", "memory_recall", "dynamic_update", "similar_distinction", "boundary", "task_reuse")
SENSITIVE = re.compile(r"\b(password|passwd|secret|token|otp|one[- ]time code|verification code|card|email|phone)\b|密码|口令|验证码|密钥|银行卡|邮箱|手机号", re.I)
RISKY = re.compile(r"rm\s+-rf|sudo\s+|chmod\s+777|drop\s+database|删除根目录", re.I)
NOISE = re.compile(r"\b(noise|chatter|distractor|weather|sports)\b|噪声|闲聊|干扰", re.I)
CONFLICT = re.compile(r"\b(conflict|changed|update|promoted|now)\b|冲突|更新|变更|改为", re.I)
CJK = re.compile(r"[\u3400-\u9fff]")
EVIDENCE_TYPES = {
    "answer_contains", "answer_not_contains", "memory_recall", "memory_absent", "memory_value",
    "memory_expired", "scope_isolation", "sensitive_not_persisted", "memory_version", "action_path",
    "action_tool", "artifact_exists", "artifact_contains", "action_exit_code", "restart_boundary",
    "evidence_chain", "state_sequence",
}


def _read_suite(path: Path) -> Dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if isinstance(payload, list):
        return {"name": path.stem, "version": 1, "cases": payload}
    if not isinstance(payload, dict) or not isinstance(payload.get("cases", []), list):
        raise ValueError("suite must contain a cases list: %s" % path)
    return payload


def _all_text(case: Dict[str, Any]) -> str:
    parts = [str(case.get("title", "")), str(case.get("description", ""))]
    for turn in case.get("turns", []) or []:
        if isinstance(turn, dict):
            parts.append(str(turn.get("user", "")))
            parts.append(str(turn.get("assistant", "")))
            if turn.get("memory"):
                parts.append(json.dumps(turn["memory"], ensure_ascii=False))
    return " ".join(parts)


def _language(case: Dict[str, Any], suite: Dict[str, Any]) -> str:
    declared = str(suite.get("language", "")).lower()
    if declared in {"zh", "en", "mixed"}:
        return declared
    name = (str(suite.get("name", "")) + " " + str(suite.get("language", ""))).lower()
    if "zh" in name:
        return "zh"
    if "en" in name:
        return "en"
    return "zh" if CJK.search(_all_text(case)) else "en"


def _case_tags(case: Dict[str, Any]) -> List[str]:
    tags = set(str(tag) for tag in (case.get("tags") or []) if str(tag))
    text = _all_text(case)
    capability = str(case.get("capability", ""))
    operations = [str((turn.get("memory") or {}).get("op", "")) for turn in case.get("turns", []) if isinstance(turn, dict)]
    if any((turn.get("memory") or {}).get("persist", True) is False for turn in case.get("turns", []) if isinstance(turn, dict)):
        tags.update(("ephemeral", "suppression"))
    if any((turn.get("memory") or {}).get("persist", True) is True for turn in case.get("turns", []) if isinstance(turn, dict) and turn.get("memory")):
        tags.add("persistent")
    if SENSITIVE.search(text):
        tags.add("sensitive")
    if RISKY.search(text):
        tags.add("risk")
    if NOISE.search(text):
        tags.add("noise")
    if "update" in operations or CONFLICT.search(text):
        tags.add("conflict_update")
    if capability == "similar_distinction":
        tags.add("similar_entity")
    if capability == "task_reuse":
        tags.add("cross_task")
    if any(turn.get("action") for turn in case.get("turns", []) if isinstance(turn, dict)):
        tags.add("action")
    if any(turn.get("query") for turn in case.get("turns", []) if isinstance(turn, dict)):
        tags.add("recall")
    if "write" in operations:
        tags.add("write")
    if "update" in operations:
        tags.add("update")
    return sorted(tags)


def _evidence_requirements(case: Dict[str, Any]) -> List[str]:
    return sorted({str(check.get("type")) for check in case.get("checks", []) if isinstance(check, dict) and check.get("type") in EVIDENCE_TYPES})


def _case_record(suite_path: Path, suite: Dict[str, Any], case: Dict[str, Any]) -> Dict[str, Any]:
    tags = _case_tags(case)
    actions = sorted({str(turn.get("action", {}).get("tool")) for turn in case.get("turns", []) if isinstance(turn, dict) and isinstance(turn.get("action"), dict) and turn["action"].get("tool")})
    case_version = int(case.get("version", suite.get("version", 1)))
    return {
        "id": str(case.get("id", "")),
        "suite": suite_path.as_posix(),
        "version": case_version,
        "capability": str(case.get("capability", "")),
        "language": _language(case, suite),
        "tags": tags,
        "similar_group": str(case.get("similar_group") or ((case.get("metamorphic") or {}).get("group_id") if "similar_entity" in tags else "") or ""),
        "cross_task_group": str(case.get("cross_task_group") or (case.get("id", "") if "cross_task" in tags else "")),
        "expected_actions": actions,
        "evidence_requirements": _evidence_requirements(case),
    }


def _sequence_coverage(raw_suites: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = Counter()
    for _path, suite in raw_suites:
        for case in suite.get("cases", []) or []:
            turns = [turn for turn in (case.get("turns") or []) if isinstance(turn, dict)]
            ops = [str((turn.get("memory") or {}).get("op", "")) for turn in turns]
            has_write = "write" in ops
            has_update = "update" in ops
            has_suppress = any((turn.get("memory") or {}).get("persist", True) is False for turn in turns)
            has_recall = any(turn.get("query") for turn in turns)
            has_action = any(turn.get("action") for turn in turns)
            if has_write and has_recall:
                counts["write_then_recall"] += 1
            if has_write and has_update and has_recall:
                counts["write_update_then_recall"] += 1
            if has_suppress and has_recall:
                counts["suppress_then_recall"] += 1
            if has_write and has_action:
                counts["write_then_action_reuse"] += 1
    return dict(sorted(counts.items()))


def build_coverage_report(suite_paths: Iterable[Union[Path, str]]) -> Dict[str, Any]:
    raw_suites = []
    cases: List[Dict[str, Any]] = []
    suite_records = []
    seen = set()
    capabilities = Counter()
    languages = Counter()
    tags = Counter()
    missing_evidence = []
    for supplied in suite_paths:
        path = Path(supplied).resolve()
        suite = _read_suite(path)
        raw_suites.append((path, suite))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        try:
            display_path = path.relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            display_path = path.name
        suite_records.append({"path": display_path, "name": str(suite.get("name", path.stem)), "version": int(suite.get("version", 1)), "sha256": digest, "cases": len(suite.get("cases", []) or [])})
        for case in suite.get("cases", []) or []:
            record = _case_record(Path(display_path), suite, case)
            case_id = record["id"]
            if not case_id:
                raise ValueError("case id is required in %s" % display_path)
            if case_id in seen:
                raise ValueError("duplicate case id across suites: %s" % case_id)
            seen.add(case_id)
            if not record["evidence_requirements"]:
                missing_evidence.append(case_id)
            cases.append(record)
            capabilities[record["capability"]] += 1
            languages[record["language"]] += 1
            tags.update(record["tags"])
    missing_capabilities = sorted(set(CAPABILITIES) - set(capabilities))
    status = "valid" if not missing_capabilities and not missing_evidence else "incomplete"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "case_count": len(cases),
        "capabilities": {capability: capabilities.get(capability, 0) for capability in CAPABILITIES},
        "languages": dict(sorted(languages.items())),
        "scenario_tags": dict(sorted(tags.items())),
        "missing_capabilities": missing_capabilities,
        "missing_evidence_requirements": missing_evidence,
        "evidence_sequences": _sequence_coverage(raw_suites),
        "suite_hashes": suite_records,
        "cases": cases,
    }


def _manifest(report: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "rule_version": 1,
        "suites": report["suite_hashes"],
        "cases": report["cases"],
    }


def _markdown(report: Dict[str, Any]) -> str:
    lines = ["# 套件覆盖报告", "", "- 状态：`%s`" % report["status"], "- 案例总数：%d" % report["case_count"], "- 缺失能力：%s" % (", ".join(report["missing_capabilities"]) or "无"), "- 缺失证据检查：%s" % (", ".join(report["missing_evidence_requirements"]) or "无"), "", "## 六类能力", "", "| 能力 | 案例数 |", "|---|---:|"]
    lines.extend("| %s | %d |" % (key, value) for key, value in report["capabilities"].items())
    lines.extend(["", "## 语言", "", "| 语言 | 案例数 |", "|---|---:|"])
    lines.extend("| %s | %d |" % (key, value) for key, value in report["languages"].items())
    lines.extend(["", "## 场景标签", "", "| 标签 | 案例数 |", "|---|---:|"])
    lines.extend("| %s | %d |" % (key, value) for key, value in report["scenario_tags"].items())
    lines.extend(["", "## 关键证据序列", "", "| 序列 | 案例数 |", "|---|---:|"])
    lines.extend("| %s | %d |" % (key, value) for key, value in report["evidence_sequences"].items())
    lines.extend(["", "## 套件指纹", "", "| 套件 | 版本 | 案例 | SHA-256 |", "|---|---:|---:|---|"])
    lines.extend("| `%s` | %s | %s | `%s` |" % (suite["path"], suite["version"], suite["cases"], suite["sha256"]) for suite in report["suite_hashes"])
    return "\n".join(lines) + "\n"


def main(argv: Union[Iterable[str], None] = None) -> int:
    parser = argparse.ArgumentParser(description="Report capability and scenario coverage for benchmark suites")
    parser.add_argument("--suites", nargs="+", required=True)
    parser.add_argument("--out", required=True, help="output directory for coverage.json and coverage.md")
    parser.add_argument("--manifest", default="", help="optional auditable YAML case inventory")
    args = parser.parse_args(list(argv) if argv is not None else None)
    output = Path(args.out)
    try:
        report = build_coverage_report(args.suites)
    except Exception as exc:
        print("coverage report failed: %s" % exc, file=sys.stderr)
        return 2
    output.mkdir(parents=True, exist_ok=True)
    (output / "coverage.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "coverage.md").write_text(_markdown(report), encoding="utf-8")
    manifest_path = Path(args.manifest) if args.manifest else output / "manifest.yaml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(yaml.safe_dump(_manifest(report), allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(json.dumps({"status": report["status"], "cases": report["case_count"], "out": str(output)}, ensure_ascii=False))
    return 0 if report["status"] == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
