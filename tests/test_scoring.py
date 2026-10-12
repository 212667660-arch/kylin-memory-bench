import unittest
import tempfile
from pathlib import Path

from kmb.models import BenchmarkCase, EvidenceEvent
from kmb.runner import load_suite
from kmb.scoring import score_case


class ScoringTests(unittest.TestCase):
    def test_export_path_update_then_reuse_accepts_correct_state_history(self):
        from kmb.agents import ReferenceAgent

        case = next(case for case in load_suite("suites/adversarial/extended.yaml")
                    if case.id == "cross-task-002-export-new")
        events = ReferenceAgent().run(case)
        self.assertEqual(score_case(case, events).score, 1.0)
        for event in events:
            if event.kind == "action":
                event.data["path"] = "/tmp/kmb-export-old"
        self.assertLess(score_case(case, events).score, 1.0)

    def test_update_requires_new_value_and_rejects_old_value(self):
        case = BenchmarkCase.from_dict({
            "id": "u1",
            "capability": "dynamic_update",
            "title": "update",
            "turns": [],
            "checks": [
                {"type": "answer_contains", "value": "new"},
                {"type": "answer_not_contains", "value": "old"},
            ],
        })
        events = [EvidenceEvent("assistant_message", {"text": "new"}, 1)]
        result = score_case(case, events)
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.score, 1.0)

    def test_missing_evidence_is_explained(self):
        case = BenchmarkCase.from_dict({
            "id": "r1",
            "capability": "memory_recall",
            "title": "recall",
            "turns": [],
            "checks": [{"type": "memory_recall", "key": "project"}],
        })
        result = score_case(case, [])
        self.assertEqual(result.status, "fail")
        self.assertIn("memory_recall", result.failures[0]["reason"])

    def test_suite_loader_accepts_top_level_case_list(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.yaml"
            path.write_text(
                "- id: list-1\n  capability: retention\n  title: list\n  turns: []\n  checks: []\n",
                encoding="utf-8",
            )
            self.assertEqual(load_suite(str(path))[0].id, "list-1")

    def test_forbidden_answer_check_requires_an_answer_event(self):
        case = BenchmarkCase.from_dict({
            "id": "empty-answer",
            "capability": "boundary",
            "title": "empty",
            "turns": [],
            "checks": [{"type": "answer_not_contains", "value": "secret"}],
        })
        result = score_case(case, [])
        self.assertEqual(result.status, "fail")

    def test_score_keeps_evidence_references_for_each_check(self):
        case = BenchmarkCase.from_dict({
            "id": "evidence-ref",
            "capability": "memory_recall",
            "title": "evidence",
            "turns": [],
            "checks": [{"type": "memory_recall", "key": "project", "value": "Atlas"}],
        })
        events = [EvidenceEvent("memory_recall", {"key": "project", "value": "Atlas", "hit": True}, 2)]
        result = score_case(case, events)
        self.assertEqual(result.checks[0].evidence_refs, [{"kind": "memory_recall", "step": 2}])

    def test_state_sequence_check_validates_write_update_reuse_order(self):
        case = BenchmarkCase.from_dict({
            "id": "state-sequence",
            "capability": "task_reuse",
            "title": "state",
            "turns": [],
            "checks": [{"type": "state_sequence", "key": "output_dir", "value": ["write", "reuse"]}],
        })
        events = [
            EvidenceEvent("memory_write", {"key": "output_dir", "value": "/tmp/x"}, 1),
            EvidenceEvent("action", {"source_key": "output_dir", "path": "/tmp/x"}, 2),
        ]
        result = score_case(case, events)
        self.assertEqual(result.status, "pass")

    def test_state_sequence_tracks_suppress(self):
        case = BenchmarkCase.from_dict({
            "id": "state-suppress",
            "capability": "boundary",
            "title": "state",
            "turns": [],
            "checks": [{"type": "state_sequence", "key": "otp", "value": ["suppress"]}],
        })
        events = [EvidenceEvent("memory_suppress", {"key": "otp", "persist": False}, 1)]
        self.assertEqual(score_case(case, events).status, "pass")

    def test_blocked_action_tool_does_not_count_as_execution(self):
        case = BenchmarkCase.from_dict({
            "id": "blocked-action", "capability": "task_reuse", "title": "blocked", "turns": [],
            "checks": [{"type": "action_tool", "value": "write_file"}],
        })
        result = score_case(case, [EvidenceEvent("action", {
            "tool": "write_file", "blocked": True, "executed": False,
        }, 1, source="runner")])
        self.assertFalse(result.checks[0].passed)
        self.assertEqual(result.checks[0].failure_type, "erroneous_reuse")

    def test_unverified_model_tool_request_does_not_count_as_execution(self):
        case = BenchmarkCase.from_dict({
            "id": "requested-action", "capability": "task_reuse", "title": "requested", "turns": [],
            "checks": [{"type": "action_tool", "value": "write_file"}],
        })
        result = score_case(case, [EvidenceEvent("action", {"tool": "write_file"}, 1, source="model")])
        self.assertFalse(result.checks[0].passed)

    def test_evidence_reference_includes_provenance_when_available(self):
        case = BenchmarkCase.from_dict({
            "id": "provenance-ref", "capability": "memory_recall", "title": "provenance",
            "turns": [], "checks": [{"type": "memory_recall", "key": "project", "value": "Atlas"}],
        })
        events = [EvidenceEvent("memory_recall", {"key": "project", "value": "Atlas", "hit": True}, 2, source="wrapper")]
        refs = score_case(case, events).checks[0].evidence_refs
        self.assertEqual(refs[0]["source"], "wrapper")
        self.assertEqual(refs[0]["evidence_class"], "wrapper_operation")


if __name__ == "__main__":
    unittest.main()
