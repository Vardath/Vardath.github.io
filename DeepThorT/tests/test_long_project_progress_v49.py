"""v49: productive long-lived work, not unlimited repetition of failed inference."""
import json
import tempfile
import unittest
from pathlib import Path

from deepthort_local.agent_plan import PlanError, remaining_plan_gaps
from deepthort_local.hierarchical_planning import HierarchicalPlanStore
from deepthort_local.specification_library import SpecificationIndex, generate_indexed_plan
from deepthort_local.indexed_roadmap_repair import MAX_UNPRODUCTIVE_CALLS, _prompt


def proposal(*entries):
    return json.dumps({'files': [{'path': path, 'description': desc}
                                 for path, desc in entries]})


COMPLETE = proposal(
    ('content.xml', 'X4 extension metadata and PE macro references checked against original installed vanilla game'),
    ('md/pe_monitor.xml', 'Mission Director ownership check: player-owned PE ship respawn and full equipment retention'),
    ('libraries/pe_ship.xml', 'X4 ship macro equipment connections, installed vanilla speed and handling, cargo storage, forward weapons, turrets'))


class Model:
    def __init__(self, answers):
        self.answers = iter(answers)
        self.calls = []

    def chat(self, session, prompt, *, max_tokens):
        self.calls.append((session, prompt, max_tokens))
        return next(self.answers)


class LongProjectProgressV49(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.project = self.root / 'x4mods'
        self.project.mkdir()
        self.db = self.root / 'sections.sqlite3'
        self.index = SpecificationIndex(self.db)
        self.hierarchy = HierarchicalPlanStore(self.root / 'hierarchy.sqlite3')
        self.id = 17
        self.chat = 'project-chat'
        self.original = ('Create an X4 Foundations mod for the Xenon PE. Preserve original PE '
                         'ship connections, installed vanilla game references, player-owned '
                         'ownership monitor and respawn; improve cargo, speed, handling, '
                         'weapons and turrets.\n'
                         + ('Keep existing game and save compatibility.\n' * 210))
        self.index.index(self.id, self.original)
        self.assertGreater(self.index.status(self.id, self.original)['sections'], 1)

    def populate_sections(self):
        while row := self.index.next_section(self.id, self.original):
            self.index.save_response(self.id, self.original, row['ordinal'],
                                     proposal((f'docs/section{row["ordinal"]}.txt',
                                               f'Original model plan for section {row["ordinal"]}')),
                                     project=self.project)

    def plan(self, model, **kwargs):
        return generate_indexed_plan(model, self.index, self.id, 'plan-17',
            self.original, self.project, max_rounds=kwargs.pop('max_rounds',40),
            hierarchy=self.hierarchy, chat_id=self.chat, **kwargs)

    def test_review_continues_past_one_call_when_each_section_passes(self):
        count = self.index.status(self.id, self.original)['sections']
        model = Model([proposal((f'docs/section{i}.txt', f'Section {i} source proposal'))
                       for i in range(count)] + [COMPLETE])
        answer, stages = self.plan(model, max_rounds=1, continuous=True)
        self.assertEqual(stages, [])
        self.assertIn('hierarchy_ready', json.loads(answer))
        self.assertGreater(len(model.calls), 2)
        self.assertEqual(self.index.status(self.id, self.original)['pending'], 0)
        self.assertFalse(remaining_plan_gaps(self.index.merged_steps(self.id,self.original), self.original))

    def test_eight_unproductive_calls_pause_and_keep_checkpoint(self):
        self.populate_sections()
        before=self.index.merged_steps(self.id,self.original)
        model=Model(['This is not JSON']*MAX_UNPRODUCTIVE_CALLS)
        with self.assertRaisesRegex(PlanError, 'paused for lack of verified progress'):
            self.plan(model, continuous=True)
        self.assertEqual(len(model.calls), MAX_UNPRODUCTIVE_CALLS)
        self.assertEqual(before, self.index.merged_steps(self.id,self.original))
        status=SpecificationIndex(self.db).roadmap_stall_status(self.id,self.original)
        self.assertEqual(status['unproductive_in_a_row'],MAX_UNPRODUCTIVE_CALLS)
        self.assertEqual(status['recorded_attempts'],MAX_UNPRODUCTIVE_CALLS)
        self.assertIsNone(self.hierarchy.latest_for_chat(self.chat,self.project))
        self.assertEqual(list(self.project.iterdir()), [])
        # Explicit retry with an actually useful model correction is still possible.
        reply,_=self.plan(Model([COMPLETE]), max_rounds=1, continuous=True)
        self.assertIn('hierarchy_ready', json.loads(reply))
        self.assertEqual(self.index.roadmap_stall_status(self.id,self.original)['unproductive_in_a_row'],0)

    def test_additional_file_cannot_open_new_acceptance_gap(self):
        self.populate_sections()
        before=self.index.merged_steps(self.id,self.original)
        with self.assertRaisesRegex(PlanError,'introduce unmet'):
            self.index.merge_model_revision(self.id,self.original,0,
                proposal(('assets/units/size_m/macros/pe_variant_macro.xml',
                          'New PE independent ship macro with original equipment connections')),
                project=self.project)
        self.assertEqual(before,self.index.merged_steps(self.id,self.original))
        # A model-authored dependency pair is safe because the index is present.
        applied=self.index.merge_model_revision(self.id,self.original,0,
            proposal(('assets/units/size_m/macros/pe_variant_macro.xml',
                       'New PE independent ship macro with original equipment connections'),
                      ('index/macros.xml','Register new PE ship macro with X4 index')),
            project=self.project)
        self.assertTrue(applied)

    def test_outcome_audit_requires_exact_reserved_attempt_and_verified_gap_closure(self):
        self.populate_sections()
        serial=self.index.reserve_revision_attempt(self.id,self.original,0,'exact prompt')
        result=self.index.record_revision_outcome(self.id,self.original,serial,
            ['a','b'], ['b'],file_count=5,accepted=True)
        self.assertEqual(result['checks_closed_total'],1)
        self.assertEqual(result['unproductive_in_a_row'],0)
        other=self.index.reserve_revision_attempt(self.id,self.original,0,'different prompt')
        result=self.index.record_revision_outcome(self.id,self.original,other,
            ['b'],['b'],file_count=5,accepted=True)
        self.assertEqual(result['unproductive_in_a_row'],1)
        self.assertEqual(result['checks_closed_total'],1)
        with self.assertRaises(ValueError):
            self.index.record_revision_outcome(self.id,self.original,999,['a'],[],file_count=1,accepted=True)
        self.assertEqual(SpecificationIndex(self.db).roadmap_stall_status(self.id,self.original), result)

    def test_target_prompt_never_drops_original_section(self):
        self.populate_sections()
        rows=self.index._verified_rows(self.id,self.original)
        text=_prompt(rows,self.original,0,'extension metadata (content.xml)',
                     ['extension metadata (content.xml)'],self.index.merged_steps(self.id,self.original))
        self.assertIn(self.original[rows[0][1]:rows[0][2]],text)
        self.assertIn('CHECK TO CLOSE: extension metadata (content.xml)',text)
        self.assertLessEqual(len(text),7500)
        self.assertNotIn('CURRENT GAPS (',text)

if __name__ == '__main__':
    unittest.main()
