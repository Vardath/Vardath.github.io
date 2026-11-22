"""Initial X4 request discovers local sources and preserves approval boundaries."""
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local.x4_sources import (
    automatic_x4_preflight, is_x4_inspection_request,
    x4_request_in_context,
)
from deepthort_local.conversation_workflow import ConversationStore


class X4InitialInspectionTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.project=self.root/'x4mods';self.project.mkdir()
        self.app_root=self.root/'deepthort';self.app_root.mkdir()
        self.game=self.root/'SteamLibrary'/'steamapps'/'common'/'X4 Foundations'
        self.game.mkdir(parents=True)
        (self.game/'X4.exe').write_bytes(b'game')
        (self.game/'01.cat').write_text('ship_xen_m_corvette_02_a_macro.xml 0 80')
        (self.game/'01.dat').write_bytes(b'cat')
        (self.project/'notes.txt').write_text('local project')
        self.refs=self.app_root/'reference'/'x4'

    def create_references(self):
        a=self.refs/'assets'/'units'/'size_m'
        (a/'macros').mkdir(parents=True,exist_ok=True)
        (a/'macros'/'ship_xen_m_corvette_02_a_macro.xml').write_text('''<macros><macro name="ship_xen_m_corvette_02_a_macro"><component ref="ship_xen_m_corvette_02_a"/></macro></macros>''')
        (a/'ship_xen_m_corvette_02_a.xml').write_text('''<components><component name="ship_xen_m_corvette_02_a"><connections><connection name="gun" tags="weapon medium"/><connection name="turret" tags="turret medium"/></connections></component></components>''')
        w=self.refs/'assets'/'props'/'WeaponSystems'
        (w/'laser'/'macros').mkdir(parents=True)
        (w/'turret'/'macros').mkdir(parents=True)
        (w/'laser'/'macros'/'weapon_gen_m_laser_macro.xml').write_text('<macros><macro name="weapon_gen_m_laser_macro"/></macros>')
        (w/'turret'/'macros'/'turret_gen_m_laser_macro.xml').write_text('<macros><macro name="turret_gen_m_laser_macro"/></macros>')

    def test_initial_request_inspects_project_and_game_without_user_click(self):
        r=automatic_x4_preflight(project_dir=self.project,app_root=self.app_root,discover_roots=[self.root/'SteamLibrary'])
        self.assertEqual(r['game_dir'],str(self.game.resolve()))
        self.assertIn('notes.txt',r['project_files'])
        self.assertEqual(r['catalogs'],['01.cat'])
        self.assertTrue(r['can_offer_extraction'])
        self.assertFalse(r['ready_for_planning'])
        self.assertFalse(self.refs.exists())  # inspection itself did not extract or write

    def test_existing_references_auto_selected_and_evidence_verified(self):
        self.create_references()
        r=automatic_x4_preflight(project_dir=self.project,app_root=self.app_root,game_dir=self.game)
        self.assertTrue(r['ready_for_planning'])
        self.assertEqual(r['reference_dir'],str(self.refs.resolve()))
        self.assertEqual(len(r['pe_component_connections']),2)

    def test_followup_examine_it_inherits_project_context(self):
        self.assertTrue(x4_request_in_context('please examine it',project_dir=self.project))
        self.assertTrue(is_x4_inspection_request('please examine it',x4_context=True))
        self.assertTrue(x4_request_in_context('inspect the relevant files',previous_prompts=['Make an X4 ship']))
        self.assertFalse(x4_request_in_context('hello',project_dir=self.root/'unrelated'))

    def test_interrupted_extraction_is_never_automatically_reexecuted(self):
        store=ConversationStore(self.root/'state'/'conversations.sqlite3')
        ident=store.submit('chat-1',str(self.project),'draft_plan','Create X4 PE extension')
        self.assertTrue(store.change(ident,'running','inspect',allowed=('pending',)))
        self.assertTrue(store.change(ident,'waiting_sources','approved extraction',allowed=('running',)))
        resumed=ConversationStore(self.root/'state'/'conversations.sqlite3')
        self.assertEqual(resumed.get(ident)['state'],'failed')
        self.assertIn('interrupted',resumed.get(ident)['detail'])


@unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'), 'GUI tests require Windows or Xvfb')
class X4AutoGuiTests(X4InitialInspectionTests):
    def _app(self):
        import desktop_app as mod
        patches=[patch.object(mod,'ROOT',self.app_root),
                 patch.object(mod,'STATE',self.app_root/'state'),
                 patch.object(mod.DeepThorTDesktop,'_refresh_inventory',lambda self:None),
                 patch.object(mod.DeepThorTDesktop,'_auto_start_if_installed',lambda self:None),
                 patch.object(mod.messagebox,'showwarning'),
                 patch.object(mod.messagebox,'showerror'),
                 patch.object(mod.messagebox,'showinfo')]
        for p in patches:p.start();self.addCleanup(p.stop)
        app=mod.DeepThorTDesktop();self.addCleanup(lambda:app.winfo_exists() and app._quit())
        app._set_project(self.project)
        app.x4_game_dir=str(self.game)
        return app,mod

    def test_user_initial_plan_prompt_triggers_read_only_inspection_without_ai(self):
        app,_=self._app()
        app.input.insert('1.0','Create an X4 Xenon PE ship mod')
        app._queue_input('plan')
        limit=time.monotonic()+4
        while time.monotonic()<limit and not app.x4_report:
            app._handle_events();time.sleep(.02)
        self.assertIsNotNone(app.x4_report)
        self.assertEqual(app.x4_report['game_dir'],str(self.game.resolve()))
        self.assertFalse(app.x4_report['ready_for_planning'])
        self.assertEqual(app.jobs.items(str(self.project)),[])

    def test_explicit_inspection_gets_local_report_not_model_generated_chat(self):
        self.create_references()
        app,_=self._app()
        req=app.conversations.submit(app.current_chat,str(self.project),'chat','Examine it')
        app.client.chat=lambda *args,**kwargs: (_ for _ in ()).throw(AssertionError('No AI call for local inspection'))
        app._execute_conversation(app.conversations.get(req))
        # Under the combined GUI suite the background preflight can be delayed
        # by other test windows; wait for its actual completion rather than
        # assuming every worker is scheduled within four wall-clock seconds.
        limit=time.monotonic()+12
        while time.monotonic()<limit and app.conversations.get(req)['state']!='responded':
            app._handle_events();time.sleep(.02)
        self.assertEqual(app.conversations.get(req)['state'],'responded')
        self.assertIn('Exact Xenon PE macro: verified',app.conversations.get(req)['response'])
        self.assertEqual(app.jobs.items(str(self.project)),[])

    def test_packed_game_offers_extraction_during_initial_plan_and_waits_for_consent(self):
        self.app_root.joinpath('XRCatTool.exe').write_bytes(b'tool executable stub')
        app,mod=self._app()
        request=app.conversations.submit(app.current_chat,str(self.project),'draft_plan','Build an X4 PE mod')
        app.conversations.change(request,'running','auto inspecting',allowed=('pending',))
        report=automatic_x4_preflight(project_dir=self.project,app_root=self.app_root,game_dir=self.game)
        self.assertFalse(report['ready_for_planning'])
        captured=[]
        with patch.object(mod.messagebox,'askyesno',return_value=True),\
             patch.object(app,'_start_command',lambda cmd,**kw:captured.append((cmd,kw)) or True):
            app._x4_preflight_needs_sources(request,report)
        self.assertEqual(app.conversations.get(request)['state'],'waiting_sources')
        self.assertEqual(len(captured),1)
        self.assertEqual(captured[0][1]['kind'],'x4_preflight_extraction')
        self.assertIn('-include',captured[0][0])
        self.assertEqual(app.jobs.items(str(self.project)),[])
        self.create_references()
        checked=automatic_x4_preflight(project_dir=self.project,app_root=self.app_root,game_dir=self.game)
        app._x4_preflight_extract_checked(request,checked)
        self.assertEqual(app.conversations.get(request)['state'],'pending')

    def test_denial_does_not_queue_or_modify_project(self):
        self.app_root.joinpath('XRCatTool.exe').write_bytes(b'tool executable stub')
        app,mod=self._app()
        request=app.conversations.submit(app.current_chat,str(self.project),'draft_plan','Build X4 PE')
        app.conversations.change(request,'running','auto inspecting',allowed=('pending',))
        report=automatic_x4_preflight(project_dir=self.project,app_root=self.app_root,game_dir=self.game)
        with patch.object(mod.messagebox,'askyesno',return_value=False):
            app._x4_preflight_needs_sources(request,report)
        self.assertEqual(app.conversations.get(request)['state'],'failed')
        self.assertEqual(app.jobs.items(str(self.project)),[])
        self.assertEqual((self.project/'notes.txt').read_text(),'local project')

if __name__=='__main__':unittest.main()
