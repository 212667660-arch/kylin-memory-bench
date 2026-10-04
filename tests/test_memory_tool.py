# -*- coding: utf-8 -*-
"""Unit tests for B-track memory modules and MemoryToolAgent (offline)."""
from __future__ import annotations

import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from kmb.agents import DecisionTextBackend, MemoryToolAgent, OpenAICompatibleAgent, OpenAICompatibleToolBackend, build_agent_from_config
from kmb.memory_modules import ExactKVMemory, SimilarityMemory, looks_persist_refusal
from kmb.models import BenchmarkCase
from kmb.runner import load_suite
from scripts.export_kylinbot_evidence import export_case


class MemoryModuleTests(unittest.TestCase):
    def test_kv_write_recall_update(self):
        mem = ExactKVMemory()
        r = mem.save("project", "Atlas", persist=True, context="Remember project=Atlas")
        self.assertTrue(r.applied)
        self.assertEqual(mem.recall("project"), (True, "Atlas"))
        r2 = mem.update("project", "Borealis")
        self.assertTrue(r2.applied)
        self.assertEqual(r2.old_value, "Atlas")
        self.assertEqual(mem.recall("project"), (True, "Borealis"))

    def test_similar_refuses_sensitive(self):
        mem = SimilarityMemory()
        self.assertFalse(mem.save("otp", "731204", persist=True, context="one-time code").applied)
        self.assertFalse(mem.save("api_token", "tok_live_demo", persist=True, context="temporary").applied)
        self.assertTrue(mem.save("project", "Atlas", persist=True, context="Remember project=Atlas").applied)

    def test_looks_persist_refusal(self):
        self.assertIsNotNone(looks_persist_refusal("otp", "123456", "one-time"))
        self.assertIsNone(looks_persist_refusal("project", "Atlas", "remember"))


class MemoryToolAgentTests(unittest.TestCase):
    def _case(self, turns):
        return BenchmarkCase(
            id="native-test-001",
            capability="retention",
            title="t",
            turns=turns,
            checks=[{"type": "memory_recall", "key": "project", "value": "Atlas"}],
        )

    def test_emits_memory_layer_events(self):
        agent = MemoryToolAgent("b-memory-kv", memory_impl="kv")
        events = agent.run(self._case([
            {"user": "Remember project=Atlas"},
            {"user": "What is project?"},
        ]))
        kinds = [e.kind for e in events]
        self.assertIn("memory_write", kinds)
        self.assertIn("memory_recall", kinds)
        write = next(e for e in events if e.kind == "memory_write")
        self.assertEqual(write.source, "memory_layer")
        self.assertTrue(write.data.get("state_observed"))
        recall = next(e for e in events if e.kind == "memory_recall")
        self.assertEqual(recall.data.get("value"), "Atlas")
        for e in events:
            e.to_dict()

    def test_kv_vs_similar_boundary_differs(self):
        turns = [
            {"user": "My one-time code is 731204, do not store it"},
            {"user": "Do you remember my one-time code?"},
        ]
        case = self._case(turns)
        kv_events = MemoryToolAgent("b-memory-kv", memory_impl="kv").run(case)
        sim_events = MemoryToolAgent("b-memory-similar", memory_impl="similar").run(case)
        sim_applied_sensitive = [
            e for e in sim_events
            if e.kind == "memory_write" and ("otp" in str(e.data.get("key","")).lower() or "731204" in str(e.data.get("value")))
        ]
        self.assertFalse(sim_applied_sensitive)
        # KV may persist when save tool fires; similar must not apply sensitive write
        self.assertTrue(any(e.kind in ("memory_write", "memory_suppress", "memory_recall") for e in sim_events))

    def test_config_builds_memory_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "agent-x.yaml"
            cfg.write_text("name: b-memory-kv\ntype: memory_tool\nmemory_impl: kv\n", encoding="utf-8")
            agent = build_agent_from_config(str(cfg))
            self.assertIsInstance(agent, MemoryToolAgent)
            self.assertEqual(agent.memory_kind, "kv")

    def test_native_suite_no_prewrite(self):
        cases = load_suite("suites/native/decision-core.yaml")
        self.assertGreaterEqual(len(cases), 6)
        for case in cases:
            for turn in case.turns:
                self.assertNotIn("memory", turn)

    def test_decision_backend_parses_remember(self):
        backend = DecisionTextBackend()
        calls = backend.plan("Remember project=Atlas", None, 1)
        self.assertTrue(calls and calls[0]["tool"] == "save")

    def test_openai_tool_backend_executes_model_tool_call_then_returns_model_answer(self):
        backend = OpenAICompatibleAgent("fixture", "https://example.invalid/v1", "fixture-model", "KMB_TEST_KEY")
        responses = [
            {"id": "decision-1", "choices": [{"finish_reason": "tool_calls", "message": {
                "content": None,
                "tool_calls": [{"id": "call-1", "type": "function", "function": {"name": "save_memory", "arguments": '{"key":"project","value":"Atlas","persist":true}'}}],
            }}]},
            {"id": "answer-1", "choices": [{"finish_reason": "stop", "message": {"content": "I will remember project Atlas.", "tool_calls": []}}]},
        ]
        with patch.object(backend, "_request", side_effect=responses) as request:
            agent = MemoryToolAgent("b-memory-kv", "kv", OpenAICompatibleToolBackend(backend), action_root=tempfile.mkdtemp())
            events = agent.run(self._case([{"user": "Remember project=Atlas"}]))

        self.assertTrue(any(event.kind == "memory_write" and event.source == "memory_layer" for event in events))
        self.assertTrue(any(event.kind == "assistant_message" and event.source == "model" and "Atlas" in event.data["text"] for event in events))
        self.assertEqual(len(request.call_args_list), 2)
        self.assertIn("tools", request.call_args_list[0].kwargs["extra_options"])
        self.assertEqual(request.call_args_list[1].args[0][-1]["role"], "tool")
    def test_tool_backend_omits_empty_tool_calls_from_history(self):
        """DashScope 系后端拒绝 assistant 消息里的空 tool_calls 数组——历史消息不得携带空列表。"""
        backend = OpenAICompatibleAgent("fixture", "https://example.invalid/v1", "fixture-model", "KMB_TEST_KEY")
        responses = [
            {"id": "d1", "choices": [{"finish_reason": "stop", "message": {"content": "Sure.", "tool_calls": []}}]},
            {"id": "a1", "choices": [{"finish_reason": "stop", "message": {"content": "Nothing stored.", "tool_calls": []}}]},
            {"id": "d2", "choices": [{"finish_reason": "tool_calls", "message": {"content": None, "tool_calls": [
                {"id": "call-2", "type": "function", "function": {"name": "save_memory", "arguments": '{"key":"project","value":"Borealis","persist":true}'}},
            ]}}]},
            {"id": "a2", "choices": [{"finish_reason": "stop", "message": {"content": "Stored Borealis.", "tool_calls": []}}]},
        ]
        with patch.object(backend, "_request", side_effect=responses) as request:
            agent = MemoryToolAgent("b-memory-kv", "kv", OpenAICompatibleToolBackend(backend), action_root=tempfile.mkdtemp())
            agent.run(self._case([{"user": "hello"}, {"user": "Remember project=Borealis"}]))
        for call in request.call_args_list:
            for message in call.args[0]:
                if message.get("role") == "assistant":
                    self.assertNotEqual(message.get("tool_calls"), [], "assistant 历史消息携带空 tool_calls 会被 DashScope 系后端 400 拒绝")


    def test_memory_tool_file_action_is_written_only_inside_configured_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            memory = MemoryToolAgent("b-memory-kv", "kv", action_root=root / "actions")
            events = memory.run(self._case([
                {"user": "Remember output_dir=/etc"},
                {"user": "Create the report using output_dir"},
            ]))
            action = next(event for event in events if event.kind == "action")
            self.assertTrue(action.data["executed"])
            self.assertEqual(action.data["path"], "/etc")
            self.assertTrue(Path(action.data["actual_path"]).is_relative_to(root / "actions"))
            self.assertTrue(Path(action.data["actual_path"]).is_file())


