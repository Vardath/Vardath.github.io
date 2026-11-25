import hashlib
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from deepthort_local.agent_plan import PlanError
from deepthort_local.engine_acceptance import audit_engine_project
from deepthort_local.specification_library import SpecificationIndex, generate_indexed_plan


class VariantRegistrationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.project = self.root/'staging'
        self.project.mkdir()
        self.reference = self.root/'vanilla'
        self.base = 'assets/units/size_m/macros/base_macro.xml'
        self.source = self.reference/self.base
        self.source.parent.mkdir(parents=True)
        self.data = b'<macros><macro name="base_macro" class="ship_m"><component ref="base_component"/><connections/></macro></macros>'
        self.source.write_bytes(self.data)
        self.vanilla_index = self.reference/'index/macros.xml'
        self.vanilla_index.parent.mkdir()
        self.vanilla_index.write_text(f'<index><entry name="base_macro" value="{self.base[:-4]}"/></index>')
        self.digest = hashlib.sha256(self.data).hexdigest()[:12]
        self.evidence = f'ship_candidates: {self.base} IDs base_macro SHA {self.digest}'
        self.original = 'Create an independent ship variant for X4: Foundations from base_macro.\nExtension ID: test_ship\n'
        self.index = SpecificationIndex(self.root/'index.db')
        self.index.index(1,self.original)
        self.name = 'test_ship_new_macro'
        self.bad = {'path':self.base,'description':'Base ship proposal from inspected source'}

    def collision(self):
        with self.assertRaisesRegex(PlanError,'shadows'):
            self.index.save_response(1,self.original,0,json.dumps({'files':[self.bad]}),
                                     project=self.project,inspected_evidence=self.evidence)

    def pending(self, evidence=None):
        row = self.index.next_section(1,self.original)
        return self.index.pending_variant(1,row,self.original,evidence or self.evidence)

    def resume(self):
        self.collision()
        self.index = SpecificationIndex(self.index.path)
        test = self
        class Model:
            def chat(self, session, prompt, max_tokens):
                test.assertIn('base_macro',prompt)
                test.assertEqual(max_tokens,64)
                return test.name
        with self.assertRaises(PlanError):  # Full project still has requirements.
            generate_indexed_plan(Model(),self.index,1,'resume',self.original,self.project,
                                  inspected_evidence=self.evidence,max_rounds=1)
        return self.index.merged_steps(1,self.original)

    def test_compact_repair_resumes_and_renders_exact_pair_only(self):
        steps = self.resume()
        self.assertEqual(len(steps),2)
        self.assertEqual(list(self.project.iterdir()),[])
        self.assertEqual(self.index.status(1,self.original)['reviewed'],1)
        for step in steps:
            xml = self.index.render_planned_variant(self.project,step['path'],steps,self.reference)
            dest = self.project/step['path']
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(xml,encoding='utf8')
        (self.project/'content.xml').write_text('<content id="test_ship"/>')
        doc = ET.parse(self.project/steps[0]['path']).getroot()
        doc[0].set('name','base_macro')
        self.assertEqual(ET.tostring(doc),ET.tostring(ET.fromstring(self.data)))
        self.assertEqual(self.source.read_bytes(),self.data)
        audit = audit_engine_project(self.project)
        self.assertTrue(audit['accepted'],audit)
        self.assertFalse(audit['acceptance_confirmed'])
        self.assertEqual([o['name'] for o in audit['observations'] if o['code']=='local_macro_binding_verified'],[self.name])
        self.assertIsNone(self.index.render_planned_variant(self.root,steps[0]['path'],steps,self.reference))
        edited = [dict(steps[0], description='Change engines too'),steps[1]]
        self.assertIsNone(self.index.render_planned_variant(self.project,steps[0]['path'],edited,self.reference))
        self.source.write_bytes(self.data+b' ')
        with self.assertRaisesRegex(PlanError,'changed'):
            self.index.render_planned_variant(self.project,steps[0]['path'],steps,self.reference)

    def test_full_vanilla_index_detects_an_unseen_collision_or_moved_base(self):
        steps = self.resume()
        self.vanilla_index.write_text(f'<index><entry name="{self.name}" value="elsewhere"/></index>')
        with self.assertRaisesRegex(PlanError,'already exists'):
            self.index.render_planned_variant(self.project,steps[0]['path'],steps,self.reference)
        self.vanilla_index.write_text('<index><entry name="base_macro" value="misdirected"/></index>')
        with self.assertRaisesRegex(PlanError,'does not resolve'):
            self.index.render_planned_variant(self.project,steps[0]['path'],steps,self.reference)

    def test_ambiguous_or_stale_sources_and_invalid_replies_stay_pending(self):
        with self.assertRaises(PlanError):
            self.index.save_response(1,self.original,0,json.dumps({'files':[self.bad,self.bad]}),
                                     project=self.project,inspected_evidence=self.evidence)
        self.assertIsNone(self.pending())
        self.collision()
        self.assertIsNone(self.pending(self.evidence.replace(self.digest,'0'*12)))
        choice = self.pending()
        for invalid in ('../test_ship_macro','base_macro','TEST_ship_macro','test_ship_new_macro\nother_macro'):
            with self.assertRaises(PlanError):
                choice.proposal(invalid,self.evidence)
        with self.assertRaises(PlanError):
            choice.proposal(self.name,self.evidence+'\nship_candidates: other.xml IDs '+self.name+' SHA '+self.digest)
        for _ in range(2):
            with self.assertRaises(PlanError):
                self.index.save_response(1,self.original,0,'bad',project=self.project,
                                         inspected_evidence=self.evidence,variant=self.pending())
        self.assertIsNone(self.pending())
        self.assertEqual(self.index.merged_steps(1,self.original),[])

    def test_index_name_alone_does_not_register_the_target(self):
        (self.project/'content.xml').write_text('<content id="test_ship"/>')
        asset = self.project/'assets/macros/local.xml'
        asset.parent.mkdir(parents=True)
        asset.write_bytes(self.data)
        idx = self.project/'index/macros.xml'
        idx.parent.mkdir()
        for prefix,sel in [('extensions/test_ship/assets/macros/missing','/index'),
                           ('extensions/other/assets/macros/local','/index'),
                           ('extensions/test_ship/assets/macros/local','/wrong')]:
            idx.write_text(f'<diff><add sel="{sel}"><entry name="base_macro" value="{prefix}"/></add></diff>')
            result = audit_engine_project(self.project)
            self.assertFalse(result['accepted'],result)
            self.assertIn('local_macro_not_indexed',{x['code'] for x in result['issues']})
        idx.write_text('<diff><add sel="/index"><entry name="base_macro" value="assets/macros/local"/></add>'
                       '<remove sel="/index/entry"/></diff>')
        self.assertTrue(audit_engine_project(self.project)['pending'])
