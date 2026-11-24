"""Preserve reply notices; reject invalid AI plans rather than substituting templates."""
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from deepthort_local.agent_plan import (
    budgeted_file_step_prompt, parse_build_plan, PlanError)

REQUEST=('Create X4 Foundations player owned Xenon PE mod with 10x cargo, '
         '4x speed, improved handling, 50,000 damage per successful weapon '
         'and turret hit, and 60 seconds respawn after loss of ownership. '
         'Inspect actual vanilla components and keep existing save compatibility.')


def verified_report():
    return {
       'ready_for_planning': True, 'pe_macro_verified': True,
       'pe_component_verified': True,
       'pe_component_file': 'assets/units/size_m/ship_xen_m_corvette_02_a.xml',
       'pe_component_connections':[{'name':'gun','tags':'weapon medium'},
                                   {'name':'turret','tags':'turret medium'}],
       'ship_candidates':[{'file':'assets/units/size_m/macros/ship_xen_m_corvette_02_a_macro.xml',
                           'identifiers':['ship_xen_m_corvette_02_a_macro']}],
       'weapon_candidates':[{'file':'assets/props/WeaponSystems/laser/macros/weapon_gen_m_laser_macro.xml',
                            'identifiers':['weapon_gen_m_laser_macro']}],
       'turret_candidates':[{'file':'assets/props/WeaponSystems/turret/macros/turret_gen_m_laser_macro.xml',
                            'identifiers':['turret_gen_m_laser_macro']}],
    }


class SourceGroundedPlanning(unittest.TestCase):
    def test_predefined_fallback_not_imported(self):
        from deepthort_local import agent_plan
        self.assertFalse(hasattr(agent_plan, 'source_grounded_pe_plan'))

    def test_budgeted_code_prompt_preserves_complete_spec_and_existing_file(self):
        full=REQUEST+' extra exact details'*140
        old='<xml><important>preserve me</important></xml>'
        desc='Build player-owned unique ship macro after source inspection. '
        paths=[{'path':f'assets/f{i}.xml','description':'Need verified XML '+('other steps '*30)}
               for i in range(20)]
        prompt=budgeted_file_step_prompt(full,'assets/pe.xml',desc,old,paths,max_chars=7500)
        self.assertLessEqual(len(prompt),7500)
        self.assertIn(full,prompt)
        self.assertIn(desc,prompt)
        self.assertIn(old,prompt)
        self.assertIn('assets/pe.xml',prompt)

    def test_budgeted_code_prompt_fails_closed_if_user_spec_cannot_fit(self):
        with self.assertRaisesRegex(PlanError,'No user requirements were shortened'):
            budgeted_file_step_prompt('important details '*1000,'content.xml',
                                     'keep all details','','[]' if False else [],max_chars=7500)


@unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Tk display required')
class ReplyActivityGui(unittest.TestCase):
    def setUp(self):
        import desktop_app
        self.mod=desktop_app
        self.temp=tempfile.TemporaryDirectory()
        self.project=Path(self.temp.name)/'mods'
        self.project.mkdir()
        self.p1=patch.object(desktop_app,'STATE',Path(self.temp.name)/'state')
        self.p2=patch.object(desktop_app.DeepThorTDesktop,'_refresh_inventory',lambda self:None)
        self.p1.start();self.p2.start()
        self.app=desktop_app.DeepThorTDesktop()
        self.app._set_project(self.project)

    def tearDown(self):
        self.app._quit()
        self.p2.stop();self.p1.stop();self.temp.cleanup()

    def test_waiting_stage_heartbeat_and_no_health_overwrite(self):
        self.app.input.insert('1.0','Hello local model')
        with patch.object(self.app,'_auto_start_if_installed'):
            self.app._send()
        self.assertIn('WAITING FOR REPLY',self.app.reply_notice.get())
        req=self.app.conversations.next_pending()
        self.app.conversations.change(req['id'],'running','Local model processing conversation',allowed=('pending',))
        self.app.active_conversation=req['id']
        self.app.reply_started=time.monotonic()-65
        self.app._set_reply_stage(req['id'],'Waiting for local model inference (response not yet returned)')
        self.assertIn('1m 05s',self.app.reply_notice.get())
        self.assertIn('Waiting for local model',self.app.reply_notice.get())
        self.app.last_server_health={'ready':True,'inference_busy':True,'inference_elapsed_seconds':65}
        self.app._render_reply_notice()
        self.assertIn('generating a response',self.app.reply_notice.get())
        self.app._set_connection_status('AI READY — chat replies run outside the execution queue.')
        self.assertIn('generating a response',self.app.reply_notice.get())
        self.app._set_reply_stage(req['id']+100,'WRONG LATE MESSAGE')
        self.assertNotIn('WRONG',self.app.reply_notice.get())

    def test_invalid_model_answer_never_becomes_a_draft(self):
        req=self.app.conversations.submit(self.app.current_chat,str(self.project),'draft_plan',REQUEST)
        self.app.conversations.change(req,'running','Local model processing conversation',allowed=('pending',))
        self.app.active_conversation=req
        self.app.reply_started=time.monotonic()-2
        self.app.x4_report=verified_report()
        self.app._conversation_reply(req,json.dumps({'files':[
             {'path':'src/main.py','description':'Generate generic Python program'}]}))
        saved=self.app.conversations.get(req)
        self.assertEqual(saved['state'],'failed')
        self.assertIsNone(self.app.conversations.latest_draft(self.app.current_chat,str(self.project)))
        self.assertEqual(self.app.jobs.items(str(self.project)),[])
        self.assertIn('DRAFT FAILED',self.app.reply_notice.get())
        self.assertNotIn('DRAFT IMPLEMENTATION PLAN',self.app.chat_history.get('1.0','end'))

    def test_unverified_source_prevents_salvage_and_shows_failure(self):
        req=self.app.conversations.submit(self.app.current_chat,str(self.project),'draft_plan',REQUEST)
        self.app.conversations.change(req,'running','Local model processing conversation',allowed=('pending',))
        self.app.active_conversation=req
        self.app.reply_started=time.monotonic()-1
        self.app.x4_report={'ready_for_planning':False}
        self.app._conversation_reply(req,'{"files": []}')
        self.assertEqual(self.app.conversations.get(req)['state'],'failed')
        self.assertIn('DRAFT FAILED',self.app.reply_notice.get())
        self.assertEqual(self.app.jobs.items(str(self.project)),[])


if __name__=='__main__':
    unittest.main()
