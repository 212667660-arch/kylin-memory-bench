import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.official_acceptance import run_official_acceptance


class OfficialAcceptanceTests(unittest.TestCase):
    def test_invalid_agent_score_cannot_pass_offline_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            suite = "suites/core-zh.yaml"

            def fake_run(command, cwd, log_path):
                if "compare" in command:
                    output = Path(command[command.index("--out") + 1])
                    for name in ("reference", "kylinbot-process"):
                        target = output / name
                        target.mkdir(parents=True)
                        (target / "result.json").write_text(json.dumps({
                            "score_valid": name == "reference",
                            "score_status": "valid" if name == "reference" else "invalid_runtime",
                        }), encoding="utf-8")
                return {"exit_code": 0, "log": str(log_path)}

            with patch("scripts.official_acceptance._run", side_effect=fake_run), patch(
                "scripts.official_acceptance.OFFLINE_PAIRS",
                [("core", suite, "test", "reference", "kylinbot-process")],
            ):
                result = run_official_acceptance(root)
            self.assertEqual(result.status, "invalid")
            self.assertEqual(result.exit_code, 3)
            self.assertTrue(any(item["status"] == "fail" for item in result.summary["checks"]))

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
