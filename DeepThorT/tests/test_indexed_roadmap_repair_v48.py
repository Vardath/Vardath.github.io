"""v48: previously indexed X4 drafts must progress, not fail instantly."""
import json
import tempfile
import unittest
from pathlib import Path

from deepthort_local.agent_plan import PlanError, remaining_plan_gaps
from deepthort_local.hierarchical_planning import HierarchicalPlanStore
from deepthort_local.specification_library import SpecificationIndex, generate_indexed_plan
from deepthort_local.indexed_roadmap_repair import _prompt


class FakeModel:
    def __init__(self, replies):
        self.replies=list(replies)
        self.calls=[]
    def chat(self, session, prompt, *, max_tokens):
        self.calls.append((session,prompt,max_tokens))
        if not self.replies:
            raise AssertionError('Unexpected extra inference')
        return self.replies.pop(0)


def planned(items):
    return json.dumps({'files': [{'path': path, 'description': desc}
                                 for path,desc in items]})


CORRECTION=planned([
    ('content.xml','Create X4 extension metadata for Xenon PE based on original installed vanilla game references and ship macro connection mapping'),
    ('md/player_pe.xml','Mission Director XML for Xenon PE player-owned ship ownership check, replacement respawn, and handling of existing equipment'),
    ('libraries/pe_equipment.xml','X4 ship equipment and cargo storage, speed and handling, forward weapon and turret upgrades using inspected vanilla definitions'),
])


class IndexedRepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name); self.project=root/'x4mods';self.project.mkdir()
        self.index=SpecificationIndex(root/'spec.sqlite3')
        self.hierarchy=HierarchicalPlanStore(root/'roadmap.sqlite3')
        self.id=25; self.chat='x4-chat'
        self.original=(
            'Build an X4 Foundations mod for the Xenon PE ship. '
            'Keep the PE connection mapping and vanilla equipment references. '
            'Increase cargo storage, speed and handling, upgrade weapons and turrets, '
            'ensure player-owned ownership monitoring and respawn.\n'
            + 'Important: preserve installed X4 and save compatibility.\n'*145)
        self.index.index(self.id,self.original)
        ordinal=0
        while (row:=self.index.next_section(self.id,self.original)) is not None:
            self.index.save_response(self.id,self.original,row['ordinal'],
                planned([(f'docs/section{ordinal}.txt',f'Unfinished section {ordinal} reference notes')]),
                project=self.project)
            ordinal+=1
        self.assertGreater(ordinal,1)

    def run_plan(self,model,max_rounds=40):
        return generate_indexed_plan(model,self.index,self.id,'plan-25',self.original,self.project,
            chat_id=self.chat,hierarchy=self.hierarchy,max_rounds=max_rounds)

    def test_old_failure_becomes_real_model_correction_and_validated_roadmap(self):
        with self.assertRaisesRegex(PlanError,'Plan does not cover'):
            self.hierarchy.prepare(self.index,self.id,self.original,self.project,chat_id=self.chat)
        model=FakeModel([CORRECTION])
        answer,steps=self.run_plan(model,max_rounds=3)
        self.assertEqual(steps,[])
        self.assertIn('hierarchy_ready',json.loads(answer))
        self.assertEqual(len(model.calls),1)
        self.assertIn('VERBATIM ORIGINAL SOURCE SECTION',model.calls[0][1])
        self.assertEqual(self.index.status(self.id,self.original)['pending'],0)
        complete=self.index.merged_steps(self.id,self.original)
        self.assertFalse(remaining_plan_gaps(complete,self.original))
        self.assertTrue(any(item['path']=='content.xml' for item in complete))
        self.assertIsNotNone(self.hierarchy.latest_for_chat(self.chat,self.project))

    def test_unfinished_corrections_persist_across_retry_without_restarting_sections(self):
        incomplete=planned([('content.xml','X4 extension metadata, installed vanilla PE macro connection map')])
        first=FakeModel([incomplete])
        with self.assertRaisesRegex(PlanError,'corrections are saved'):
            self.run_plan(first,max_rounds=1)
        self.assertEqual(self.index.status(self.id,self.original)['pending'],0)
        self.assertIn('content.xml',{x['path'] for x in self.index.merged_steps(self.id,self.original)})
        second=FakeModel([CORRECTION]); answer,_=self.run_plan(second,max_rounds=2)
        self.assertIn('hierarchy_ready',json.loads(answer))
        self.assertNotEqual(first.calls[0][0],second.calls[0][0])

    def test_malformed_invalid_and_duplicate_revisions_do_not_authorize(self):
        before=self.index.merged_steps(self.id,self.original)
        ordinal=0
        with self.assertRaises(PlanError):
            self.index.merge_model_revision(self.id,self.original,ordinal,'{"files":[',project=self.project)
        with self.assertRaises(PlanError):
            self.index.merge_model_revision(self.id,self.original,ordinal,
                planned([('../outside.xml','escape')]),project=self.project)
        with self.assertRaises(PlanError):
            self.index.merge_model_revision(self.id,self.original,ordinal,
                planned([('run.py','Generic Python app')]),project=self.project)
        self.assertEqual(self.index.merged_steps(self.id,self.original),before)
        self.assertIsNone(self.hierarchy.latest_for_chat(self.chat,self.project))

    def test_different_original_cannot_reuse_revision_state(self):
        self.index.merge_model_revision(self.id,self.original,0,CORRECTION,project=self.project)
        with self.assertRaisesRegex(ValueError,'changed'):
            self.index.merge_model_revision(self.id,self.original+' altered',0,CORRECTION,project=self.project)

    def test_repeated_bad_model_reply_has_new_durable_attempt_id(self):
        model=FakeModel(['not json','not json'])
        with self.assertRaisesRegex(PlanError,'corrections are saved'):
            self.run_plan(model,max_rounds=2)
        self.assertEqual(len(model.calls),2)
        self.assertNotEqual(model.calls[0][0],model.calls[1][0])
        self.assertIsNone(self.hierarchy.latest_for_chat(self.chat,self.project))
        self.assertEqual(self.index.status(self.id,self.original)['pending'],0)

    def test_repeating_another_sections_file_does_not_duplicate_scope(self):
        before=self.index._verified_rows(self.id,self.original)
        other=json.loads(before[1][5])[0]
        self.assertFalse(self.index.merge_model_revision(self.id,self.original,0,
            json.dumps({'files':[other]}),project=self.project))
        self.assertEqual(self.index._verified_rows(self.id,self.original),before)

    def test_prompt_contains_complete_selected_source_section(self):
        rows=self.index._verified_rows(self.id,self.original)
        prompt=_prompt(rows,self.original,0,'extension metadata (content.xml)',
                       ['extension metadata (content.xml)'],self.index.merged_steps(self.id,self.original))
        self.assertIn(self.original[rows[0][1]:rows[0][2]],prompt)
        self.assertLessEqual(len(prompt),7500)
        self.assertNotIn('no work was queued.',' '.join(x['path'] for x in self.index.merged_steps(self.id,self.original)))

if __name__=='__main__':unittest.main()
