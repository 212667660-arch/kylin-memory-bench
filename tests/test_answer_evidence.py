import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kmb.agent_adapters.base import AgentCommandError, extract_text, invoke_command
from kmb.agent_adapters.openclaw import OpenClawAdapter
from kmb.models import BenchmarkCase, EvidenceEvent
from kmb.runner import load_suite, validate_cases
from kmb.scoring import score_case


class AnswerScopeTests(unittest.TestCase):
    def test_correct_update_does_not_reject_the_initial_confirmation(self):
        case = next(c for c in load_suite('suites/quick.yaml') if c.id == 'quick-update')
        events = [
            EvidenceEvent('memory_write', {'key': 'venue', 'value': 'Room A'}, 1),
            EvidenceEvent('assistant_message', {'text': 'Stored venue Room A'}, 1),
            EvidenceEvent('memory_update', {'key': 'venue', 'value': 'Room B'}, 2),
            EvidenceEvent('assistant_message', {'text': 'Updated venue Room B'}, 2),
            EvidenceEvent('assistant_message', {'text': 'The venue is Room B'}, 3),
        ]
        result = score_case(case, events)
        self.assertEqual(result.score, 1.0)
        self.assertTrue(all(ref['step'] == 3 for ref in result.checks[-1].evidence_refs))

    def test_early_confirmation_cannot_satisfy_a_failed_final_answer(self):
        case = next(c for c in load_suite('suites/quick.yaml') if c.id == 'quick-retention')
        events = [
            EvidenceEvent('assistant_message', {'text': 'Stored project Atlas'}, 1),
            EvidenceEvent('memory_recall', {'key': 'project', 'value': 'Atlas', 'hit': True}, 2),
            EvidenceEvent('assistant_message', {'text': 'I do not know the project'}, 2),
        ]
        self.assertFalse(score_case(case, events).checks[-1].passed)

    def test_missing_final_answer_does_not_fall_back_to_an_earlier_reply(self):
        case = next(c for c in load_suite('suites/quick.yaml') if c.id == 'quick-retention')
        result = score_case(case, [EvidenceEvent('assistant_message', {'text': 'Atlas'}, 1)])
        self.assertFalse(result.checks[-1].passed)

    def test_boundary_exclusion_remains_effective_for_every_round(self):
        case = next(c for c in load_suite('suites/quick.yaml') if c.id == 'quick-boundary')
        result = score_case(case, [
            EvidenceEvent('assistant_message', {'text': 'Your code is 731204'}, 1),
            EvidenceEvent('assistant_message', {'text': 'I did not retain that code'}, 2),
        ])
        self.assertFalse(result.checks[-1].passed)

    def test_explicit_last_scope_can_target_a_boundary_query(self):
        case = BenchmarkCase.from_dict({
            'id': 'scoped-boundary', 'capability': 'boundary', 'title': 'scoped',
            'turns': [{'user': 'first'}, {'user': 'last'}],
            'checks': [{'type': 'answer_not_contains', 'value': 'old', 'answer_scope': 'last'}],
        })
        result = score_case(case, [
            EvidenceEvent('assistant_message', {'text': 'old'}, 1),
            EvidenceEvent('assistant_message', {'text': 'new'}, 2),
        ])
        self.assertTrue(result.checks[0].passed)

    def test_explicit_step_and_all_scope_have_distinct_meanings(self):
        case = BenchmarkCase.from_dict({
            'id': 'scoped', 'capability': 'retention', 'title': 'scoped',
            'turns': [{'user': 'first'}, {'user': 'last'}],
            'checks': [
                {'type': 'answer_contains', 'value': 'early', 'step': 1},
                {'type': 'answer_not_contains', 'value': 'early', 'answer_scope': 'all'},
            ],
        })
        result = score_case(case, [
            EvidenceEvent('assistant_message', {'text': 'early'}, 1),
            EvidenceEvent('assistant_message', {'text': 'final'}, 2),
        ])
        self.assertTrue(result.checks[0].passed)
        self.assertFalse(result.checks[1].passed)
        self.assertEqual([ref['step'] for ref in result.checks[0].evidence_refs], [1])

    def test_invalid_answer_selectors_are_rejected(self):
        for selector in ({'step': 0}, {'step': True}, {'step': '2'}, {'step': 3},
                         {'answer_scope': 'latest-ish'}, {'step': 1, 'answer_scope': 'all'}):
            with self.subTest(selector=selector):
                case = BenchmarkCase.from_dict({
                    'id': 'invalid-selector', 'capability': 'retention', 'title': 'invalid',
                    'turns': [{'user': 'first'}, {'user': 'last'}],
                    'checks': [{'type': 'answer_contains', 'value': 'x', **selector}],
                })
                with self.assertRaises(ValueError):
                    validate_cases([case])

    def test_legacy_cases_without_turns_use_latest_observed_turn(self):
        case = BenchmarkCase.from_dict({
            'id': 'legacy', 'capability': 'retention', 'title': 'legacy', 'turns': [],
            'checks': [{'type': 'answer_contains', 'value': 'early'}],
        })
        result = score_case(case, [
            EvidenceEvent('assistant_message', {'text': 'early'}, 1),
            EvidenceEvent('assistant_message', {'text': 'final'}, 2),
        ])
        self.assertFalse(result.checks[0].passed)


