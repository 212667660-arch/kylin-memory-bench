import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kmb.agent_adapters.base import AgentCommandError, classify_error, preflight_command
from kmb.agents import AgentAdapter, ReferenceAgent
from kmb.models import BenchmarkCase, EvidenceEvent
from kmb.agent_registry import AgentProfile
from kmb.quick_compare import QuickCompareOptions, run_quick_compare


def _profile(agent_id):
    return AgentProfile(
        id=agent_id,
        display_name=agent_id.title(),
        installed=True,
        runnable=True,
        adapter=agent_id,
        evidence_mode="agent_memory_observed",
        memory_paths=["~/.%s/state.db" % agent_id],
        capabilities=["retention", "memory_recall", "dynamic_update", "similar_distinction", "boundary", "task_reuse"],
        reason="fixture",
    )
from kmb.scoring import score_case


class ErrorBoundaryTests(unittest.TestCase):
    def test_error_classifier_separates_provider_failures(self):
        self.assertEqual(classify_error(RuntimeError("402 billing quota exceeded")), "billing_error")
        self.assertEqual(
            classify_error(RuntimeError("API key has insufficient balance; billing error")),
            "billing_error",
        )
        self.assertEqual(classify_error(RuntimeError("401 invalid API key")), "credential_error")
        self.assertEqual(classify_error(FileNotFoundError("state.db missing")), "missing_input")
        self.assertEqual(classify_error(TimeoutError("timed out")), "timeout")

    def test_preflight_is_read_only_and_reports_command(self):
        report = preflight_command([sys.executable, "--version"], "test")
        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["executable"], sys.executable)
        self.assertEqual(report["argument_count"], 1)

    def test_missing_action_evidence_is_not_observable(self):
        case = BenchmarkCase.from_dict({
            "id": "action-boundary", "capability": "task_reuse", "title": "action", "turns": [],
            "checks": [{"type": "action_tool", "value": "write_file"}],
        })
        result = score_case(case, [])
        self.assertEqual(result.checks[0].category, "not_observable")
        self.assertEqual(result.failures[0]["category"], "not_observable")

    def test_explicit_unsupported_action_is_not_behavior_failure(self):
        case = BenchmarkCase.from_dict({
            "id": "unsupported-action", "capability": "task_reuse", "title": "action", "turns": [],
            "checks": [{"type": "action_tool", "value": "write_file"}],
        })
        result = score_case(case, [EvidenceEvent("action", {
            "tool": "write_file", "unsupported": True, "executed": False,
        }, 1, source="runner")])
        self.assertEqual(result.checks[0].category, "unsupported_action")

    def test_quick_compare_writes_blocked_preflight(self):
        class BlockedAgent(ReferenceAgent):
            name = "blocked"

            def preflight(self):
                return {"agent": self.name, "status": "blocked", "checks": [], "reason": "billing gate"}

        profiles = [
            _profile("a"),
            _profile("b"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "quick"
            with patch("kmb.quick_compare.discover_agents", return_value=profiles), patch(
                "kmb.quick_compare.adapter_for_profile", return_value=BlockedAgent()
            ):
                with self.assertRaisesRegex(RuntimeError, "preflight failed"):
                    run_quick_compare(QuickCompareOptions(out_dir=str(out)), root=Path.cwd())
            payload = (out / "quick-compare.json").read_text(encoding="utf-8")
            self.assertIn('"status": "blocked"', payload)

    def test_runtime_failure_is_counted_once_and_invalidates_score(self):
        class BillingAgent(AgentAdapter):
            name = "billing"

            def run(self, _case):
                raise AgentCommandError("API key has insufficient balance", category="billing_error")

        case = BenchmarkCase.from_dict({
            "id": "billing", "capability": "retention", "title": "billing",
            "turns": [], "checks": [],
        })
        with tempfile.TemporaryDirectory() as tmp:
            from kmb.runner import run_suite
            result = run_suite(BillingAgent(), [case], tmp)
        self.assertEqual(result["failure_counts"]["billing_error"], 1)
        self.assertEqual(result["error_cases"], 1)
        self.assertFalse(result["score_valid"])


if __name__ == "__main__":
    unittest.main()
