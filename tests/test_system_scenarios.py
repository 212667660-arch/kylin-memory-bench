import json
import tempfile
import unittest
from pathlib import Path

from scripts.system_scenarios import _fact, run_all


class SystemScenarioTests(unittest.TestCase):
    def test_fact_contains_lifecycle_metadata(self):
        fact = _fact("test", "workspace", "/data/test", "scope-a", version=2)
        self.assertEqual(fact["persistence"], "persistent")
        self.assertEqual(fact["sensitivity"], "normal")
        self.assertEqual(fact["scope"], "scope-a")
        self.assertEqual(fact["version"], 2)
        self.assertIn("provenance", fact)

    def test_safe_executor_records_real_and_unexecuted_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            summary = run_all(Path(directory), "system-test", ["process-restart", "system-reboot", "user-switch", "permissions"])
            self.assertEqual(summary["passed_scenarios"], 1 if __import__("os").name != "posix" else 2)
            self.assertEqual(summary["not_executed_scenarios"], 3 if __import__("os").name != "posix" else 2)
            events = [json.loads(line) for line in (Path(directory) / "evidence.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertTrue(any(item["kind"] == "restart_boundary" for item in events))
            recalls = sum(1 for item in events if item["kind"] == "memory_recall")
            self.assertGreaterEqual(recalls, 3 if __import__("os").name == "posix" else 1)
            self.assertTrue(any(item["kind"] == "action" and item["data"].get("artifact_path") for item in events))
            self.assertTrue((Path(directory) / "system-summary.json").exists())
