"""Regression for 22 Nov v20: 7K prompts kept JSON output stuck at 384 tokens."""
import json
import tempfile
import unittest
from pathlib import Path

from deepthort_local.agent_plan import build_plan_prompt, build_revision_prompt, generate_model_plan, PlanError
from test_x4_plan_guard import VALID, REQUEST

class Model:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = []
    def chat(self, session, prompt, *, max_tokens):
        self.calls.append((session, prompt, max_tokens))
        return next(self.replies)


def valid_steps(items):
    return json.dumps({'files':items})

class JsonRecoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)

    def test_output_budget_escalates_for_long_prompts_and_recovers_valid_plan(self):
        long_request = REQUEST + '\n' + 'Preserve original specifications. '*115
        first = build_plan_prompt(long_request)
        self.assertGreater(len(long_request), 3000)
        self.assertLess(len(first), 7500)
        model = Model([
            '{"files":[{"path":"content.xml","description":"incomplete"}',
            '{"files": [',
            valid_steps(VALID),
        ])
        _, result = generate_model_plan(model,'long-x4',long_request,self.project,first,max_rounds=3)
        self.assertEqual(result, VALID)
        self.assertEqual([call[2] for call in model.calls], [384,640,768])
        self.assertTrue(all(long_request in call[1] for call in model.calls))
        for _, prompt, _ in model.calls[1:]:
            self.assertIn('FORMAT RECOVERY',prompt)
            self.assertIn('ONE file',prompt)
        self.assertEqual(len(model.calls),3)

    def test_valid_partial_plan_resets_malformed_streak(self):
        model = Model([
            '{"files":[',
            valid_steps(VALID[:2]),
            '{"files":[',
            valid_steps(VALID[2:]),
        ])
        _, result=generate_model_plan(model,'partial',REQUEST,self.project,build_plan_prompt(REQUEST),max_rounds=4)
        self.assertEqual(result,VALID)
        self.assertEqual([call[2] for call in model.calls],[384,640,384,640])
        self.assertNotIn('FORMAT RECOVERY',model.calls[2][1])
        self.assertIn('FORMAT RECOVERY',model.calls[3][1])

    def test_unsolved_malformed_plan_cannot_be_approved(self):
        model=Model(['{"files": [','{"files": [','{"files": ['])
        with self.assertRaisesRegex(PlanError,'No substitute plan was created'):
            generate_model_plan(model,'invalid',REQUEST,self.project,build_plan_prompt(REQUEST),max_rounds=3)
        self.assertEqual([call[2] for call in model.calls],[384,640,768])

    def test_recovery_prompt_respects_char_budget_and_preserves_spec(self):
        long_request=REQUEST+'\n'+('Do not omit a user-specified requirement. '*100)
        prompt=build_revision_prompt(long_request, VALID[:2], 'Invalid JSON response',
                     focus='cargo storage increase',format_recovery=True)
        self.assertIn(long_request,prompt)
        self.assertLessEqual(len(prompt),7500)
        self.assertIn('FORMAT RECOVERY',prompt)
        self.assertNotIn('src/main.py',prompt)

if __name__=='__main__': unittest.main()
