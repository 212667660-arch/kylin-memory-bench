import json
import tempfile
import unittest
from pathlib import Path

from scripts.coverage_report import build_coverage_report, main


ROOT = Path(__file__).resolve().parents[1]


class CoverageReportTests(unittest.TestCase):
    def test_report_counts_capability_language_and_risk_dimensions(self):
        report = build_coverage_report([ROOT / "suites/core-zh.yaml"])
        self.assertEqual(report["capabilities"]["retention"], 1)
        self.assertEqual(report["languages"]["zh"], 6)
        self.assertGreaterEqual(report["scenario_tags"].get("sensitive", 0), 1)
        self.assertEqual(len(report["suite_hashes"]), 1)
        self.assertEqual(len(report["cases"]), 6)
        self.assertTrue(all(item["evidence_requirements"] for item in report["cases"]))

    def test_report_covers_extended_tags_and_writes_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            exit_code = main([
                "--suites", "suites/core-zh.yaml", "suites/core-zh-expanded.yaml",
                "suites/adversarial/extended.yaml", "suites/adversarial/multilingual-en.yaml",
                "--out", str(out), "--manifest", str(out / "manifest.yaml"),
            ])
            self.assertEqual(exit_code, 0)
            report = json.loads((out / "coverage.json").read_text(encoding="utf-8"))
            self.assertEqual(report["capabilities"]["boundary"], 10)
            self.assertEqual(report["languages"]["mixed"], 19)
            self.assertEqual(report["languages"]["en"], 6)
            self.assertGreaterEqual(report["scenario_tags"]["sensitive"], 8)
            self.assertGreaterEqual(report["scenario_tags"]["risk"], 2)
            self.assertGreaterEqual(report["scenario_tags"]["suppression"], 8)
            self.assertGreaterEqual(report["scenario_tags"]["noise"], 6)
            self.assertTrue((out / "coverage.md").exists())
            self.assertTrue((out / "manifest.yaml").exists())

    def test_report_counts_multilingual_en_suite(self):
        report = build_coverage_report([ROOT / "suites/adversarial/multilingual-en.yaml"])
        self.assertEqual(report["languages"]["en"], 6)
        self.assertEqual(report["capabilities"]["retention"], 1)
        self.assertEqual(report["capabilities"]["memory_recall"], 1)
        self.assertEqual(report["capabilities"]["dynamic_update"], 1)
        self.assertEqual(report["capabilities"]["similar_distinction"], 1)
        self.assertEqual(report["capabilities"]["boundary"], 1)
        self.assertEqual(report["capabilities"]["task_reuse"], 1)
        self.assertGreaterEqual(report["scenario_tags"].get("sensitive", 0), 1)
        self.assertGreaterEqual(report["scenario_tags"].get("suppression", 0), 1)
        self.assertGreaterEqual(report["scenario_tags"].get("noise", 0), 1)
        self.assertGreaterEqual(report["scenario_tags"].get("conflict_update", 0), 1)
        self.assertGreaterEqual(report["scenario_tags"].get("similar_entity", 0), 1)
        self.assertTrue(all(item["evidence_requirements"] for item in report["cases"]))

    def test_duplicate_case_ids_across_suites_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "one.yaml"
            second = root / "two.yaml"
            content = "name: same\nversion: 1\ncases:\n- id: duplicate\n  capability: retention\n  title: a\n  turns: []\n  checks: [{type: answer_contains, value: x}]\n"
            first.write_text(content, encoding="utf-8")
            second.write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate case id"):
                build_coverage_report([first, second])

    def test_sensitive_and_risk_cases_require_suppression_evidence(self):
        """Sensitive/risk cases must demand suppression, not merely absence."""
        for path in (ROOT / "suites/adversarial/extended.yaml", ROOT / "suites/adversarial/multilingual-en.yaml"):
            payload = json.loads(path.read_text(encoding="utf-8")) if False else __import__("yaml").safe_load(path.read_text(encoding="utf-8"))
            for case in payload.get("cases", []):
                checks = [str(check.get("type")) for check in case.get("checks") or []]
                text = json.dumps(case, ensure_ascii=False)
                sensitive_marker = any(word in text.lower() for word in ("otp", "password", "secret", "token", "card", "email", "密码", "口令", "验证码", "密钥", "银行卡", "邮箱", "手机号"))
                risk_marker = any(word in text for word in ("rm -rf", "sudo ", "chmod 777", "drop database", "删除根目录"))
                if sensitive_marker or risk_marker:
                    self.assertIn(
                        "sensitive_not_persisted", checks,
                        "%s: sensitive/risk 案例必须要求抑制证据" % case.get("id"),
                    )

    def test_new_cases_do_not_reuse_existing_core_ids(self):
        """The 2026-09-27 additions must append new IDs, never rename core cases."""
        core = {
            str(case.get("id"))
            for suite in ("suites/core-zh.yaml",)
            for case in __import__("yaml").safe_load((ROOT / suite).read_text(encoding="utf-8")).get("cases", [])
        }
        added = __import__("yaml").safe_load((ROOT / "suites/adversarial/multilingual-en.yaml").read_text(encoding="utf-8")).get("cases", [])
        self.assertEqual(len(added), 6)
        for case in added:
            self.assertNotIn(str(case.get("id")), core)


if __name__ == "__main__":
    unittest.main()
