#!/usr/bin/env python3
"""Inventory reference-repository license and data-risk evidence.

This is a reproducible file inventory, not a legal license classifier. It does
not install, copy, or redistribute files from the research cache.
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT / ".tmp-github-research"
REPOSITORIES = {
    "MemoryAgentBench": "MemoryAgentBench",
    "GoodAI/goodai-ltm-benchmark": "goodai-ltm-benchmark",
    "ProsusAI/MemEval": "MemEval",
    "MemTensor/HaluMem": "HaluMem",
    "rzhub/GateMem": "GateMem",
    "Kylin-Agent-Competition/kylinOS-agent-memory": "kylinOS-agent-memory",
    "openkylin/llm-agent": "llm-agent",
}
LICENSE_NAMES = re.compile(r"^(license|licence|copying|notice)(\..*)?$", re.IGNORECASE)
MANIFEST_NAMES = {
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "requirements-dev.txt",
    "poetry.lock", "package.json", "package-lock.json", "environment.yml", "environment.yaml",
}
RISK_PARTS = {"data", "dataset", "datasets", "prompt", "prompts", "third_party", "third-party", "figures", "results"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _license_hint(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:20000].upper()
    except OSError:
        return "unreadable"
    for marker, label in (
        ("AGPL", "AGPL-family"), ("APACHE LICENSE", "Apache-2.0-family"),
        ("MIT LICENSE", "MIT-family"), ("ALL RIGHTS RESERVED", "All-Rights-Reserved"),
        ("CC BY-NC-ND", "CC-BY-NC-ND-family"), ("CREATIVE COMMONS", "Creative-Commons-family"),
    ):
        if marker in text:
            return label
    return "present-unclassified"


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def scan_repository(name: str, relative_root: str) -> dict:
    repo = RESEARCH_ROOT / relative_root
    if not repo.exists():
        return {"name": name, "status": "missing", "root": _relative(repo), "needs_manual_review": True}
    license_files = []
    manifests = []
    risk_paths = []
    file_count = 0
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        file_count += 1
        if LICENSE_NAMES.match(path.name):
            license_files.append({"path": _relative(path), "sha256": _sha256(path), "hint": _license_hint(path)})
        if path.name.lower() in MANIFEST_NAMES:
            manifests.append(_relative(path))
        if any(part.lower() in RISK_PARTS for part in path.parts):
            risk_paths.append(_relative(path))
    return {
        "name": name,
        "status": "scanned",
        "root": _relative(repo),
        "file_count": file_count,
        "license_files": license_files,
        "dependency_manifests": sorted(set(manifests)),
        "data_prompt_or_third_party_paths": sorted(risk_paths)[:500],
        "risk_path_count": len(risk_paths),
        "needs_manual_review": True,
        "note": "Inventory only; inspect each data, prompt, result, and transitive dependency license separately.",
    }


def scan_loose_material(name: str, relative_path: str) -> dict:
    path = ROOT / relative_path
    if not path.exists():
        return {"name": name, "status": "missing", "root": relative_path, "needs_manual_review": True}
    return {
        "name": name,
        "status": "loose-research-material",
        "root": relative_path,
        "file_count": 1,
        "license_files": [{"path": relative_path, "sha256": _sha256(path), "hint": _license_hint(path)}] if "LICENSE" in path.name.upper() else [],
        "dependency_manifests": [], "data_prompt_or_third_party_paths": [], "risk_path_count": 0,
        "needs_manual_review": True,
        "note": "Loose or archived research material is not a source tree and must not be packaged.",
    }


def build_inventory() -> dict:
    repositories = [scan_repository(name, relative_root) for name, relative_root in REPOSITORIES.items()]
    # HaluMem and GoodAI may be present only as raw/archived research material.
    if repositories[1]["status"] == "missing":
        repositories[1] = scan_loose_material("GoodAI/goodai-ltm-benchmark (archive)", ".tmp-github-research/goodai.zip")
    if repositories[3]["status"] == "missing":
        repositories[3] = scan_loose_material("MemTensor/HaluMem (raw license)", ".tmp-github-research/HaluMem-LICENSE.txt")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "research_root": _relative(RESEARCH_ROOT),
        "disclaimer": "This inventory is not a legal opinion and does not grant reuse rights.",
        "repositories": repositories,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Inventory reference repository license evidence")
    parser.add_argument("--out", default=None, help="write JSON inventory to this path")
    args = parser.parse_args(argv)
    payload = build_inventory()
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
