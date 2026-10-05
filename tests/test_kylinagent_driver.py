import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from kylinagent_driver import map_case_to_events  # noqa: E402


def _turn_result(messages, final_response=""):
    return {"final_response": final_response, "messages": messages}


def _memory_tool_result(count, snippet=""):
    results = [{"session_id": "s1", "snippet": snippet}] if count else []
    return {"success": True, "mode": "discover", "query": "q", "results": results, "count": count}


class KylinAgentDriverMappingTests(unittest.TestCase):
    CASE = {"id": "native-test-001", "turns": [{"user": "u1"}, {"user": "u2"}]}

    def test_plain_answer_turn_emits_user_and_assistant_events(self):
        turns = [_turn_result([
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "My project is Atlas."},
        ]), {}]
        events = map_case_to_events(self.CASE, turns)
        kinds = [(e["kind"], e["source"]) for e in events]
        self.assertIn(("user_message", "runner"), kinds)
        self.assertIn(("assistant_message", "model"), kinds)
        self.assertTrue(all(e["data"].get("native_memory_events") is None for e in events))

    def test_memory_tool_call_maps_to_memory_recall_with_hit_and_snippet(self):
        turns = [_turn_result([
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "c1", "function": {"name": "memory", "arguments": json.dumps({"query": "timezone"})}},
            ]},
            {"role": "tool", "tool_name": "memory", "content": json.dumps(
                _memory_tool_result(1, snippet="... my timezone is Asia/Shanghai ..."))},
            {"role": "assistant", "content": "Asia/Shanghai"},
        ]), {}]
        events = map_case_to_events(self.CASE, turns)
        recalls = [e for e in events if e["kind"] == "memory_recall"]
        self.assertEqual(len(recalls), 1)
        self.assertEqual(recalls[0]["source"], "memory_layer")
        self.assertEqual(recalls[0]["data"]["key"], "timezone")
        self.assertTrue(recalls[0]["data"]["hit"])
        self.assertIn("Asia/Shanghai", recalls[0]["data"]["value"])

    def test_memory_tool_miss_maps_to_hit_false(self):
        turns = [_turn_result([
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "c1", "function": {"name": "memory", "arguments": json.dumps({"query": "otp"})}},
            ]},
            {"role": "tool", "tool_name": "memory", "content": json.dumps(_memory_tool_result(0))},
            {"role": "assistant", "content": "I don't know."},
        ]), {}]
        events = map_case_to_events(self.CASE, turns)
        recalls = [e for e in events if e["kind"] == "memory_recall"]
        self.assertEqual(len(recalls), 1)
        self.assertFalse(recalls[0]["data"]["hit"])
        self.assertIsNone(recalls[0]["data"]["value"])

    def test_write_file_tool_maps_to_executed_action(self):
        turns = [_turn_result([
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "c1", "function": {"name": "write_file", "arguments": json.dumps(
                    {"path": "/tmp/kmb-native-demo/report.md", "content": "report"})}},
            ]},
            {"role": "tool", "tool_name": "write_file", "content": json.dumps({"success": True})},
            {"role": "assistant", "content": "Report written."},
        ]), {}]
        events = map_case_to_events(self.CASE, turns)
        actions = [e for e in events if e["kind"] == "action" and e["source"] == "model"]
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["data"]["tool"], "write_file")
        self.assertTrue(actions[0]["data"]["executed"])
        self.assertEqual(actions[0]["data"]["exit_code"], 0)
        self.assertEqual(actions[0]["data"]["path"], "/tmp/kmb-native-demo/report.md")

    def test_final_response_fallback_when_stream_has_no_assistant_text(self):
        turns = [_turn_result([
            {"role": "user", "content": "u1"},
        ], final_response="fallback answer")]
        events = map_case_to_events(self.CASE, turns)
        assistants = [e for e in events if e["kind"] == "assistant_message"]
        self.assertEqual(len(assistants), 1)
        self.assertEqual(assistants[0]["data"]["text"], "fallback answer")

    def test_no_memory_write_events_are_ever_emitted(self):
        """KylinAgent 的记忆范式是会话检索——映射层不得伪造键值写事件。"""
        turns = [_turn_result([
            {"role": "user", "content": "Remember project=Atlas"},
            {"role": "assistant", "content": "Noted.", "tool_calls": [
                {"id": "c1", "function": {"name": "memory", "arguments": json.dumps({"query": "remember project Atlas"})}},
            ]},
            {"role": "tool", "tool_name": "memory", "content": json.dumps(_memory_tool_result(0))},
        ]), {}]
        events = map_case_to_events(self.CASE, turns)
        self.assertFalse(any(e["kind"] in ("memory_write", "memory_update", "memory_suppress") for e in events))


if __name__ == "__main__":
    unittest.main()
