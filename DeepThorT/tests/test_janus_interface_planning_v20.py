"""v20: independent JANUS status reporting and truthful, more targeted planning."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deepthort_local.janus_interface import addressed_to_janus, janus_state_reply
from deepthort_local.agent_plan import (
    build_plan_prompt, build_revision_prompt, generate_model_plan,
    remaining_plan_gaps, PlanError,
)
from test_x4_plan_guard import REQUEST, VALID
from test_model_planning_v13 import files, ScriptedLocalModel


class JanusInterfaceTests(unittest.TestCase):
    def test_explicit_addressee_not_unrelated_conversation(self):
        for prompt in ('JANUS, report status', '@Janus: what are you doing?', 'janus why is Qwen busy?'):
            self.assertTrue(addressed_to_janus(prompt), prompt)
        for prompt in ('What is JANUS?', 'Explain JANUS architecture', 'Build an X4 mod', ''):
            self.assertFalse(addressed_to_janus(prompt), prompt)

    def test_local_reply_is_factual_and_read_only(self):
        answer = janus_state_reply(
            'JANUS, stop the model',
            status={'cycle': 17, 'paused': 0, 'last_focus': 'waiting for approval',
                    'last_action': 'observe',
                    'cores_json': json.dumps({'Front': {'focus': 'X4 code', 'posture': 'defer_or_observe'}})},
            goal='Review approved project work',
            sentinel={'state': 'watching', 'detail': 'No stalled process'},
            job_counts={'approved': 1, 'running': 0},
            model_health={'ready': True, 'inference_busy': True},
            latest_action={'label': 'Test mod', 'status': 'approved'},
        )
        for item in ('JANUS LOCAL INTERFACE', 'recorded cycles: 17', 'waiting for approval',
                     'Qwen is occupied', 'Test mod', 'No action was taken'):
            self.assertIn(item, answer)
        self.assertNotIn('I stopped', answer)


class PlannerEfficiencyTests(unittest.TestCase):
    def test_full_original_request_is_retained_in_all_revision_prompts(self):
        lines=['Create the X4 player PE project with verified vanilla game files.']
        lines.extend(f'Additional requirement {i}: equipment, handling and tests.'
                     for i in range(80))
        lines.append('The forward guns and turrets must deal 50,000 damage per hit.')
        lines.append('The ship needs 10x cargo and 4x speed, and a 60-second respawn.')
        spec='\n'.join(lines)
        prompt=build_revision_prompt(spec,[], 'Need cargo storage',focus='ten-times cargo capacity')
        self.assertIn(spec,prompt)
        self.assertIn('PRIMARY TARGET',prompt)
        self.assertLessEqual(len(prompt),7500)
        self.assertIn('ORIGINAL SPECIFICATION (COMPLETE)',prompt)

    def test_small_specs_remain_complete(self):
        prompt=build_revision_prompt(REQUEST,VALID[:2], 'Missing details',
                                     focus='forward weapon upgrades')
        self.assertIn(REQUEST,prompt)
        self.assertIn(VALID[0]['path'],prompt)
        self.assertIn('Register vardath_xenon_pe',prompt)

    def test_model_only_validates_own_plan_and_stops_early(self):
        fake=ScriptedLocalModel([files(VALID[:2]),files(VALID[2:])])
        with tempfile.TemporaryDirectory() as td:
            result,steps=generate_model_plan(fake,'v20',REQUEST,td,build_plan_prompt(REQUEST))
        self.assertEqual(steps,VALID)
        self.assertEqual(len(fake.prompts),2)
        self.assertTrue(all('ORIGINAL SPECIFICATION (COMPLETE)' in p or
                            'USER PROJECT REQUIREMENTS' in p for p in fake.prompts))

    def test_regressive_rewrite_cannot_erase_a_satisfied_requirement(self):
        initial=[dict(VALID[0]),dict(VALID[1])]
        changed=dict(initial[1]); changed['description']='Basic unmodified PE component and connections'
        model=ScriptedLocalModel([files(initial), files([changed])])
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(PlanError,'after 2 attempts'):
                generate_model_plan(model,'regress',REQUEST,td,build_plan_prompt(REQUEST),max_rounds=2)
        self.assertIn('PRIMARY TARGET',model.prompts[-1])

    def test_revision_never_fabricates_file_proposals_after_malformed_reply(self):
        fake=ScriptedLocalModel(['not JSON']*4)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(PlanError,'No substitute plan'):
                generate_model_plan(fake,'bad',REQUEST,td,build_plan_prompt(REQUEST),max_rounds=4)
        self.assertEqual(len(fake.prompts),4)


@unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Tk desktop needed')
class JanusDesktopTests(unittest.TestCase):
    def test_janus_reply_while_model_busy_does_not_touch_model_or_work_queue(self):
        import desktop_app as d
        with tempfile.TemporaryDirectory() as td:
            with patch.object(d,'STATE',Path(td)/'state'), \
                 patch.object(d.DeepThorTDesktop,'_refresh_inventory',lambda self:None), \
                 patch.object(d.DeepThorTDesktop,'_auto_start_if_installed') as start:
                app=d.DeepThorTDesktop()
                try:
                    old=app.conversations.submit(app.current_chat,app._project_key(),
                                                 'chat','Other Qwen request')
                    app.conversations.change(old,'running','Inference running',allowed=('pending',))
                    app.active_conversation=old
                    app.last_server_health={'ready':True,'inference_busy':True}
                    app.input.insert('1.0','JANUS, report current status')
                    app._send()
                    newest=app.conversations.thread(app.current_chat)[-1]
                    self.assertEqual(newest['state'],'responded')
                    self.assertIn('Qwen is occupied',newest['response'])
                    self.assertEqual(app.conversations.get(old)['state'],'running')
                    self.assertEqual(app.jobs.items(app._project_key()),[])
                    start.assert_not_called()
                finally:
                    app._quit()


if __name__=='__main__':unittest.main()
