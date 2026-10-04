import json
import tempfile
import unittest
from pathlib import Path

from kmb.cli import main
from kmb.report import write_html_report


class CliReportTests(unittest.TestCase):
    def test_validate_and_list_cases_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            suite = Path(directory) / "suite.yaml"
            suite.write_text("cases:\n- id: c1\n  capability: retention\n  title: one\n  turns: []\n  checks: []\n", encoding="utf-8")
            self.assertEqual(main(["validate", "--suite", str(suite)]), 0)
            self.assertEqual(main(["list-cases", "--suite", str(suite)]), 0)

    def test_validate_rejects_duplicate_case_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            suite = Path(directory) / "invalid.yaml"
            suite.write_text(
                "cases:\n"
                "- id: duplicate\n  capability: retention\n  title: one\n  turns: []\n  checks: []\n"
                "- id: duplicate\n  capability: retention\n  title: two\n  turns: []\n  checks: []\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                main(["validate", "--suite", str(suite)])

    def test_strict_validate_requires_all_six_capabilities(self):
        with tempfile.TemporaryDirectory() as directory:
            suite = Path(directory) / "partial.yaml"
            suite.write_text("cases:\n- id: c1\n  capability: retention\n  title: one\n  turns: []\n  checks: []\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                main(["validate", "--strict", "--suite", str(suite)])

    def test_compare_requires_two_distinct_agents(self):
        with tempfile.TemporaryDirectory() as directory:
            suite = Path(directory) / "suite.yaml"
            suite.write_text("cases:\n- id: c1\n  capability: retention\n  title: one\n  turns: []\n  checks: []\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                main(["compare", "--agents", "reference", "reference", "--suite", str(suite), "--out", str(Path(directory) / "out")])

    def test_html_report_contains_collapsible_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            (Path(directory) / "radar.svg").write_text("<svg></svg>", encoding="utf-8")
            write_html_report([{
                "agent": "a", "overall": 50, "dimensions": {"retention": 50},
                "failure_counts": {"omission": 1},
                "results": [{"case_id": "c", "status": "fail", "score": 0.5,
                             "checks": [{"passed": False, "reason": "missing", "evidence_refs": []}],
                             "failures": [{"type": "omission", "reason": "missing"}]}],
            }], str(path))
            content = path.read_text(encoding="utf-8")
        self.assertIn("<details>", content)
        self.assertIn("omission", content)
        self.assertIn("<img", content)
        self.assertIn("失败统计", content)
        self.assertIn("能力边界", content)

    def test_runtime_error_report_marks_score_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            write_html_report([{
                "agent": "broken", "overall": 0, "score_valid": False,
                "score_status": "invalid_runtime", "error_cases": 1,
                "dimensions": {}, "results": [],
            }], str(path))
            content = path.read_text(encoding="utf-8")
        self.assertIn("不可评分", content)
        self.assertNotIn("<td>0.00</td>", content)
