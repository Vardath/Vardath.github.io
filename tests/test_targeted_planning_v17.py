"""v17 regression: 40 expensive passes must target missing criteria, not loop blindly.

Scripted model responses only; passing tests do not establish actual Qwen ability
or prove the X4 extension will run in-game.
"""
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.agent_plan import (
    PlanError, build_plan_prompt, build_revision_prompt, generate_model_plan,
    parse_build_plan, remaining_plan_gaps, planning_focus,
)
from test_model_planning_v13 import ScriptedLocalModel, files
from test_x4_plan_guard import REQUEST, VALID


class TrackingFakeModel(ScriptedLocalModel):
    def __init__(self, replies, db):
        super().__init__(replies)
        self.db = Path(db)


class TargetedPlanningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)

    def test_failed_replies_are_targeted_and_rotated_even_with_zero_steps(self):
        model = TrackingFakeModel(['garbled model output'] * 40,
                                  self.path / 'sessions.sqlite3')
        with self.assertRaisesRegex(PlanError, 'after 40 attempts'):
            generate_model_plan(model, 'target', REQUEST, self.path,
                                build_plan_prompt(REQUEST), max_rounds=40)
        self.assertEqual(len(model.prompts), 40)
        foci = []
        for prompt in model.prompts[1:]:
            self.assertIn(REQUEST, prompt)
            self.assertIn('PRIMARY TARGET FOR THIS PASS', prompt)
            self.assertLessEqual(len(prompt), 7500)
            foci.append(prompt.split('PRIMARY TARGET FOR THIS PASS (a criterion still missing from the accumulated plan): ', 1)[1].split('\n', 1)[0])
        self.assertGreater(len(set(foci)), 3)
        self.assertIn('extension metadata (content.xml)', foci)
        self.assertIn('Mission Director XML (md/*.xml)', foci)
        records = (self.path / 'logs' / 'planner.jsonl').read_text(encoding='utf-8').splitlines()
        self.assertEqual(len(records), 40)
        last = json.loads(records[-1])['data']
        self.assertEqual(last['pass_number'], 40)
        self.assertEqual(last['proposed_file_count'], 0)
        self.assertTrue(last['rejected_duplicate'])
        self.assertGreater(last['remaining_gap_count'], 0)
        self.assertNotIn(REQUEST, '\n'.join(records))

    def test_model_can_generate_a_file_at_a_time_without_canned_substitutions(self):
        model = ScriptedLocalModel([files([item]) for item in VALID])
        answer, plan = generate_model_plan(model, 'small-files', REQUEST, self.path,
                                           build_plan_prompt(REQUEST), max_rounds=9)
        self.assertEqual(plan, VALID)
        self.assertEqual(json.loads(answer)['files'], VALID)
        self.assertEqual(len(model.prompts), len(VALID))
        for prompt in model.prompts:
            self.assertIn(REQUEST, prompt)
        self.assertIn('PRIMARY TARGET', model.prompts[-1])

    def test_valid_json_inside_prose_can_be_parsed_without_inventing_files(self):
        raw = 'Suggested step:\n' + files([VALID[0]]) + '\nThat is one file.'
        self.assertEqual(parse_build_plan(raw, self.path, fragment=True), [VALID[0]])
        with self.assertRaisesRegex(PlanError, 'complete valid JSON'):
            parse_build_plan(raw + '\n' + files([VALID[1]]), self.path, fragment=True)

    def test_malformed_json_remains_rejected_and_not_synthesized(self):
        raw='Here is a plan: {"files":[{"path":"content.xml","description":'
        with self.assertRaises(PlanError):
            parse_build_plan(raw, self.path, fragment=True)

    def test_targets_derive_from_validation_not_hardcoded_replacement(self):
        empty=remaining_plan_gaps([], REQUEST)
        self.assertIn('extension metadata (content.xml)', empty)
        self.assertIn('Mission Director XML (md/*.xml)', empty)
        first=planning_focus([], REQUEST, 2)
        next_=planning_focus([], REQUEST, 3)
        self.assertNotEqual(first,next_)
        self.assertEqual(remaining_plan_gaps(VALID, REQUEST),[])
        for p in (first,next_):
            text=build_revision_prompt(REQUEST,[], 'Model did not return valid JSON',focus=p)
            self.assertIn('PRIMARY TARGET',text)
            self.assertIn(REQUEST,text)
            self.assertNotIn('src/main.py',text)


if __name__=='__main__':unittest.main()
