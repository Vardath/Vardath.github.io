"""Regression: user rejected a generic src/main.py plan for an X4 PE extension."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local.agent_plan import (PlanError, parse_build_plan, build_plan_prompt, validate_project_plan, project_kind)
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.job_queue import JobStore

REQUEST = '''Create an X4: Foundations player-owned Xenon PE extension; 10x cargo,
50,000 damage per successful hit for forward weapons and turrets, 4x base speed,
better handling, inspect vanilla weapon connectors, and 60 seconds without an owned
ship should respawn it via MD; do not modify NPC ships.'''

VALID = [
 {'path':'content.xml','description':'Register vardath_xenon_pe extension metadata and version for existing saves; inspect vanilla game definitions first'},
 {'path':'assets/units/size_m/macros/vardath_pe.xml','description':'Using inspected vanilla PE ship macro and connections, create player owned PE variant with 10x cargo storage, 4x base speed, better handling and acceleration; preserve NPC PE'},
 {'path':'assets/props/WeaponSystems/macros/vardath_pe_gun.xml','description':'Select fast-firing compatible vanilla forward weapon and create a unique upgraded macro with 50,000 damage per hit; inspect vanilla equipment refs'},
 {'path':'assets/props/WeaponSystems/macros/vardath_pe_turret.xml','description':'Select compatible vanilla turret based on weapon connection map with 50,000 per-hit damage and high firing rate; inspect base PE references'},
 {'path':'md/vardath_pe_ownership.xml','description':'Use Mission Director to check player-owned ship ownership and, if absent, spawn after 60 seconds; cancel when owned; no duplicates after save/load, inspect reference files'},
 {'path':'assets/props/WeaponSystems/bullet/macros/vardath_pe_bullet.xml','description':'Create a unique bullet macro from vanilla M-class projectile references to apply 50,000 per successful hit without modifying other ships'},
 {'path':'index/macros.xml','description':'Register the independently named new PE ship, M-class weapon, M-class turret and bullet macro names against verified installed game resource paths'},
]

class X4PlanGuardTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name);self.project=self.root/'x4mods';self.project.mkdir()
 def test_detect_x4_and_no_generic_example(self):
  self.assertEqual(project_kind(REQUEST),'x4')
  p=build_plan_prompt(REQUEST)
  self.assertIn('Mission Director',p)
  self.assertNotIn('"path":"src/main.py"',p)
  self.assertIn('50,000',p)
 def test_reject_actual_generic_plan(self):
  fake='{"files":[{"path":"src/main.py","description":"Implementation of the entry point"}]}'
  with self.assertRaisesRegex(PlanError,'X4 specification'):
   parse_build_plan(fake,self.project,request=REQUEST)
 def test_valid_x4_specific_plan_and_numeric_coverage(self):
  v=parse_build_plan(json.dumps({'files':VALID}),self.project,request=REQUEST)
  self.assertEqual(v,VALID)
  for idx,word in [(1,'10x'),(3,'50,000'),(4,'60 seconds')]:
   bad=[dict(x) for x in VALID]
   bad[idx]['description']=bad[idx]['description'].replace(word,'ordinary')
   if idx==3:
    for step in bad:step['description']=step['description'].replace('50,000','ordinary')
   with self.assertRaises(PlanError):validate_project_plan(bad,REQUEST)
 def test_rejects_missing_asset_registrations_and_independent_bullet(self):
  for missing_path in ('index/macros.xml','assets/props/WeaponSystems/bullet/macros/vardath_pe_bullet.xml'):
   subset=[step for step in VALID if step['path']!=missing_path]
   with self.subTest(missing_path=missing_path),self.assertRaises(PlanError):
    validate_project_plan(subset,REQUEST)
  new_component={'path':'assets/units/size_m/vardath_pe.xml',
     'description':'Register isolated player PE component with verified vanilla connections'}
  with self.assertRaisesRegex(PlanError,'index/components.xml'):
   validate_project_plan(VALID+[new_component],REQUEST)
  l_class=[dict(step) for step in VALID]
  l_class[2]['description']+=' vanilla weapon_arg_l_destroyer_01_mk1_macro'
  with self.assertRaisesRegex(PlanError,'L/XL-class'):
   validate_project_plan(l_class,REQUEST)

 def test_no_x4_writes_from_generic_plan_even_with_forged_approval_key(self):
  q=JobStore(self.root/'state/jobs.sqlite3')
  with self.assertRaises(PlanError):
   q.submit_approved_build(str(self.project),'chat-1',REQUEST,
    [{'path':'src/main.py','description':'Implementation of entry point'}],'draft:1')
  self.assertEqual(q.items(str(self.project)),[])
 def test_legacy_bad_draft_revoked_but_conversation_preserved(self):
  c=ConversationStore(self.root/'state/conversations.sqlite3')
  n=c.submit('chat-1',str(self.project),'draft_plan',REQUEST)
  draft=c.save_draft(n,[{'path':'src/main.py','description':'Implementation of entry point'}])
  self.assertEqual(c.invalidate_incompatible_drafts(),1)
  self.assertEqual(c.invalidate_incompatible_drafts(),0)
  self.assertEqual(c.draft(draft)['state'],'discarded')
  self.assertIsNotNone(c.get(n))
  self.assertIsNone(c.latest_draft('chat-1',str(self.project)))
 def test_rejection_button_discard_and_keep_queue_empty(self):
  if not (os.name=='nt' or os.environ.get('DISPLAY')): self.skipTest('Tk display unavailable')
  import desktop_app as d
  with patch.object(d,'STATE',self.root/'state'),\
       patch.object(d.DeepThorTDesktop,'_refresh_inventory',lambda self:None),\
       patch.object(d.messagebox,'askyesno',return_value=False),\
       patch.object(d.messagebox,'showerror'),\
       patch.object(d.messagebox,'showinfo'),\
       patch.object(d.messagebox,'showwarning'):
   app=d.DeepThorTDesktop()
   try:
    app._set_project(self.project)
    n=app.conversations.submit(app.current_chat,str(self.project),'draft_plan',REQUEST)
    draft=app.conversations.save_draft(n,VALID)
    self.assertIsNotNone(app.conversations.latest_draft(app.current_chat,str(self.project)))
    app._approve_conversation_plan()
    self.assertEqual(app.conversations.draft(draft)['state'],'discarded')
    self.assertEqual(app.jobs.items(str(self.project)),[])
   finally:app._quit()

if __name__=='__main__':unittest.main()

class X4DraftFailureTests(unittest.TestCase):
 @unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Tk desktop not available')
 def test_model_template_echo_is_rejected_before_draft_creation(self):
  import desktop_app as d
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp); project=root/'mods';project.mkdir()
   with patch.object(d,'STATE',root/'state'),\
        patch.object(d.DeepThorTDesktop,'_refresh_inventory',lambda self:None),\
        patch.object(d.messagebox,'showinfo'),patch.object(d.messagebox,'showwarning'),\
        patch.object(d.messagebox,'showerror'):
    app=d.DeepThorTDesktop()
    try:
     app._set_project(project)
     req=app.conversations.submit(app.current_chat,str(project),'draft_plan',REQUEST)
     app.conversations.change(req,'running','model generating',allowed=('pending',))
     app._conversation_reply(req,json.dumps({'files':[{'path':'src/main.py','description':'Implementation of the entry point'}]}))
     self.assertEqual(app.conversations.get(req)['state'],'failed')
     self.assertIsNone(app.conversations.latest_draft(app.current_chat,str(project)))
     self.assertEqual(app.jobs.items(str(project)),[])
    finally:app._quit()
