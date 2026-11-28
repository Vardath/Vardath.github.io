"""Real desktop construction and navigation in an isolated temporary state.
No model startup, installation, external calls or background work admission.
This does not certify native model inference or the physical user's display.
"""
import os
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch


@unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'Tk display required')
class IntegratedInterfaceTests(unittest.TestCase):
    def setUp(self):
        import desktop_app
        from deepthort_local.memory_observer import MemoryObserver
        self.stack=ExitStack()
        self.addCleanup(self.stack.close)
        tmp=self.stack.enter_context(tempfile.TemporaryDirectory())
        self.state=Path(tmp)/'state'
        self.stack.enter_context(patch.object(desktop_app,'STATE',self.state))
        self.stack.enter_context(patch.object(MemoryObserver,'start_duty',lambda *a,**kw:None))
        cls=desktop_app.DeepThorTDesktop
        for name in ('_refresh_inventory','_auto_start_if_installed','_start_sentinel',
                     '_scheduler','_automatic_tool_tick','_tool_probe_tick','_project_work_tick',
                     '_poll_server','_council_tick','_process_snapshot','_refresh_janus_view'):
            self.stack.enter_context(patch.object(cls,name,lambda *a,**kw:None))
        self.app=cls()
        self.addCleanup(self.app._quit)

    def test_all_workspaces_reachable_and_preserve_draft(self):
        app=self.app
        expected=('Chats','Work queue','File review','Tasks','Processes','JANUS & Sentinel',
                  'Computer & Tools','Files & Images','Command Centre','Approvals & PC Activity',
                  'Knowledge & Memory','Studio','Settings & Integrations')
        self.assertEqual(tuple(app.tabs.tab(t,'text') for t in app.tabs.tabs()),expected)
        app.input.insert('1.0','Unsent acceptance test draft')
        for size in ('1320x860','1138x765','1000x650'):
            app.geometry(size)
            for i,name in enumerate(expected):
                with self.subTest(size=size,workspace=name):
                    app.workspace_navigator.current.set(name)
                    app.workspace_navigator.select()
                    app.update()
                    self.assertEqual(app.tabs.index('current'),i)
                    self.assertEqual(app.workspace_navigator.current.get(),name)
                    self.assertTrue(app.workspace_navigator.choice.winfo_ismapped())
            app.tabs.select(0)
            app.update()
            self.assertEqual(app.input.get('1.0','end-1c'),'Unsent acceptance test draft')

    def test_overviews_are_read_only_and_tool_categories_do_not_dispatch(self):
        app=self.app
        with patch.object(app,'_start_command') as run, patch.object(app.jobs,'change') as change:
            app._refresh_command_centre()
            app._refresh_approval_centre()
            app._refresh_knowledge_centre()
            app._refresh_studio()
            app._refresh_settings_centre()
            app._studio_tool_category('Music & audio')
            app.update()
            self.assertEqual(app.tabs.index('current'),7)
            self.assertEqual(app.media_shelf.category.get(),'Music & audio')
            run.assert_not_called()
            change.assert_not_called()
        self.assertIn('snapshot',app.settings_centre.notice.get())
        self.assertIn('bounded',app.studio_centre.notice.get())

    def test_primary_context_help_and_exact_navigation(self):
        from deepthort_local.ui_help import TABS
        app=self.app
        self.assertEqual(set(app.workspace_navigator.names),set(TABS))
        self.assertTrue(app.bind_all('<F1>'))
        self.assertTrue(app.bind('<Control-F6>'))
        self.assertTrue(app.input.bind('<Control-Return>'))
        self.assertTrue(app.input.bind('<Control-Shift-Return>'))

    def test_failed_refresh_clears_previous_workspace_records(self):
        app=self.app
        app.command_centre.render('previous',
            [('old-project',('1','previous','paused','1','1'))],
            [('7',('7','waiting_approval','build','old target','old evidence'))],
            {'waiting_approval':1})
        app.approval_centre.render('previous',
            [('7',('7','waiting_approval','old target','old evidence'))],
            [('8',('8','complete','old action','review','old time'))])
        with patch.object(app,'_project_key',return_value='new'), \
             patch('deepthort_local.project_queue.inventory',side_effect=OSError('fixture failure')), \
             patch.object(app.jobs,'items',side_effect=OSError('fixture failure')):
            app._refresh_command_centre()
            app._refresh_approval_centre()
        self.assertEqual(app.command_centre.project,'new')
        self.assertEqual(app.approval_centre.project,'new')
        for table in (app.command_centre.projects,app.command_centre.jobs,
                      app.approval_centre.job_table,app.approval_centre.action_table):
            self.assertFalse(table.get_children())
        self.assertIn('Snapshot unavailable',app.command_centre.notice.get())
        self.assertIn('Snapshot unavailable',app.approval_centre.notice.get())

    def test_unavailable_conversation_does_not_open_wrong_chat(self):
        app=self.app
        app.tabs.select(8)
        app.update()
        before=app.current_chat
        with patch.object(app.jobs,'get',return_value={
                'project':app._project_key(),'mode':'chat','chat_id':'missing-fixture-chat'}):
            app._open_command_job('7')
        self.assertEqual(app.tabs.index('current'),8)
        self.assertEqual(app.current_chat,before)
        self.assertIn('not open',app.command_centre.notice.get())

    def test_original_primary_chat_actions_within_window(self):
        app=self.app
        app.tabs.select(0)
        for size in ('1320x860','1138x765'):
            with self.subTest(size=size):
                app.geometry(size)
                app.update()
                buttons=[w for row in app.chat_actions.winfo_children()
                         for w in row.winfo_children() if w.winfo_class()=='TButton']
                labels=[b.cget('text') for b in buttons]
                for label in ('Draft project plan','Approve plan & queue','Revise existing file'):
                    self.assertIn(label,labels)
                bottom=app.winfo_rooty()+app.winfo_height()
                self.assertTrue(all(b.winfo_ismapped() for b in buttons))
                self.assertLessEqual(max(b.winfo_rooty()+b.winfo_height() for b in buttons),bottom)
