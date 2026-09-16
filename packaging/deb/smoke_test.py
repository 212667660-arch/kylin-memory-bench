#!/usr/bin/env python3
"""Minimal offline test shipped inside the Debian package."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from kmb.cli import main
from kmb.runner import load_suite


class PackageSmokeTests(unittest.TestCase):
    def _home(self):
        configured = os.environ.get("KMB_HOME")
        if configured:
            return Path(configured)
        installed = Path("/usr/share/kylin-memory-bench")
        return installed if installed.exists() else Path(__file__).resolve().parents[1]

    def test_cli_can_validate_packaged_suite(self):
        suite = self._home() / "suites" / "core-zh.yaml"
        self.assertEqual(main(["validate", "--strict", "--suite", str(suite)]), 0)
        self.assertEqual(len(load_suite(str(suite))), 6)

    def test_cli_generates_offline_report_artifacts(self):
        home = self._home()
        suite = home / "suites" / "core-zh.yaml"
        with tempfile.TemporaryDirectory() as directory:
            # Deterministic agents validate package mechanics, not real-Agent claims.
            self.assertEqual(main([
                "compare", "--agents", str(home / "configs" / "agent-reference.yaml"),
                str(home / "configs" / "agent-flawed.yaml"), "--suite", str(suite),
                "--out", directory, "--run-id", "deb-package-smoke", "--seed", "42",
            ]), 0)
            self.assertTrue((Path(directory) / "comparison.json").exists())
            self.assertTrue((Path(directory) / "comparison.html").exists())
            self.assertTrue(json.loads((Path(directory) / "comparison.json").read_text(encoding="utf-8"))["agents"])


if __name__ == "__main__":
    unittest.main()
