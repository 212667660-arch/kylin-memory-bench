import json
import tempfile
import unittest
from pathlib import Path

from scripts.official_score import calculate_official_score


class OfficialScoreTests(unittest.TestCase):
    def test_official_score_uses_pdf_weights_and_excludes_user_deferred_items(self):
        score = calculate_official_score({"status": "pass", "checks": [{"status": "pass", "exit_code": 0}]})
        self.assertEqual(score["weights"], {"PDF-13": 15, "PDF-14": 25, "PDF-15": 25, "PDF-16": 15, "PDF-17": 10, "PDF-18": 10})
        self.assertEqual(score["excluded_from_score"], ["PDF-12", "LICENSE"])
        self.assertEqual(score["total"], sum(score["points"].values()))

    def test_partial_repeat_batch_does_not_receive_full_stability_points(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            acceptance = root / "acceptance"
            repeat = acceptance / "official-repeat"
            repeat.mkdir(parents=True)
            (repeat / "repeat-summary.json").write_text(json.dumps({
                "status": "partial",
                "aggregates": {"kylinbot": {"batch_count": 3, "score_valid_rate_percent": 33.33}},
            }), encoding="utf-8")
            score = calculate_official_score({"status": "invalid", "checks": []}, root=root)
            self.assertEqual(score["items"]["PDF-16"]["points"], 5)
            self.assertEqual(score["items"]["PDF-16"]["status"], "partial")

    def test_score_uses_latest_official_bundle_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "dist" / "official-bundle-final" / "release-manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text('{"files": []}\n', encoding="utf-8")
            score = calculate_official_score(
                {"status": "pass", "checks": [{"status": "pass", "exit_code": 0}]},
                root=root,
            )
            self.assertEqual(score["items"]["PDF-18"]["points"], 10)
            self.assertIn(str(manifest.resolve()), score["items"]["PDF-18"]["evidence"])

    def test_empty_or_single_agent_repeat_cannot_receive_full_stability_points(self):
        for aggregates in ({}, {"kylinbot": {"batch_count": 2, "score_valid_rate_percent": 100.0}}):
            with self.subTest(aggregates=aggregates), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                repeat = root / "official-repeat"
                repeat.mkdir()
                (repeat / "repeat-summary.json").write_text(json.dumps({
                    "status": "completed", "aggregates": aggregates,
                }), encoding="utf-8")
                score = calculate_official_score({"acceptance_dir": str(root), "checks": []}, root=root)
                self.assertEqual(score["items"]["PDF-16"]["status"], "partial")


    def test_license_limitation_reflects_root_license(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            score_absent = calculate_official_score({"status": "pass", "checks": []}, root=root)
            self.assertTrue(any("未处理" in item for item in score_absent["limitations"]))
            (root / "LICENSE").write_text("MIT License\n", encoding="utf-8")
            score_present = calculate_official_score({"status": "pass", "checks": []}, root=root)
            self.assertTrue(any("已生效" in item and "MIT" in item for item in score_present["limitations"]))
            self.assertEqual(score_present["excluded_from_score"], ["PDF-12", "LICENSE"])

if __name__ == "__main__":
    unittest.main()
