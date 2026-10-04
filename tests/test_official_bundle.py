import tempfile
import unittest
from pathlib import Path

from scripts.audit_official_bundle import audit_bundle
from scripts.build_official_bundle import build_bundle


class OfficialBundleTests(unittest.TestCase):
    def test_deb_payload_includes_runtime_script_dependencies(self):
        script = Path("scripts/build_deb.sh").read_text(encoding="utf-8")
        for name in (
            "export_kylinbot_evidence.py",
            "kylinbot_command_agent.py",
            "kylinbot_command_wrapper.py",
            "official_score.py",
        ):
            self.assertIn(name, script)

    def test_official_bundle_excludes_credentials_runs_caches_and_research(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = build_bundle(Path(directory) / "bundle")
            self.assertFalse(bundle.contains(".env"))
            self.assertFalse(bundle.contains("api_key"))
            self.assertFalse(bundle.contains("runs"))
            self.assertFalse(bundle.contains(".tmp-github-research"))
            self.assertTrue(bundle.contains("docs/official-acceptance.md"))
            self.assertEqual(audit_bundle(bundle.root, strict=True)["status"], "pass")

    def test_audit_rejects_concrete_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secret = "sk-" + "1234567890abcdef1234567890"
            (root / "bad.txt").write_text("api_key=" + secret, encoding="utf-8")
            (root / "release-manifest.json").write_text('{"files": []}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                audit_bundle(root, strict=True)


if __name__ == "__main__":
    unittest.main()
