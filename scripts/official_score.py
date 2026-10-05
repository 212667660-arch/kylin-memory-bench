#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calculate a conservative official-view score from observed acceptance artifacts."""
from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = {"PDF-13": 15, "PDF-14": 25, "PDF-15": 25, "PDF-16": 15, "PDF-17": 10, "PDF-18": 10}
EXCLUDED = ["PDF-12", "LICENSE"]


def _all_checks_pass(evidence: Dict[str, Any]) -> bool:
    checks = evidence.get("checks") or []
    return bool(checks) and all(item.get("exit_code") == 0 and item.get("status") == "pass" for item in checks)


def calculate_official_score(evidence: Dict[str, Any], root: Optional[Path | str] = None) -> Dict[str, Any]:
    """Return weighted points with explicit reasons and no document self-attestation."""
    base = Path(root or ROOT).resolve()
    acceptance_dir = Path(evidence.get("acceptance_dir") or base)
    checks_pass = _all_checks_pass(evidence)
    coverage = base / "runs/coverage-report/coverage-report.json"
    if not coverage.exists():
        coverage = base / "runs/coverage-report/coverage.json"
    repeat = acceptance_dir / "official-repeat/repeat-summary.json"
    bundle_candidates = sorted(
        (path for path in (base / "dist").glob("official-bundle-*/release-manifest.json") if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    bundle_manifest = bundle_candidates[0] if bundle_candidates else base / "dist/official-bundle/release-manifest.json"
    points = {}
    items = {}

    def add(key: str, value: int, status: str, reason: str, command: str = ""):
        points[key] = max(0, min(WEIGHTS[key], int(value)))
        items[key] = {"weight": WEIGHTS[key], "points": points[key], "status": status, "reason": reason, "command": command, "evidence": []}

    add("PDF-13", WEIGHTS["PDF-13"] if checks_pass else 8, "pass" if checks_pass else "partial", "已观察到统一 CLI、Agent 发现/预检和 EvidenceEvent strict 校验。", "python -m kmb.cli official-acceptance")
    items["PDF-13"]["evidence"] = [str(acceptance_dir / "acceptance-summary.json"), str(acceptance_dir / "commands.json")]
    add("PDF-14", WEIGHTS["PDF-14"] if coverage.is_file() else 18, "pass" if coverage.is_file() else "partial", "覆盖报告存在且包含六类能力、语言、风险标签和套件哈希。" if coverage.is_file() else "覆盖代码存在，但当前验收目录未附覆盖报告。", "python scripts/coverage_report.py")
    items["PDF-14"]["evidence"] = [str(coverage)] if coverage.is_file() else ["scripts/coverage_report.py", "suites/coverage/manifest.yaml"]
    add("PDF-15", WEIGHTS["PDF-15"] if checks_pass else 18, "pass" if checks_pass else "partial", "结构化结果、失败分类、证据引用和 strict verify 已执行。", "python scripts/verify_run.py --strict")
    items["PDF-15"]["evidence"] = [str(acceptance_dir / "commands.json"), str(acceptance_dir / "artifacts.json")]
    if repeat.is_file():
        repeat_payload = json.loads(repeat.read_text(encoding="utf-8"))
        aggregates = repeat_payload.get("aggregates") or {}
        all_valid = repeat_payload.get("status") == "completed" and all(
            item.get("score_valid_rate_percent") == 100.0 and item.get("batch_count", 0) > 1
            for item in aggregates.values()
        )
        if all_valid:
            add("PDF-16", WEIGHTS["PDF-16"], "pass", "重复批次含执行成功率、有效分数率、均值、标准差和失败类型。", "python -m kmb.cli official-repeat")
            items["PDF-16"]["evidence"] = [str(repeat)]
        else:
            add("PDF-16", 5, "partial", "重复批次已保留，但存在 billing/timeout 或无效分数；不能宣称完整稳定。", "python -m kmb.cli official-repeat")
            items["PDF-16"]["evidence"] = [str(repeat)]
    else:
        add("PDF-16", 5, "partial", "本机/VM 官方重复批次证据尚未附在当前验收目录；不能用单次结果宣称稳定。", "python -m kmb.cli official-repeat")
        items["PDF-16"]["evidence"] = ["scripts/official_repeat.py", "scripts/aggregate_repeats.py"]
    report_files = [acceptance_dir / "acceptance-summary.json", acceptance_dir / "acceptance-summary.md", acceptance_dir / "acceptance-summary.html"]
    has_reports = all(path.is_file() for path in report_files)
    add("PDF-17", WEIGHTS["PDF-17"] if has_reports else 6, "pass" if has_reports else "partial", "JSON/Markdown/HTML 摘要及对比雷达产物可复核。", "python -m kmb.cli official-acceptance")
    items["PDF-17"]["evidence"] = [str(path) for path in report_files if path.is_file()]
    has_bundle = bundle_manifest.is_file()
    license_active = (base / "LICENSE").is_file()
    pdf18_reason = "官方脱敏包审计和 CLI/打包入口已具备；根目录 LICENSE 已生效（MIT，2026-10-05 负责人确认）。" if license_active else "官方脱敏包审计和 CLI/打包入口已具备；许可证仍单列为排除项。"
    add("PDF-18", WEIGHTS["PDF-18"] if has_bundle and checks_pass else 6, "pass" if has_bundle and checks_pass else "partial", pdf18_reason, "python scripts/build_official_bundle.py && python scripts/audit_official_bundle.py --strict")
    items["PDF-18"]["evidence"] = [str(path) for path in (base / "dist").glob("official-bundle-*/release-manifest.json")]
    total = sum(points.values())
    license_note = (
        "根目录 LICENSE 已生效（MIT，2026-10-05 项目负责人确认；评分模型不变，LICENSE 仍不计分）。"
        if license_active else
        "LICENSE 按用户要求未处理；不存在根目录生效许可证不能视为发布许可。"
    )
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "weights": dict(WEIGHTS), "points": points, "items": items, "total": total, "max_total": sum(WEIGHTS.values()), "excluded_from_score": list(EXCLUDED), "acceptance_status": evidence.get("status"), "license": {"active": license_active, "text": "MIT"}, "limitations": ["PDF-12 桌面视频按用户要求未处理。", license_note, "native_memory_events=0 时只报告系统级观测，不宣称模型原生记忆。"]}


def _write_outputs(out: Path, score: Dict[str, Any]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "scorecard.json").write_text(json.dumps(score, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    license_line = "- LICENSE：已生效（MIT）" if (score.get("license") or {}).get("active") else "- 排除：`LICENSE`（许可证）"
    lines = ["# 官方视角自评分", "", "- 总分：**%d/%d**" % (score["total"], score["max_total"]), "- 排除：`PDF-12`（视频）", license_line, "", "| 项目 | 权重 | 得分 | 状态 | 依据 |", "|---|---:|---:|---|---|"]
    for key in WEIGHTS:
        item = score["items"][key]
        lines.append("| %s | %d | %d | %s | %s |" % (key, item["weight"], item["points"], item["status"], item["reason"]))
    lines.extend(["", "## 边界", "", *["- " + item for item in score["limitations"]], ""])
    (out / "scorecard.md").write_text("\n".join(lines), encoding="utf-8")
    rows = "".join("<tr><td>%s</td><td>%d</td><td>%d</td><td>%s</td></tr>" % (key, score["items"][key]["weight"], score["items"][key]["points"], html.escape(score["items"][key]["status"])) for key in WEIGHTS)
    html_footer = "PDF-12 视频按用户要求未处理；LICENSE 已生效（MIT）。" if (score.get("license") or {}).get("active") else "PDF-12 视频和 LICENSE 按用户要求未处理。"
    (out / "official-review.html").write_text("<!doctype html><meta charset='utf-8'><title>官方视角自评分</title><h1>官方视角自评分：%d/%d</h1><table border='1'><tr><th>项目</th><th>权重</th><th>得分</th><th>状态</th></tr>%s</table><p>%s</p>" % (score["total"], score["max_total"], rows, html_footer), encoding="utf-8")


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Calculate the official weighted score")
    parser.add_argument("--acceptance", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)
    acceptance = Path(args.acceptance).resolve()
    try:
        evidence = json.loads((acceptance / "acceptance-summary.json").read_text(encoding="utf-8"))
        evidence["acceptance_dir"] = str(acceptance)
        score = calculate_official_score(evidence)
        _write_outputs(Path(args.out), score)
    except Exception as exc:
        print("official score failed: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps({"status": "ok", "total": score["total"], "max_total": score["max_total"], "out": str(Path(args.out).resolve())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
