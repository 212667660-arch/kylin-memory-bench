#!/usr/bin/env python3
"""Agent environment fingerprint: hash skills/config/binaries for provenance.

Read-only. Emits only SHA-256 digests, file counts and paths — never file
contents — so no secret stored in an agent config can leak through it.

Purpose: pin the agent environment (skill tree, config, executable) so that
benchmark batches run on different days can be proven identical before their
scores are compared. Suite/scorer hashes are already recorded by
official_repeat; this covers the Agent side, which was previously `unknown`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Per-agent paths (relative to the agent HOME) that influence behaviour and
# therefore must be identical between batches whose scores get compared.
# Memory databases are deliberately excluded: official_repeat clones the home
# and clears memory tables, so their content never reaches a scored batch.
AGENT_SPECS: Dict[str, List[Dict[str, str]]] = {
    "kylinbot": [
        {"label": "config", "path": ".kylinbot/config.toml", "kind": "file"},
        {"label": "skills", "path": ".kylinbot/workspace/skills", "kind": "tree"},
    ],
    "openclaw": [
        {"label": "config", "path": ".openclaw/openclaw.json", "kind": "file"},
        {"label": "skills", "path": ".openclaw/skills", "kind": "tree"},
    ],
    "hermes": [
        {"label": "config", "path": ".hermes/config.yaml", "kind": "file"},
    ],
    "kylinagent": [
        {"label": "config", "path": ".kylin-agent-runtime", "kind": "tree"},
    ],
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fingerprint_file(path: Path) -> Dict[str, Any]:
    return {"sha256": _sha256_file(path), "files": 1, "bytes": path.stat().st_size}


def _fingerprint_tree(path: Path) -> Dict[str, Any]:
    entries: List[str] = []
    files = 0
    total = 0
    for candidate in sorted(path.rglob("*")):
        if not candidate.is_file() or candidate.is_symlink():
            continue
        relative = candidate.relative_to(path).as_posix()
        digest = _sha256_file(candidate)
        size = candidate.stat().st_size
        entries.append("%s:%s" % (relative, digest))
        files += 1
        total += size
    combined = hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest() if entries else ""
    return {"sha256": combined, "files": files, "bytes": total}


def fingerprint_agent_home(agent_id: str, home: Path, bin_path: Path = None) -> Dict[str, Any]:
    """Fingerprint one agent's behaviour-relevant files under ``home``."""
    home = Path(home).expanduser()
    items: List[Dict[str, Any]] = []
    for spec in AGENT_SPECS.get(agent_id, []):
        target = home / spec["path"]
        if not target.exists():
            items.append({"label": spec["label"], "path": spec["path"], "kind": spec["kind"], "sha256": "", "files": 0, "bytes": 0, "status": "missing"})
            continue
        report = _fingerprint_file(target) if spec["kind"] == "file" else _fingerprint_tree(target)
        report.update({"label": spec["label"], "path": spec["path"], "kind": spec["kind"], "status": "present"})
        items.append(report)
    if bin_path is not None and Path(bin_path).is_file():
        report = _fingerprint_file(Path(bin_path))
        report.update({"label": "executable", "path": str(bin_path), "kind": "file", "status": "present"})
        items.append(report)
    digests = [item["sha256"] for item in items if item["sha256"]]
    combined = hashlib.sha256("\n".join(digests).encode("utf-8")).hexdigest() if digests else "missing"
    return {
        "agent": agent_id,
        "home": str(home),
        "items": items,
        "fingerprint_sha256": combined,
        "note": "read-only fingerprint; hashes only, no file contents; memory DBs excluded (cleared per batch)",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read-only agent environment fingerprint for batch provenance")
    parser.add_argument("--agents", nargs="+", default=sorted(AGENT_SPECS), help="agent ids to fingerprint (default: all)")
    parser.add_argument("--home", default=os.path.expanduser("~"), help="agent home directory (default: current user home)")
    parser.add_argument("--bin", action="append", default=[], metavar="AGENT=PATH", help="also hash an executable file, e.g. --bin kylinbot=/usr/bin/kylin-bot")
    parser.add_argument("--out", default="", help="write JSON here (default: stdout)")
    args = parser.parse_args(argv)

    bins: Dict[str, Path] = {}
    for entry in args.bin:
        agent_id, _, path = entry.partition("=")
        if not agent_id or not path:
            parser.error("--bin expects AGENT=PATH")
        bins[agent_id] = Path(path)

    payload = {
        "generated_for_agents": list(args.agents),
        "agents": [
            fingerprint_agent_home(agent_id, Path(args.home), bins.get(agent_id))
            for agent_id in args.agents
        ],
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        summary = {report["agent"]: report["fingerprint_sha256"][:16] for report in payload["agents"]}
        print(json.dumps(summary, ensure_ascii=False))
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
