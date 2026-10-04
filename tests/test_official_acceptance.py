import json
import tempfile
import unittest
from pathlib import Path

from scripts.official_acceptance import run_official_acceptance


class OfficialAcceptanceTests(unittest.TestCase):
    def test_offline_mode_writes_machine_readable_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_official_acceptance(Path(directory), mode="offline")
            self.assertEqual(result.exit_code, 0)
            summary = json.loads((Path(directory) / "acceptance-summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "pass")
            self.assertLessEqual(summary["user_steps"], 2)
            self.assertFalse(summary["secrets_written"])
            self.assertTrue(summary["artifacts"]["comparison_html"])
            self.assertTrue(any(item["name"] == "validate:suites/core-zh.yaml" for item in summary["checks"]))
            self.assertTrue((Path(directory) / "acceptance-summary.md").exists())
            self.assertTrue((Path(directory) / "acceptance-summary.html").exists())
            self.assertTrue((Path(directory) / "commands.json").exists())

    def test_invalid_mode_is_reported_without_running_agents(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_official_acceptance(Path(directory), mode="invalid")
            self.assertEqual(result.exit_code, 4)
            self.assertEqual(result.status, "error")


if __name__ == "__main__":
    unittest.main()
