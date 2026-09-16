import hashlib
import tempfile
import unittest
from pathlib import Path

from kmb.agents import MemoryControllerAgent
from kmb.runner import load_suite, run_suite, validate_cases
from kmb.scoring import score_case


class FakeBackend:
    name = "offline-fixture"
    model = "offline-fixture-v1"

    def describe(self):
        return {"adapter": type(self).__name__, "model": self.model, "fixture": True}

    def _url(self):
        return "offline://fixture"

    def _request(self, messages):
        return {"id": "offline", "choices": [{"message": {"content": "fixture response"}, "finish_reason": "stop"}]}

    def _message(self, response):
        return response["choices"][0]["message"]

    def _tool_events(self, message, step):
        return []

    def _evidence_events(self, case, response, message, step):
        return []


class LifecycleInnovationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_suite("suites/lifecycle/innovation.yaml")
        validate_cases(cls.cases, require_all_capabilities=True)

    def test_case_defaults_migrate_legacy_turn_metadata(self):
        case = load_suite("suites/core-zh.yaml")[0]
        self.assertEqual(case.facts[0]["persistence"], "persistent")
        self.assertEqual(case.facts[0]["scope"], "default")
        self.assertTrue(case.facts[0]["fact_id"])

    def test_wrapper_lifecycle_records_metadata_restart_and_artifact(self):
        case = next(item for item in self.cases if item.id == "lifecycle-path-001")
        with tempfile.TemporaryDirectory(dir=str(Path.cwd())) as directory:
            events = MemoryControllerAgent("fixture", FakeBackend(), directory).run(case)
            result = score_case(case, events)
            self.assertEqual(result.status, "pass")
            action = next(event for event in events if event.kind == "action")
            artifact = next(event for event in events if event.kind == "file_artifact")
            self.assertEqual(action.data["path"], "/data/b")
            self.assertEqual(action.data["exit_code"], 0)
            self.assertEqual(action.data["execution_scope"], "sandbox")
            self.assertTrue(action.data["artifact_sha256"])
            self.assertEqual(action.to_dict()["trust_level"], "verified")
            self.assertEqual(action.data["artifact_sha256"], hashlib.sha256(Path(action.data["artifact_path"]).read_bytes()).hexdigest())
            self.assertEqual(artifact.data["artifact_sha256"], action.data["artifact_sha256"])
            self.assertTrue(any(event.kind == "restart_boundary" and not event.data["system_restart"] for event in events))
            update = next(event for event in events if event.kind == "memory_update")
            self.assertEqual(update.data["fact_version"], 2)
            self.assertEqual(update.data["scope"], "project-a")

    def test_wrapper_expiry_sensitive_and_scope_rules_are_deterministic(self):
        agent = MemoryControllerAgent("fixture", FakeBackend(), tempfile.mkdtemp(dir=str(Path.cwd())))
        for case_id in ("lifecycle-expire-001", "lifecycle-sensitive-001", "lifecycle-scope-001"):
            case = next(item for item in self.cases if item.id == case_id)
            events = agent.run(case)
            result = score_case(case, events)
            self.assertEqual(result.status, "pass", (case_id, result.to_dict()))

    def test_runner_writes_lineage_and_group_level_results(self):
        with tempfile.TemporaryDirectory(dir=str(Path.cwd())) as directory:
            result = run_suite(MemoryControllerAgent("fixture", FakeBackend(), directory), self.cases, directory, run_id="innovation-fixture", seed=42)
        self.assertEqual(result["evidence_schema_version"], 2)
        self.assertEqual(result["evidence_chain"]["link_coverage"], 1.0)
        groups = {item["group_id"]: item for item in result["metamorphic_groups"]}
        self.assertTrue(groups["path-update"]["passed"])
        self.assertTrue(groups["wording-invariance"]["passed"])
        self.assertTrue(groups["scope-isolation"]["passed"])
        self.assertTrue(groups["similar-entity-no-confusion"]["passed"])
        self.assertTrue(groups["token-boundary"]["passed"])


if __name__ == "__main__":
    unittest.main()
