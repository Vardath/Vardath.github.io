"""v14 regression: a large model-proposed plan must not crash revision budgeting.

Tests the failure recorded at 2026-11-21 05:06 UTC in the user's diagnostics.
The model, not the planner, remains responsible for every plan step.
"""
import json
import tempfile
import unittest
from pathlib import Path

from deepthort_local.agent_plan import (PlanError, build_revision_prompt,
                                       build_plan_prompt, generate_model_plan)
from test_model_planning_v13 import ScriptedLocalModel, files
from test_x4_plan_guard import REQUEST, VALID


class RevisionContextV14(unittest.TestCase):
    def test_long_existing_path_manifest_does_not_crash_or_truncate_spec(self):
        request = REQUEST + '\n' + 'Preserve every constraint. ' * 132
        paths = [
            {'path': f'assets/{"nested/" * 12}set_{i:02d}/' + ('m' * 55) + '.xml',
             'description': 'Model-generated file; must be retained in state'}
            for i in range(22)
        ]
        evidence = '\n'.join([
            'PE connection: gun medium slot',
            'ship_candidates: verified vanilla PE asset',
            'weapon_candidates: installed M-class gun',
            'turret_candidates: installed M-class turret',
            'storage_candidates: vanilla PE storage'
        ])
        prompt = build_revision_prompt(request, paths, 'Missing components.xml',
                                       x4_evidence=evidence, max_chars=7500)
        self.assertIn(request, prompt)
        self.assertLessEqual(len(prompt), 7500)
        self.assertIn('omitted from THIS model context', prompt)
        self.assertIn('retained for merging and validation', prompt)
        # Never cut a file path in half to make it fit.
        for step in paths:
            path = step['path']
            self.assertTrue(path not in prompt or path + '\n' in prompt)
        # More context remains in local state and a second pass can see others.
        second = build_revision_prompt(request, paths, 'Missing components.xml',
                                       max_chars=7500, path_window=10)
        self.assertLessEqual(len(second), 7500)
        self.assertIn(request, second)
        self.assertNotEqual(prompt, second)
        self.assertEqual(len(paths), 22)

    def test_evidence_not_at_expense_of_previous_model_paths(self):
        prior = VALID[:2]
        evidence = '\n'.join(f'weapon_candidates: source_{i:02d}/' + ('long' * 95)
                             for i in range(25))
        prompt = build_revision_prompt(REQUEST, prior, 'Missing Mission Director',
                                       x4_evidence=evidence)
        self.assertIn(REQUEST, prompt)
        for step in prior:
            self.assertIn(step['path'], prompt)
        self.assertLessEqual(len(prompt), 7500)

    def test_model_has_opportunity_to_revise_after_oversized_prior_context(self):
        # Large prior paths are deliberately incomplete, so the validator must
        # still pass every model-authored step through the ordinary checks.
        with tempfile.TemporaryDirectory() as directory:
            first = [
                {'path':f'assets/units/size_m/macros/' + 'a' * 160 + f'{i}.xml',
                 'description':'Inspect vanilla PE original ship and component connections'}
                for i in range(5)
            ]
            client = ScriptedLocalModel([files(first), files(VALID)])
            long_request = REQUEST + '\n' + 'Keep all requirements. ' * 125
            response, steps = generate_model_plan(
                client, 'session', long_request, Path(directory),
                build_plan_prompt(long_request), max_rounds=2,
                x4_evidence='PE connection: verified medium gun and turret',
            )
            self.assertEqual(len(client.prompts), 2)
            self.assertIn(long_request, client.prompts[1])
            self.assertLessEqual(len(client.prompts[1]), 7500)
            self.assertTrue(any(s['path'] == 'content.xml' for s in steps))
            self.assertEqual(json.loads(response)['files'], steps)

    def test_genuinely_unfit_full_spec_remains_fail_closed(self):
        with self.assertRaisesRegex(PlanError, 'no specification was truncated'):
            build_revision_prompt('X' * 7400, [], 'Missing source inspection')


if __name__ == '__main__':
    unittest.main()
