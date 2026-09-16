#!/usr/bin/env python3
"""Verify that a run directory has structurally valid result and evidence files."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kmb.models import validate_event_dict

REQUIRED_DIMENSIONS = {"retention", "memory_recall", "dynamic_update", "similar_distinction", "boundary", "task_reuse"}


def verify_run(path: str, strict: bool = False) -> dict:
    directory = Path(path)
    result_path = directory / "result.json"
    evidence_path = directory / "evidence.jsonl"
    if not result_path.exists():
        raise ValueError("missing result.json")
    if not evidence_path.exists():
        raise ValueError("missing evidence.jsonl")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    rows = result.get("results")
    if not isinstance(rows, list) or int(result.get("cases", -1)) != len(rows):
        raise ValueError("result cases count does not match results")
    if not result.get("agent"):
        raise ValueError("result missing agent")
    if strict and not REQUIRED_DIMENSIONS.issubset(set(result.get("dimensions", {}))):
        raise ValueError("result is missing one or more benchmark dimensions")
    evidence_count = 0
    with evidence_path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            event = json.loads(line)
            for field in ("case_id", "kind", "data", "step"):
                if field not in event:
                    raise ValueError("evidence line %d missing %s" % (line_number, field))
            try:
                validate_event_dict(event)
            except ValueError as exc:
                raise ValueError("evidence line %d invalid: %s" % (line_number, exc))
            evidence_count += 1
    return {"status": "valid", "agent": result["agent"], "cases": len(rows), "evidence_events": evidence_count, "run_id": result.get("run_id")}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Verify a KylinMemoryBench run")
    parser.add_argument("run_dir")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = verify_run(args.run_dir, args.strict)
    except Exception as exc:
        print("invalid: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
