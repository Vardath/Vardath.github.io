"""Regression for 2026-11-21 15:57 diagnostics: four attempts are insufficient.

Use scripted local-model replies only. A passing test proves planner control
flow, not real ONNX model intelligence or that the Xenon PE mod runs in X4.
"""
import inspect
import json
import tempfile
import unittest
from pathlib import Path

from deepthort_local.agent_plan import (
    MAX_PLAN_ATTEMPTS, PlanError, build_plan_prompt, generate_model_plan,
)
from test_model_planning_v13 import ScriptedLocalModel, files
from test_x4_plan_guard import REQUEST, VALID


class PlanningAttemptsV15(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)

    def run_plan(self, model, *, rounds=None, stage=None):
        kwargs = {'stage': stage} if stage else {}
        if rounds is not None:
            kwargs['max_rounds'] = rounds
        return generate_model_plan(
            model, 'forty-pass-test', REQUEST, self.project,
            build_plan_prompt(REQUEST), **kwargs,
        )

    def test_default_allows_forty_failures_and_reports_correct_count(self):
        self.assertEqual(MAX_PLAN_ATTEMPTS, 40)
        model = ScriptedLocalModel(['not-json'] * MAX_PLAN_ATTEMPTS)
        stages = []
        with self.assertRaisesRegex(PlanError, 'after 40 attempts'):
            self.run_plan(model, stage=stages.append)
        self.assertEqual(len(model.prompts), 40)
        self.assertIn('pass 40/40', stages[-1])
        self.assertTrue(all(REQUEST in prompt for prompt in model.prompts))
        self.assertTrue(all(len(prompt) <= 7500 for prompt in model.prompts))
        self.assertTrue(any('repeats an earlier rejected' in s for s in stages))

    def test_success_on_first_pass_stops_without_extras(self):
        model = ScriptedLocalModel([files(VALID)])
        _, steps = self.run_plan(model)
        self.assertEqual(steps, VALID)
        self.assertEqual(len(model.prompts), 1)

    def test_success_on_late_pass_stops_before_forty(self):
        model = ScriptedLocalModel(['not-json'] * 16 + [files(VALID)])
        stages = []
        result, steps = self.run_plan(model, stage=stages.append)
        self.assertEqual(json.loads(result)['files'], VALID)
        self.assertEqual(steps, VALID)
        self.assertEqual(len(model.prompts), 17)
        self.assertIn('pass 17/40', stages[-1])

    def test_oversized_candidate_does_not_poison_future_revisions(self):
        junk = [
            {'path': f'docs/unrelated_{i:02d}.txt',
             'description': 'Unrelated example candidate that cannot repair PE XML'}
            for i in range(20)
        ]
        model = ScriptedLocalModel([
            files(VALID[:6]), files(junk), files(VALID[6:]),
        ])
        result, steps = self.run_plan(model, rounds=3)
        self.assertEqual(json.loads(result)['files'], VALID)
        self.assertEqual(steps, VALID)
        self.assertEqual(len(model.prompts), 3)

    def test_desktop_uses_same_forty_attempt_budget(self):
        import desktop_app
        source = inspect.getsource(desktop_app.DeepThorTDesktop._execute_conversation)
        self.assertIn('max_rounds=MAX_PLAN_ATTEMPTS', source)
        self.assertEqual(desktop_app.MAX_PLAN_ATTEMPTS, 40)


if __name__ == '__main__':
    unittest.main()