class GateCountingTests(unittest.TestCase):
    def test_agent_owned_process_memory_count(self):
        """A-track gate: count agent-owned memory events, not only model_native_memory."""
        agent = MemoryToolAgent("b-memory-kv", memory_impl="kv")
        events = agent.run(BenchmarkCase(
            id="g1", capability="retention", title="t",
            turns=[{"user": "Remember project=Atlas"}],
            checks=[],
        ))
        agent_owned = [
            e for e in events
            if e.source in ("process", "memory_layer", "wrapper")
            and e.kind in ("memory_write", "memory_update", "memory_recall", "memory_suppress")
        ]
        self.assertGreater(len(agent_owned), 0)


class KylinBotSnapshotExporterTests(unittest.TestCase):
    def test_snapshot_does_not_turn_unrelated_history_into_current_write(self):
        case = {"id": "gate", "turns": [
            {"user": "Remember project=Atlas"},
            {"user": "What is project?"},
        ]}
        memories = [(
            "row-1", "project_codename", "old project value", "core", "2026-09-20", "2026-09-20"
        )]
        events = export_case(case, memories)
        memory_events = [e for e in events if e["kind"].startswith("memory_")]
        self.assertEqual([e["kind"] for e in memory_events], ["memory_recall"])
        self.assertFalse(memory_events[0]["data"]["hit"])

    def test_snapshot_recall_is_marked_as_non_temporal_observation(self):
        case = {"id": "gate", "turns": [{"user": "What is project?"}]}
        memories = [(
            "row-1", "project", "Atlas", "core", "2026-09-20", "2026-09-20"
        )]
        events = export_case(case, memories)
        recall = next(e for e in events if e["kind"] == "memory_recall")
        self.assertTrue(recall["data"]["hit"])
        self.assertTrue(recall["data"]["snapshot_only"])
        self.assertIn("snapshot", recall["data"]["source_note"])


if __name__ == "__main__":
    unittest.main()
