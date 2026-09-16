import unittest
import tempfile
from pathlib import Path

from kmb.agents import AgentAdapter, NoMemoryAgent
from kmb.models import BenchmarkCase, EvidenceEvent
from kmb.runner import run_suite


class FlakyAgent(AgentAdapter):
    name = "flaky"

    def __init__(self):
        self.calls = 0

    def run(self, case):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("transient")
        return [EvidenceEvent("assistant_message", {"text": "ok"}, 1)]


class RunnerTests(unittest.TestCase):
    def test_retry_records_metadata_and_recovers(self):
        case = BenchmarkCase.from_dict({
            "id": "retry", "capability": "retention", "title": "retry",
            "turns": [], "checks": [{"type": "answer_contains", "value": "ok"}],
        })
        result = run_suite(FlakyAgent(), [case], "runs/test-retry", retries=1, run_id="fixed-run", seed=7)
        self.assertEqual(result["run_id"], "fixed-run")
        self.assertEqual(result["seed"], 7)
        self.assertEqual(result["results"][0]["status"], "pass")
        self.assertEqual(result["results"][0]["attempts"], 2)
        self.assertEqual(result["failure_counts"].get("runtime_error"), 1)

    def test_simulated_events_are_not_reported_as_native_memory(self):
        case = BenchmarkCase.from_dict({
            "id": "simulated", "capability": "retention", "title": "simulated",
            "turns": [], "checks": [],
        })

        class SimulatedAgent(AgentAdapter):
            name = "simulated"

            def run(self, _case):
                return [EvidenceEvent("memory_write", {"key": "x", "value": "y"}, 1, source="simulated")]

        with tempfile.TemporaryDirectory(dir=str(Path.cwd())) as directory:
            result = run_suite(SimulatedAgent(), [case], directory)
        self.assertEqual(result["observability"]["mode"], "simulated_baseline")
        self.assertEqual(result["observability"]["native_memory_events"], 0)

    def test_wrapper_events_are_reported_as_system_level(self):
        case = BenchmarkCase.from_dict({
            "id": "wrapper", "capability": "memory_recall", "title": "wrapper",
            "turns": [], "checks": [],
        })

        class WrapperAgent(AgentAdapter):
            name = "wrapper"

            def run(self, _case):
                return [EvidenceEvent("memory_recall", {"key": "x", "value": "y", "hit": True}, 1, source="wrapper")]

        with tempfile.TemporaryDirectory(dir=str(Path.cwd())) as directory:
            result = run_suite(WrapperAgent(), [case], directory)
        self.assertEqual(result["observability"]["mode"], "system_level_wrapper_assisted")
        self.assertEqual(result["observability"]["native_memory_events"], 0)
        self.assertEqual(result["observability"]["wrapper_memory_events"], 1)

    def test_no_memory_baseline_is_reported_and_scored(self):
        class FakeBackend:
            name = "fake-model"
            model = "fake-v1"

            def describe(self):
                return {"adapter": "FakeBackend", "model": self.model}

            def _url(self):
                return "http://mock.local/chat/completions"

            def _request(self, messages):
                return {"id": "mock", "choices": [{"message": {"content": "no memory"}, "finish_reason": "stop"}]}

            def _message(self, response):
                return response["choices"][0]["message"]

            def _tool_events(self, message, step):
                return []

            def _evidence_events(self, case, response, message, step):
                return []

        case = BenchmarkCase.from_dict({
            "id": "no-memory-score", "capability": "memory_recall", "title": "no memory",
            "turns": [
                {"user": "Remember project=Atlas", "memory": {"op": "write", "key": "project", "value": "Atlas", "persist": True}},
                {"user": "What is project?", "query": {"key": "project"}},
            ],
            "checks": [{"type": "memory_recall", "key": "project", "value": "Atlas"}],
        })
        with tempfile.TemporaryDirectory(dir=str(Path.cwd())) as directory:
            result = run_suite(NoMemoryAgent("no-memory", FakeBackend()), [case], directory, run_id="no-memory-run")
        self.assertEqual(result["run_id"], "no-memory-run")
        self.assertEqual(result["observability"]["mode"], "no_memory_baseline")
        self.assertGreater(result["observability"]["memory_disabled_events"], 0)
        self.assertEqual(result["results"][0]["status"], "fail")
        self.assertEqual(result["agent_metadata"]["memory_mode"], "disabled")
