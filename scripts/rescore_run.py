#!/usr/bin/env python3
"""Rescore existing JSONL evidence without changing the original run directory."""

import argparse
import copy
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kmb.models import EvidenceEvent, summarize_evidence
from kmb.report import radar_svg, write_html_report, write_markdown
from kmb.runner import load_suite
from kmb.scoring import score_case


def _event(raw):
    data = dict(raw.get("data", {}))
    return EvidenceEvent(
        kind=str(raw["kind"]), data=data, step=int(raw.get("step", 0)),
        timestamp=str(raw.get("timestamp") or EvidenceEvent("placeholder", {}, 0).timestamp),
        source=str(raw.get("source") or data.get("source") or "unknown"),
        evidence_class=str(raw.get("evidence_class") or data.get("evidence_class") or ""),
    )


def rescore_run(source_dir, suite_path, output_dir):
    source, output = Path(source_dir), Path(output_dir)
    if source.resolve() == output.resolve():
        raise ValueError("--out must differ from source_dir to preserve the original evidence")
    result_path, evidence_path = source / "result.json", source / "evidence.jsonl"
    if not result_path.exists() or not evidence_path.exists():
        raise ValueError("source run must contain result.json and evidence.jsonl")
    original = json.loads(result_path.read_text(encoding="utf-8"))
    original_cases = {str(item.get("case_id")): item for item in original.get("results", [])}
    events_by_case, all_events = {}, []
    for line in evidence_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        event = _event(raw)
        case_id = str(raw.get("case_id", ""))
        events_by_case.setdefault(case_id, []).append(event)
        all_events.append(event)

    results, failures, attempt_errors = [], Counter(), Counter()
    for event in all_events:
        if event.kind != "error":
            continue
        message = str(event.data.get("message", "")).lower()
        if "timeout" in message:
            attempt_errors["timeout"] += 1
        elif "filenotfounderror" in message or "missing_input" in message:
            attempt_errors["missing_input"] += 1
        else:
            attempt_errors["runtime_error"] += 1
    for case in load_suite(str(suite_path)):
        score = score_case(case, events_by_case.get(case.id, []))
        prior = original_cases.get(case.id, {})
        score.attempts = int(prior.get("attempts", 1))
        if prior.get("status") == "error":
            runtime_failures = [item for item in prior.get("failures", []) if item.get("type") == "runtime_error"]
            score.status, score.score = "error", 0.0
            score.failures.extend(runtime_failures or [{
                "type": "runtime_error", "reason": "source run recorded a runtime error", "check": {},
                "evidence_refs": [{"kind": "error", "step": 0, "source": "runner", "evidence_class": "runtime_error"}],
            }])
        score.observability = summarize_evidence(events_by_case.get(case.id, []))
        for failure in score.failures:
            failures[failure.get("type", "invalid_behavior")] += 1
        results.append(score.to_dict())
    failures.update(attempt_errors)

    dimensions = {}
    for capability in {item["capability"] for item in results}:
        values = [float(item["score"]) for item in results if item["capability"] == capability]
        dimensions[capability] = round(sum(values) / len(values) * 100, 2)
    rescored = copy.deepcopy(original)
    rescored.update({
        "cases": len(results), "dimensions": dimensions,
        "overall": round(sum(float(item["score"]) for item in results) / len(results) * 100, 2) if results else 0.0,
        "failure_counts": dict(failures), "results": results,
        "observability": summarize_evidence(all_events),
        "evidence": str(output / "evidence.jsonl"),
        "rescored_at": datetime.now(timezone.utc).isoformat(),
        "rescore_policy": "current deterministic scorer; source evidence copied unchanged",
        "attempt_error_counts": dict(attempt_errors),
        "source_run": str(source),
    })
    output.mkdir(parents=True, exist_ok=True)
    (output / "evidence.jsonl").write_text(evidence_path.read_text(encoding="utf-8"), encoding="utf-8")
    (output / "result.json").write_text(json.dumps(rescored, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(rescored, str(output / "result.md"))
    (output / "radar.svg").write_text(radar_svg(rescored["dimensions"]), encoding="utf-8")
    write_html_report([rescored], str(output / "result.html"))
    return rescored


def main(argv=None):
    parser = argparse.ArgumentParser(description="Rescore a KylinMemoryBench run without changing source evidence")
    parser.add_argument("source_dir")
    parser.add_argument("--suite", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        result = rescore_run(args.source_dir, args.suite, args.out)
    except Exception as exc:
        print("rescore failed: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps({"status": "ok", "agent": result.get("agent"), "overall": result.get("overall"), "out": args.out}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
