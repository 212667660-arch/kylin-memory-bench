#!/usr/bin/env python3
"""Build a deterministic, credential-free source bundle for official review."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]

INCLUDE_DIRS = ("kmb", "configs", "suites", "docs", "scripts", "tests", "packaging")
INCLUDE_FILES = (
    "README.md", "CHANGELOG.md", "NOTICE", "THIRD_PARTY_NOTICES.md",
    "LICENSE", "pyproject.toml", "setup.py",
)
FORBIDDEN_NAMES = {
    ".git", ".tmp-github-research", ".venv", ".venv-kmb-system", "runs",
    "dist", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".sqlite", ".sqlite3", ".db"}


@dataclass
class BundleResult:
    root: Path
    manifest: dict

    def contains(self, relative: str) -> bool:
        return (self.root / relative).exists()


def _ignore(directory: str, names: List[str]) -> set[str]:
    ignored = set()
    for name in names:
        path = Path(directory) / name
        if name in FORBIDDEN_NAMES or name.startswith(".tmp-"):
            ignored.add(name)
        elif path.is_file() and (path.suffix.lower() in FORBIDDEN_SUFFIXES or name in {".env", "credentials.env"}):
            ignored.add(name)
    return ignored


def _files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "release-manifest.json":
            continue
        if any(part in FORBIDDEN_NAMES or part.startswith(".tmp-") for part in path.relative_to(root).parts):
            continue
        yield path


def _sanitize_text_files(root: Path) -> None:
    """Remove host-specific HOME paths from copied documentation and tests."""
    patterns = (
        (re.compile(r"(?i)(?:[A-Z]:\\Users\\)[^\\/\s]+", re.I), "<user-home>"),
        (re.compile(r"/home/[^/\s]+", re.I), "<user-home>"),
    )
    for path in _files(root):
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            continue
        updated = content
        for pattern, replacement in patterns:
            updated = pattern.sub(replacement, updated)
        if updated != content:
            path.write_text(updated, encoding="utf-8")


def build_bundle(out: Path | str, source_root: Path | str = ROOT) -> BundleResult:
    source = Path(source_root).resolve()
    destination = Path(out).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError("bundle output is not empty: %s" % destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name in INCLUDE_DIRS:
        source_path = source / name
        if source_path.is_dir():
            shutil.copytree(source_path, destination / name, ignore=_ignore, dirs_exist_ok=True)
    for name in INCLUDE_FILES:
        path = source / name
        if path.is_file():
            shutil.copy2(path, destination / name)
    _sanitize_text_files(destination)
    manifest_files = []
    for path in _files(destination):
        manifest_files.append({
            "path": path.relative_to(destination).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        })
    manifest = {
        "format": "kmb-official-bundle-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(source),
        "python": "%d.%d" % sys.version_info[:2],
        "files": manifest_files,
        "excluded": sorted(FORBIDDEN_NAMES | {"credentials", "private HOME", "historical runs"}),
    }
    (destination / "release-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return BundleResult(destination, manifest)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build the credential-free official source bundle")
    parser.add_argument("--out", default="dist/official-bundle")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        result = build_bundle(args.out)
    except Exception as exc:
        print("bundle build failed: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps({"status": "ok", "out": str(result.root), "files": len(result.manifest["files"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