class CliAnswerTests(unittest.TestCase):
    def test_openclaw_payload_is_selected_instead_of_tool_metadata(self):
        raw = json.dumps({'result': {'payloads': [{'text': 'Room B'}]}, 'meta': {'tool': 'edit'}})
        self.assertEqual(extract_text(raw), 'Room B')

    def test_pretty_json_and_log_prefix_are_supported(self):
        raw = json.dumps({'result': {'payloads': [{'text': 'Room B'}]}, 'meta': {'model': 'ignored'}}, indent=2)
        self.assertEqual(extract_text(raw), 'Room B')
        self.assertEqual(extract_text('Starting agent\n' + raw), 'Room B')

    def test_jsonl_ignores_user_tool_and_log_records(self):
        raw = '\n'.join(json.dumps(item) for item in [
            {'role': 'user', 'content': 'prompt'},
            {'role': 'assistant', 'content': 'answer'},
            {'role': 'tool', 'content': 'tool result'},
            {'level': 'info', 'message': 'finished'},
            {'meta': {'tool': 'edit'}},
        ])
        self.assertEqual(extract_text(raw), 'answer')

    def test_response_chunks_are_kept_in_order_without_tool_blocks(self):
        raw = json.dumps({'result': {'payloads': [
            {'text': 'first'}, {'role': 'tool', 'text': 'ignore'}, {'text': 'second'},
        ]}})
        self.assertEqual(extract_text(raw), 'first\nsecond')

    def test_openai_style_assistant_message_is_supported(self):
        self.assertEqual(extract_text(json.dumps({'choices': [
            {'message': {'role': 'assistant', 'content': 'answer'}}
        ], 'meta': {'model': 'not-an-answer'}})), 'answer')

    def test_metadata_or_malformed_json_cannot_become_an_answer(self):
        for raw in ('{"meta":{"tool":"edit"}}', '{"result":{"payloads":[]}}',
                    '{"role":"tool","text":"tool-result"}', '{"result":'):
            with self.subTest(raw=raw):
                self.assertEqual(extract_text(raw), '')

    def test_plain_text_remains_supported(self):
        self.assertEqual(extract_text('The venue is Room B\n'), 'The venue is Room B')

    def test_successful_large_stdout_is_not_truncated_before_json_parsing(self):
        command = [sys.executable, '-c',
                   "import json; print(json.dumps({'result': {'payloads': [{'text': 'answer'}]}, 'meta': {'padding': 'x' * 20000}}))"]
        raw = invoke_command(command, 10)
        self.assertEqual(extract_text(raw), 'answer')
        self.assertGreater(len(raw), 20000)

    def test_command_errors_keep_bounded_diagnostics(self):
        with self.assertRaises(AgentCommandError) as caught:
            invoke_command([sys.executable, '-c', "import sys; print('x' * 20000); sys.exit(3)"], 10)
        self.assertLessEqual(len(caught.exception.stdout_tail), 8192)

    def test_openclaw_missing_assistant_payload_is_not_observable(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            memory = home / '.openclaw/workspace/USER.md'
            memory.parent.mkdir(parents=True)
            memory.write_text('', encoding='utf-8')
            case = BenchmarkCase.from_dict({
                'id': 'empty-output', 'capability': 'retention', 'title': 'empty',
                'turns': [{'user': 'query'}], 'checks': [],
            })
            with patch('kmb.agent_adapters.openclaw.invoke_command', return_value='{"meta":{"tool":"edit"}}'):
                with self.assertRaises(AgentCommandError) as caught:
                    OpenClawAdapter(home=home).run(case)
            self.assertEqual(caught.exception.category, 'not_observable')


if __name__ == '__main__':
    unittest.main()
