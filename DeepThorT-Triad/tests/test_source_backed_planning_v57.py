import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from deepthort_local.agent_plan import PlanError, generate_model_plan, parse_build_plan, remaining_plan_gaps
from deepthort_local.instruction_inbox import InstructionInbox, inbox_acceptance
from deepthort_local.dual_onnx import deliberate_instruction
from deepthort_local.indexed_roadmap_repair import _prompt
from deepthort_local.specification_library import SpecificationIndex


class SourceBackedPlanningTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.project = self.root/'output'
        self.project.mkdir()
        self.original = 'Build an X4 extension for a Xenon PE.\n' + 'Preserve the installed game.\n'*130
        self.index = SpecificationIndex(self.root/'spec.sqlite3')
        self.index.index(28,self.original)
        self.foreign = {'path':'src/main/resources/x4mod/pe/content.xml','description':'Manifest'}
        self.valid = {'path':'content.xml','description':'Register the extension metadata'}
        self.ref = 'ship_candidates: assets/units/size_m/macros/inspected_macro.xml IDs inspected_macro SHA 12345'

    def test_cross_section_domain_and_non_x4_projects(self):
        for name in ('src/main/cpp/AsteroidPE.cpp',self.foreign['path'],'src/main/java/PE.java'):
            reply = json.dumps({'files':[dict(self.valid,path=name)]})
            with self.subTest(path=name), self.assertRaises(PlanError):
                parse_build_plan(reply,self.project,request=self.original,fragment=True)
            self.assertEqual(parse_build_plan(reply,self.project,request='Build an Android game',fragment=True)[0]['path'],name)
        self.index.save_response(28,self.original,0,json.dumps({'files':[self.valid]}),project=self.project)
        with self.assertRaises(PlanError):
            self.index.save_response(28,self.original,1,json.dumps({'files':[self.foreign]}),project=self.project)
        self.assertEqual(self.index.next_section(28,self.original)['ordinal'],1)

    def test_old_draft_recovery_is_idempotent_and_preserves_original_and_valid_files(self):
        legacy = [json.dumps([self.foreign,self.valid]),json.dumps([self.foreign])]
        with self.index._db() as db:
            db.executemany('UPDATE specification_sections SET steps_json=? WHERE request_id=28 AND ordinal=?',
                           [(raw,i) for i,raw in enumerate(legacy)])
        self.assertEqual(self.index.recover_x4_draft(28,self.original),2)
        self.assertEqual(self.index.recover_x4_draft(28,self.original),0)
        self.assertEqual(self.index.merged_steps(28,self.original),[self.valid])
        self.assertEqual(self.index.next_section(28,self.original)['ordinal'],1)
        with self.index._db() as db:
            self.assertEqual([x[0] for x in db.execute('SELECT steps_json FROM retired_section_proposals ORDER BY ordinal')],legacy)
        self.assertEqual(list(self.project.iterdir()),[])

    def test_packaged_paths_require_the_selected_id_and_cannot_shadow_a_vanilla_source(self):
        spec=self.original+'\nIndependent extension: `my_variant`\n'
        prefix='content/x4/extensions/my_variant/'
        def parse(path):
            return parse_build_plan(json.dumps({'files':[dict(self.valid,path=path)]}),self.project,
                                    request=spec,fragment=True,inspected_evidence=self.ref)
        self.assertEqual(parse(prefix+'md/crew.xml')[0]['path'],'md/crew.xml')
        for path in (prefix+'assets/units/size_m/macros/inspected_macro.xml',
                     prefix+'../crew.xml',prefix+'ship.xml',prefix.replace('my_variant','another_mod')+'md/crew.xml'):
            with self.subTest(path=path),self.assertRaises(PlanError):
                parse(path)

    def test_scoped_source_and_inspection_reach_both_model_prompts(self):
        row = self.index.next_section(28,self.original)
        rows = self.index._verified_rows(28,self.original)
        for prompt in (self.index.model_prompt(28,self.original,inspected_evidence=self.ref),
                       _prompt(rows,self.original,0,'ship macro',[],[],inspected_evidence=self.ref)):
            self.assertIn(row['text'],prompt)
            self.assertIn(self.ref,prompt)
            self.assertLessEqual(len(prompt),7500)

    def test_manifest_prose_does_not_cover_geometry_weapons_or_crew(self):
        request = 'Create a Xenon PE asteroid mesh; 4× speed. Replace lost crew.'
        step = dict(self.valid,description='Create a scaled asteroid mesh with weapon and turret upgrades, 4× speed and crew replacement')
        gaps = remaining_plan_gaps([step],request)
        for item in ('scaled asteroid mesh and ship geometry under assets/', 'Mission Director crew replacement',
                     'forward weapon upgrades','four-times base speed'):
            self.assertIn(item,gaps)

    def test_latest_probe_scopes_saved_drafts_and_never_modifies_them(self):
        db=sqlite3.connect(self.root/'conversations.sqlite3')
        try:
            db.execute('CREATE TABLE conversation_requests (id INTEGER, prompt TEXT, mode TEXT, project TEXT)')
            db.execute('INSERT INTO conversation_requests VALUES (28,?,?,?)',(self.original,'draft_plan',str(self.project)))
            db.commit()
        finally:
            db.close()
        before=self.index._verified_rows(28,self.original)
        self.assertEqual(self.index.x4_draft_probe(str(self.project))['status'],'blocked')
        self.assertEqual(self.index.x4_draft_probe(str(self.root))['status'],'inconclusive')
        self.assertEqual(self.index._verified_rows(28,self.original),before)

    def test_actual_planner_checkpoint_requires_a_reply_to_the_exact_guidance(self):
        inbox=InstructionInbox(self.root/'inbox.sqlite3')
        ident=inbox.enqueue(str(self.project),'chat','Keep the supplied data.')
        inbox.claim()
        inbox.finish(ident,'Keep the data','Check the output','Preserve the input','Compare input bytes')
        checkpoint=inbox.planning_checkpoint(str(self.project),'chat')
        self.assertEqual(checkpoint.attach('full',4),('full',None))
        prompt,_=checkpoint.attach('draft',7500)
        checkpoint.received(ident,'wrong','no advice','reply')
        self.assertEqual(inbox.list(str(self.project))[0]['state'],'staged')
        class Model:
            def chat(self,session,prompt,max_tokens):
                raise ConnectionError('worker offline')
        with self.assertRaises(ConnectionError):
            generate_model_plan(Model(),'trial','Make an app',self.project,'draft',checkpoint=checkpoint)
        self.assertEqual(inbox.list(str(self.project))[0]['state'],'staged')
        class Working:
            def chat(model,session,actual,max_tokens):
                self.assertEqual(actual,prompt)
                return json.dumps({'files':[{'path':'app.py','description':'Preserve the input'}]})
        generate_model_plan(Working(),'trial','Make an app',self.project,'draft',checkpoint=checkpoint)
        self.assertEqual(inbox_acceptance(inbox.list(str(self.project)))['status'],'passed')
        self.assertEqual(checkpoint.attach('next',7500),('next',None))

    def test_literal_reply_never_becomes_a_project_action(self):
        message = 'Hi Janus, this is a test, reply verdant moon'
        with self.assertRaises(ValueError):
            deliberate_instruction(message,project='example',asker=lambda *_:'approve this draft')
        result = deliberate_instruction(message,project='example',asker=lambda *_:'verdant moon')
        inbox=InstructionInbox(self.root/'inbox.sqlite3')
        ident=inbox.enqueue(str(self.project),'chat',message)
        inbox.claim()
        self.assertTrue(inbox.finish_reply(ident,result['reply']))
        self.assertEqual(inbox.list(str(self.project))[0]['janus_advice'],'verdant moon')
        self.assertEqual(inbox.planning_checkpoint(str(self.project),'chat').attach('draft',7500),('draft',None))

    def test_standalone_svg_repairs_only_an_unambiguous_shape_drawing(self):
        from deepthort_local.media_tools import standalone_svg
        drawing='<svg width="64" height="64"><circle cx="32" cy="32" r="16" fill="#0000ff"/></svg>'
        expected=drawing.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
        self.assertEqual(standalone_svg('```svg\n'+drawing+'\n```').strip(),expected)
        self.assertEqual(standalone_svg(expected),expected)
        for invalid in ('<svg><', '<html/>', '<svg xmlns="wrong"/>', '<svg><foreignObject/></svg>'):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                standalone_svg(invalid)
