#!/usr/bin/env python3
"""Rebuild a run report with current evidence provenance semantics.

The source run is never modified. This is useful when the schema gains new
provenance fields after a historical run has already been collected.
"""

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kmb.models import EvidenceEvent, summarize_evidence
from kmb.report import radar_svg, write_html_report, write_markdown


def _event_from_raw(raw: dict) -> EvidenceEvent:
    data = dict(raw.get("data", {}))
    source = str(raw.get("source") or data.get("source") or "unknown")
    evidence_class = str(raw.get("evidence_class") or data.get("evidence_class") or "")
    return EvidenceEvent(
        kind=str(raw.get("kind", "")), data=data, step=int(raw.get("step", 0)),
        timestamp=str(raw.get("timestamp") or EvidenceEvent("placeholder", {}, 0).timestamp),
        source=source, evidence_class=evidence_class,
    )


def enrich_run(source_dir: str, destination_dir: str) -> dict:
    source = Path(source_dir)
    destination = Path(destination_dir)
    result_path = source / "result.json"
    evidence_path = source / "evidence.jsonl"
    if not result_path.exists() or not evidence_path.exists():
        raise ValueError("source run must contain result.json and evidence.jsonl")
    summary = json.loads(result_path.read_text(encoding="utf-8"))
    events_by_case = {}
    events = []
    for line in evidence_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        event = _event_from_raw(raw)
        case_id = str(raw.get("case_id", ""))
        events_by_case.setdefault(case_id, []).append(event)
        events.append(event)
    enriched = copy.deepcopy(summary)
    enriched["observability"] = summarize_evidence(events)
    for result in enriched.get("results", []):
        case_events = events_by_case.get(str(result.get("case_id", "")), [])
        result["observability"] = summarize_evidence(case_events)
        indexed = {}
        for event in case_events:
            indexed.setdefault((event.kind, event.step), []).append(event)
        for check in result.get("checks", []):
            refs = []
            for ref in check.get("evidence_refs", []):
                candidates = indexed.get((str(ref.get("kind", "")), int(ref.get("step", 0))), [])
                if candidates:
                    event = candidates[0]
                    updated = dict(ref)
                    updated.update({"source": event.source, "evidence_class": event.evidence_class})
                    refs.append(updated)
                else:
                    refs.append(ref)
            check["evidence_refs"] = refs
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "evidence.jsonl").write_text(evidence_path.read_text(encoding="utf-8"), encoding="utf-8")
    enriched["evidence"] = str(destination / "evidence.jsonl")
    (destination / "result.json").write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(enriched, str(destination / "result.md"))
    (destination / "radar.svg").write_text(radar_svg(enriched.get("dimensions", {}), score_valid=enriched.get("score_valid", True)), encoding="utf-8")
    write_html_report([enriched], str(destination / "result.html"))
    return enriched


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Enrich an existing run with provenance fields")
    parser.add_argument("source_dir")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        enriched = enrich_run(args.source_dir, args.out)
    except Exception as exc:
        print("enrichment failed: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps({
        "status": "ok", "source": args.source_dir, "out": args.out,
        "agent": enriched.get("agent"), "mode": enriched.get("observability", {}).get("mode"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
