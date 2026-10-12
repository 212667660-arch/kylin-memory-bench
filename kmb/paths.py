"""Locate benchmark assets in source, Debian and pip installations."""
from pathlib import Path
import site
import sys


def runtime_root() -> Path:
    source = Path(__file__).resolve().parents[1]
    for root in (
        source,
        Path(sys.prefix) / "share/kylin-memory-bench",
        Path(site.getuserbase()) / "share/kylin-memory-bench",
    ):
        if (root / "suites/core-zh.yaml").is_file():
            return root
    raise FileNotFoundError("KylinMemoryBench installation is missing benchmark suites")
