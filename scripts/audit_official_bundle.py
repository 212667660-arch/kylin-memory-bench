#!/usr/bin/env python3
"""Audit an official bundle for secrets, private paths and generated results."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterable, Optional

FORBIDDEN_PARTS = {".git", ".tmp-github-research", "runs", "dist", "__pycache__", ".venv", "node_modules"}
FORBIDDEN_NAMES = {".env", "credentials.env"}
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9._-]{12,}"),
    re.compile(r"(?i)(?:api[_-]?key|password)\s*[:=]\s*['\"]?(?![^\n\r]*(?:test|example|dummy|fake|synthetic|must-not))([A-Za-z0-9_-]{24,})"),
    re.compile(r"(?i)C:\\Users\\[^\\\"\n]+\\\.kylinbot|/home/[^/\"\n]+/\.kylinbot"),
)


def audit_bundle(bundle: Path | str, strict: bool = False) -> dict:
    root = Path(bundle).resolve()
    if not root.is_dir():
        raise ValueError("bundle directory does not exist: %s" % root)
    issues = []
    files = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_dir():
            continue
        files.append(relative.as_posix())
        if path.name in FORBIDDEN_NAMES or any(part in FORBIDDEN_PARTS for part in relative.parts):
            issues.append({"path": relative.as_posix(), "reason": "forbidden generated/private path"})
            continue
        if path.name == "release-manifest.json":
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            issues.append({"path": relative.as_posix(), "reason": "unreadable: %s" % exc})
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                issues.append({"path": relative.as_posix(), "reason": "credential or private path pattern"})
                break
    manifest_path = root / "release-manifest.json"
    if not manifest_path.is_file():
        issues.append({"path": "release-manifest.json", "reason": "missing manifest"})
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = {item["path"]: item["sha256"] for item in manifest.get("files", [])}
        for name, digest in expected.items():
            path = root / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                issues.append({"path": name, "reason": "manifest hash mismatch"})
    result = {"status": "pass" if not issues else "fail", "bundle": str(root), "file_count": len(files), "issues": issues}
    if strict and issues:
        raise ValueError(json.dumps(result, ensure_ascii=False))
    return result


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit an official source bundle")
    parser.add_argument("bundle")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        result = audit_bundle(args.bundle, strict=args.strict)
    except Exception as exc:
        print("bundle audit failed: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
