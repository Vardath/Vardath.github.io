"""Regression for the 17:22 diagnostics: model answer arrived after 900s.

No ONNX model or network requests are used by these tests. A simulated
interruption proves the already-durable completed model passes are replayed
without another inference, and that changed prompts cannot reuse stale output.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deepthort_local.client import LocalModelClient
from deepthort_local.agent_plan import build_plan_prompt, generate_model_plan, PlanError
from test_model_planning_v13 import files
from test_x4_plan_guard import REQUEST, VALID


class RecordingModel(LocalModelClient):
    def __init__(self, path, answers):
        super().__init__(path)
        self.answers = list(answers)
        self.calls = []
        self.raise_on_call = None

    def chat(self, session_id, prompt, max_tokens=96, *, visible_prompt=None):
        self.calls.append((session_id, prompt))
        if self.raise_on_call == len(self.calls):
            raise TimeoutError('simulated inference timeout')
        if not self.answers:
            raise AssertionError('unexpected fresh inference')
        result = self.answers.pop(0)
        with self._connect() as conn:
            conn.executemany('INSERT INTO messages(session_id,role,content) VALUES(?,?,?)',
                             ((session_id, 'user', prompt),
                              (session_id, 'assistant', result)))
        return result


class InferenceRecoveryV16(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / 'sessions.sqlite3'
        self.project = self.root / 'x4mods'
        self.project.mkdir()

    def plan(self, client, spec=REQUEST, first_prompt=None, max_rounds=4, stage=None):
        return generate_model_plan(
            client, 'plan-15-example', spec, self.project,
            first_prompt or build_plan_prompt(spec),
            max_rounds=max_rounds, stage=stage)

    def test_local_inference_timeout_exceeds_old_fifteen_minute_limit(self):
        client = LocalModelClient(self.db)
        self.assertGreater(client.timeout, 900)
        self.assertLessEqual(client.timeout, 7200)
        with self.assertRaises(ValueError):
            LocalModelClient(self.db, timeout=7201)

    def test_interrupted_plan_reuses_completed_passes_on_restart(self):
        client = RecordingModel(self.db, [files(VALID[:2]), files(VALID[2:4])])
        client.raise_on_call = 3
        with self.assertRaisesRegex(TimeoutError, 'simulated'):
            self.plan(client, max_rounds=4)
        self.assertEqual(len(client.calls), 3)
        self.assertEqual(client.completed_exchange(client.calls[0][0],client.calls[0][1]),
                         files(VALID[:2]))
        # Simulate closing and restarting the desktop; the SQLite record persists.
        fresh = RecordingModel(self.db, [files(VALID[4:])])
        stages = []
        response, steps = self.plan(fresh, max_rounds=4, stage=stages.append)
        self.assertEqual(json.loads(response)['files'], VALID)
        self.assertEqual(steps, VALID)
        self.assertEqual(len(fresh.calls), 1)
        self.assertTrue(fresh.calls[0][0].endswith('-3'))
        self.assertEqual(sum('restored from' in x for x in stages), 2)

    def test_changed_initial_prompt_never_uses_old_response(self):
        client = RecordingModel(self.db, [files(VALID)])
        first = build_plan_prompt(REQUEST)
        self.plan(client, first_prompt=first)
        self.assertIsNotNone(client.completed_exchange('plan-15-example-1',first))
        self.assertIsNone(client.completed_exchange('plan-15-example-1',first+'\\nAdditional verified reference'))
        fresh = RecordingModel(self.db, [files(VALID)])
        self.plan(fresh, first_prompt=first+'\\nAdditional verified reference')
        self.assertEqual(len(fresh.calls), 1)

    def test_failed_planning_does_not_create_approved_draft(self):
        model = RecordingModel(self.db,['not json'])
        with self.assertRaises(PlanError):
            self.plan(model, max_rounds=1)
        self.assertEqual(len(model.calls),1)
        self.assertIsNotNone(model.completed_exchange(model.calls[0][0],model.calls[0][1]))

    def test_complete_exchange_requires_matching_exact_input_pair(self):
        c = LocalModelClient(self.db)
        with c._connect() as conn:
            conn.execute("INSERT INTO messages(session_id,role,content) VALUES('partial','user','prompt')")
        self.assertIsNone(c.completed_exchange('partial','prompt'))
        with c._connect() as conn:
            conn.execute("INSERT INTO messages(session_id,role,content) VALUES('partial','assistant','result')")
        self.assertEqual(c.completed_exchange('partial','prompt'),'result')
        self.assertIsNone(c.completed_exchange('partial','different prompt'))

if __name__ == '__main__':
    unittest.main()
