"""v13 regression: plans must originate in the local model, with bounded repair."""
import json
import tempfile
import unittest
from pathlib import Path

from deepthort_local.agent_plan import (
    PlanError, build_plan_prompt, build_revision_prompt,
    generate_model_plan, parse_build_plan,
)
from test_x4_plan_guard import REQUEST, VALID


class ScriptedLocalModel:
    def __init__(self, replies):
        self.replies=list(replies)
        self.prompts=[]
        self.sessions=[]
    def chat(self, session, prompt, **kwargs):
        self.sessions.append(session)
        self.prompts.append(prompt)
        if not self.replies:
            raise AssertionError('Unplanned model call')
        return self.replies.pop(0)


def files(items):
    return json.dumps({'files': items})


class ModelPlanningV13(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project=Path(self.temp.name)

    def test_model_proposes_and_repairs_incomplete_x4_plan(self):
        client=ScriptedLocalModel([
            files(VALID[:2]),
            files(VALID[2:4]),
            files(VALID[4:]),
        ])
        stages=[]
        response, steps=generate_model_plan(
            client, 'own-plan', REQUEST, self.project,
            build_plan_prompt(REQUEST),
            x4_evidence='PE connection: gun tags weapon medium',
            stage=stages.append)
        self.assertEqual(steps, VALID)
        self.assertEqual(json.loads(response)['files'], VALID)
        self.assertEqual(len(client.sessions), 3)
        self.assertEqual(len(set(client.sessions)), 3)
        self.assertEqual(len(client.prompts), 3)
        self.assertTrue(all(REQUEST in p for p in client.prompts))
        self.assertTrue(all(len(p)<=7500 for p in client.prompts))
        self.assertIn('content.xml', client.prompts[1])
        self.assertIn('PE connection:', client.prompts[1])
        self.assertTrue(any('rejected' in s for s in stages))

    def test_invalid_model_json_is_not_replaced_by_canned_plan(self):
        client=ScriptedLocalModel(['A generic Python project.','not json'])
        with self.assertRaisesRegex(PlanError, 'No substitute plan was created'):
            generate_model_plan(client,'plan',REQUEST,self.project,
                                build_plan_prompt(REQUEST),max_rounds=2)
        self.assertEqual(len(client.prompts),2)
        self.assertIn('valid JSON', client.prompts[1].lower() if False else client.prompts[1])

    def test_invalid_x4_python_template_does_not_poison_repair(self):
        client=ScriptedLocalModel([
            files([{'path':'src/main.py','description':'Implement generic entry point'}]),
            files(VALID)
        ])
        response, steps=generate_model_plan(client,'plan',REQUEST,self.project,
                                           build_plan_prompt(REQUEST),max_rounds=2)
        self.assertEqual(steps, VALID)
        self.assertNotIn('src/main.py', response)

    def test_duplicate_model_path_replaces_its_prior_description(self):
        first=[dict(VALID[0]), dict(VALID[1])]
        outdated=first[1]['description']
        first[1]['description']='Initial vanilla PE variant idea'
        client=ScriptedLocalModel([files(first),files(VALID[1:])])
        answer, steps=generate_model_plan(client,'plan',REQUEST,self.project,
                                          build_plan_prompt(REQUEST),max_rounds=2)
        self.assertEqual(steps, VALID)
        self.assertIn(outdated,answer)
        self.assertEqual(len(steps),len(VALID))

    def test_blocked_plan_from_model_does_not_bypass_validation(self):
        client=ScriptedLocalModel(['{"blocked":"need X4 sources"}'])
        with self.assertRaises(PlanError):
            generate_model_plan(client,'plan',REQUEST,self.project,
                                build_plan_prompt(REQUEST),max_rounds=1)

    def test_revision_prompt_retains_full_user_spec(self):
        request=REQUEST+'\n'+('Never remove an original constraint. '*80)
        text=build_revision_prompt(request, VALID[:2],'Missing Mission Director',
                   x4_evidence='PE connection: gun tags weapon medium')
        self.assertIn(request,text)
        self.assertLessEqual(len(text),7500)
        for step in VALID[:2]:self.assertIn(step['path'],text)

    def test_revision_fails_if_full_original_request_cannot_fit(self):
        with self.assertRaisesRegex(PlanError,'no specification was truncated'):
            build_revision_prompt('X'*7400,[], 'Missing source assets')

    def test_plan_fragments_not_approvable_until_complete(self):
        partial=files(VALID[:2])
        parsed=parse_build_plan(partial,self.project,fragment=True)
        self.assertEqual(parsed, VALID[:2])
        with self.assertRaises(PlanError):
            parse_build_plan(partial,self.project,request=REQUEST)


if __name__=='__main__':unittest.main()

class NoTemplateApprovalRegression(unittest.TestCase):
    def test_old_fallback_draft_cannot_be_approved(self):
        import os
        from unittest.mock import patch
        if not (os.name=='nt' or os.environ.get('DISPLAY')):
            self.skipTest('GUI display required')
        import desktop_app
        with tempfile.TemporaryDirectory() as root:
            project=Path(root)/'mods';project.mkdir()
            with patch.object(desktop_app,'STATE',Path(root)/'state'), \
                 patch.object(desktop_app.DeepThorTDesktop,'_refresh_inventory',lambda self:None), \
                 patch.object(desktop_app.messagebox,'showwarning') as warning:
                ui=desktop_app.DeepThorTDesktop()
                try:
                    ui._set_project(project)
                    request_id=ui.conversations.submit(ui.current_chat,str(project),'draft_plan',REQUEST)
                    ui.conversations.change(request_id,'running','planning',allowed=('pending',))
                    ui.conversations.change(request_id,'responded',
                        'Model proposal rejected; source-grounded fallback draft #3 prepared for approval',
                        response=files(VALID),allowed=('running',))
                    draft=ui.conversations.save_draft(request_id,VALID)
                    ui._approve_conversation_plan()
                    self.assertEqual(ui.conversations.draft(draft)['state'],'discarded')
                    self.assertEqual(ui.jobs.items(str(project)),[])
                    warning.assert_called_once()
                finally:
                    ui._quit()

class GamePlanningValidation(unittest.TestCase):
    GAME='Build Faction Command as a full Android game, with galaxy sector simulation, property management, a map UI, and a verified APK.'
    GOOD=[
        {'path':'settings.gradle.kts','description':'Set up the Android-compatible game build and dependency versions'},
        {'path':'app/src/main/AndroidManifest.xml','description':'Declare Android application entry and permitted lifecycle'},
        {'path':'app/src/main/java/game/Galaxy.kt','description':'Implement galaxy sector simulation and property management gameplay'},
        {'path':'app/src/main/java/game/MapScreen.kt','description':'Implement touch screen map UI and object commands'},
        {'path':'app/src/test/java/game/GalaxyTest.kt','description':'Unit test simulation with deterministic acceptance checks'},
    ]
    def test_generic_readme_is_not_a_complete_android_game(self):
        self.assertEqual(__import__('deepthort_local.agent_plan',fromlist=['project_kind']).project_kind(self.GAME),'android_game')
        with tempfile.TemporaryDirectory() as td,self.assertRaises(PlanError):
            parse_build_plan(files([{'path':'README.md','description':'Document game'}]),td,request=self.GAME)
    def test_model_can_propose_complete_android_game_plan_in_pieces(self):
        client=ScriptedLocalModel([files(self.GOOD[:2]),files(self.GOOD[2:])])
        with tempfile.TemporaryDirectory() as td:
            result,steps=generate_model_plan(client,'game',self.GAME,td,build_plan_prompt(self.GAME),max_rounds=2)
        self.assertEqual(steps,self.GOOD)
        self.assertEqual(len(client.prompts),2)
        self.assertIn('gameplay',client.prompts[0].lower())
        self.assertIn(self.GAME, client.prompts[1])
