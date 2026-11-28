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

    def test_studio_bounded_preview_and_checkpoint_identity(self):
        import hashlib
        from types import SimpleNamespace
        from deepthort_local.studio_inspection import inspect_bytes, matching_checkpoints
        from deepthort_local.workspace import MAX_READ_BYTES
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            data=b'hello artifact'
            (root/'note.txt').write_bytes(data)
            result=inspect_bytes(root,'note.txt')
            digest=hashlib.sha256(data).hexdigest()
            self.assertEqual(result['preview'],'hello artifact')
            self.assertEqual(result['sha256'],digest)
            (root/'large.txt').write_bytes(b'x'*(MAX_READ_BYTES+1))
            self.assertIsNone(inspect_bytes(root,'large.txt')['sha256'])
            (root/'binary.txt').write_bytes(b'hello\x00')
            self.assertIsNone(inspect_bytes(root,'binary.txt')['preview'])
            (root/'long.txt').write_text('z'*13000,encoding='utf-8')
            self.assertEqual(len(inspect_bytes(root,'long.txt')['preview']),12000)
            with self.assertRaises(ValueError):
                inspect_bytes(root,'../outside.txt')
            jobs=SimpleNamespace(items=lambda project,limit:[{'project':str(root),'mode':'build','id':3}],
                                 steps=lambda ident:[{'path':'note.txt'}])
            checkpoints=SimpleNamespace(list=lambda ident:[
                {'project':str(root),'job_id':3,'id':'wrong-hash','reason':'artifact_saved','files':{'note.txt':'0'*64}},
                {'project':'other','job_id':3,'id':'wrong-project','reason':'artifact_saved','files':{'note.txt':digest}},
                {'project':str(root),'job_id':3,'id':'exact','reason':'artifact_saved','files':{'note.txt':digest}}])
            self.assertEqual(matching_checkpoints(str(root),'note.txt',digest,jobs,checkpoints),
                             [(3,'exact','artifact_saved')])

    def test_assignment_evidence_exact_workspace_and_no_dispatch(self):
        import json
        from deepthort_local.agent_contract import canonical_sha
        from deepthort_local.assignment_inspection import assignment_rows
        app=self.app
        project=app._project_key()
        contract={'job_id':700,'step_id':701,'project':project,'graph_sha256':'test-plan',
                  'requester':'janus','assignee':'implementation','reviewer':'sentinel','path':'fixture.txt'}
        with app.graphs._db() as db:
            db.execute("INSERT INTO graphs(job_id,project,plan_sha256) VALUES(?,?,?)",(700,project,'test-plan'))
            db.execute("INSERT INTO project_assignments_v43(attempt,job_id,step_id,contract,contract_sha,state) VALUES(?,?,?,?,?,?)",
                       ('fixture-attempt',700,701,json.dumps(contract),canonical_sha(contract),'assigned'))
        with patch.object(app,'_start_command') as run:
            app._refresh_assignment_evidence()
            run.assert_not_called()
        self.assertEqual(app.assignment_table.get_children(),('source:fixture-attempt',))
        self.assertEqual(app.assignment_table.item('source:fixture-attempt','values')[0],'Granite')
        self.assertFalse(assignment_rows('other',app.graphs.path,app.delegations.path))
        with app.graphs._db() as db:
            db.execute("UPDATE project_assignments_v43 SET contract_sha='wrong' WHERE attempt='fixture-attempt'")
        app._refresh_assignment_evidence()
        self.assertFalse(app.assignment_table.get_children())
        self.assertIn('unavailable',app.assignment_notice.get())

    def test_delegation_stage_evidence_is_scoped_to_current_attempt(self):
        from deepthort_local.assignment_inspection import assignment_rows
        from deepthort_local.delegation import binding
        app=self.app
        project=app._project_key()
        ident=app.conversations.submit(app.current_chat,project,'chat','fixture request')
        with app.delegations.db() as db:
            row=db.execute('SELECT * FROM conversation_requests WHERE id=?',(ident,)).fetchone()
            db.execute('INSERT INTO agent_batches_v39 VALUES(?,?,?,?)',(ident,binding(row),2,'running'))
            db.executemany('INSERT INTO agent_stages_v39 VALUES(?,?,?,?,?,?,?)',
                           [(ident,1,'old','multimedia','interrupted',None,None),
                            (ident,2,'compose','multimedia','queued',None,None)])
        rows=assignment_rows(project,app.graphs.path,app.delegations.path)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0][1][:4],('Gemma','Request #'+str(ident),'compose','queued'))
        self.assertFalse(assignment_rows('other',app.graphs.path,app.delegations.path))

    def test_grant_inspection_scope_revocation_and_policy(self):
        from deepthort_local.project_authority import issue_grant,inspect_grant,revoke_grant
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            project=root/'project';project.mkdir()
            folder=root/'grants'
            job={'id':51,'project':str(project),'chat_id':'test','mode':'build',
                 'state':'queued','approval_key':'fixture'}
            steps=[{'id':1,'sequence':1,'path':'file.txt','description':'fixture'}]
            self.assertIsNone(inspect_grant(folder,job,steps,enabled=True))
            issue_grant(folder,job,steps)
            self.assertEqual(inspect_grant(folder,job,steps,enabled=True)['status'],'Recorded active')
            self.assertEqual(inspect_grant(folder,job,steps,enabled=False)['status'],'Policy disabled')
            mismatch=inspect_grant(folder,job,[dict(steps[0],description='different')],enabled=True)
            self.assertEqual(mismatch['status'],'Identity mismatch')
            self.assertFalse(mismatch['files'])
            revoke_grant(folder,51)
            self.assertEqual(inspect_grant(folder,job,steps,enabled=True)['status'],'Not currently eligible')
            app=self.app
            app.approval_centre.render('old',[],[],[('51',('51','Recorded active','1','date'))])
            app.approval_centre.grant_table.selection_set('51')
            app.approval_centre.render('new',[],[])
            self.assertFalse(app.approval_centre.grant_table.get_children())
            self.assertFalse(app.approval_centre.grant_table.selection())

    def test_task_job_links_are_persistent_scoped_and_do_not_complete_tasks(self):
        from deepthort_local.tasks import TaskBoard
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'tasks.db'
            board=TaskBoard(db)
            ident=board.add('one','Build fixture')
            board.link('one',ident,42)
            self.assertEqual(TaskBoard(db).links('one'),{ident:42})
            self.assertEqual(board.items('one'),[(ident,'Build fixture',0)])
            self.assertFalse(board.links('two'))
            with self.assertRaises(ValueError):
                board.link('two',ident,42)
            board.mark('one',ident,True)
            self.assertEqual(board.links('one'),{ident:42})
            board.link('one',ident,None)
            self.assertFalse(board.links('one'))
            self.assertEqual(board.items('one'),[(ident,'Build fixture',1)])

    def test_task_board_displays_exact_link_and_recorded_graph(self):
        app=self.app
        with tempfile.TemporaryDirectory() as tmp:
            project=Path(tmp).resolve()
            app.project=project
            ident=app.tasks.add(str(project),'Fixture')
            app.tasks.link(str(project),ident,42)
            job={'id':42,'project':str(project),'mode':'build','state':'waiting_verification','detail':'Test still required'}
            with patch.object(app.jobs,'items',return_value=[job]),patch.object(app.jobs,'get',return_value=job), \
                 patch.object(app.graphs,'status',return_value={'state':'active','nodes':[{'kind':'verification','title':'Fixed test','state':'pending'}],'edges':[]}):
                app._refresh_tasks()
                self.assertEqual(app.task_tree.item(str(ident),'values'),('Planned','Fixture','#42 · waiting_verification'))
                app.task_tree.selection_set(str(ident))
                app._inspect_task_job()
                self.assertIn('verification · Fixed test · pending',app.task_evidence.get('1.0','end'))
                self.assertEqual(app.tasks.items(str(project))[0][2],0)
            app.project=None
            app._refresh_tasks()
            self.assertFalse(app.task_tree.get_children())

    def test_archived_picker_rechecks_workspace_and_exact_identity(self):
        app=self.app
        project=app._project_key()
        with patch.object(app.chats,'closed',return_value=[('first','Same title'),('second','Same title')]), \
             patch('desktop_app.SearchPicker') as picker,patch.object(app,'_reopen_chat') as reopen:
            app._open_archived_chat_menu()
            self.assertEqual(picker.call_args.args[2],[('first','Same title'),('second','Same title')])
            callback=picker.call_args.args[3]
            callback('missing')
            reopen.assert_not_called()
            callback('second')
            reopen.assert_called_once_with('second')
            with patch.object(app,'_project_key',return_value=project+'-different'):
                callback('first')
            reopen.assert_called_once_with('second')


    def test_secondary_event_picker_cancel_and_exact_selection(self):
        import tkinter as tk
        from tkinter import ttk
        from deepthort_local.event_trigger_dialog import choose_future_event
        parent=tk.Toplevel(self.app)
        self.addCleanup(lambda:parent.destroy() if parent.winfo_exists() else None)
        options={'first':({'label':'Long recorded label '*200},'changed'),
                 'second':({'label':'Other exact monitor'},'changed')}
        def click(button_text,selection=None):
            editor=next(w for w in parent.winfo_children() if isinstance(w,tk.Toplevel))
            combo=next(w for w in editor.winfo_children() if isinstance(w,ttk.Combobox))
            if selection is not None:combo.set(selection)
            for frame in editor.winfo_children():
                for button in frame.winfo_children():
                    if isinstance(button,ttk.Button) and button.cget('text')==button_text:
                        button.invoke();return
            self.fail('Secondary picker control not found')
        parent.after(50,lambda:click('Cancel'))
        self.assertIsNone(choose_future_event(parent,options))
        parent.after(50,lambda:click('Continue','second'))
        self.assertEqual(choose_future_event(parent,options),'second')
        parent.grab_release()

    def test_screen_review_thumbnail_reserves_controls(self):
        from deepthort_local.screen_capture_dialog import capture_preview_bounds
        self.assertEqual(capture_preview_bounds(860,600),(800,440))
        self.assertEqual(capture_preview_bounds(550,400),(510,240))
        self.assertEqual(capture_preview_bounds(20,20),(1,1))


    def test_studio_media_header_and_changed_playback_identity(self):
        import wave
        from deepthort_local.studio_media import inspect_media,playback_target
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();audio=root/'large.wav'
            with wave.open(str(audio),'wb') as writer:
                writer.setnchannels(1);writer.setsampwidth(2);writer.setframerate(16000)
                writer.writeframes(b'\x00\x00'*100000)
            observed=inspect_media(root,'large.wav')
            self.assertTrue(observed['playable'])
            self.assertIn('16000 Hz',' '.join(observed['lines']))
            self.assertEqual(playback_target(root,'large.wav',observed['identity']),audio)
            audio.write_bytes(b'not audio')
            with self.assertRaises(ValueError):playback_target(root,'large.wav',observed['identity'])
            self.assertFalse(inspect_media(root,'large.wav')['playable'])
            with self.assertRaises(ValueError):inspect_media(root,'../outside.wav')

    def test_studio_explicit_large_media_respects_exclusion(self):
        app=self.app
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();app.project=root
            app.show_all_project_files.set(True)
            media=root/'large.mp4';media.write_bytes(b'\x00\x00\x00\x18ftyp'+b'x'*200000)
            with patch('desktop_app.filedialog.askopenfilename',return_value=str(media)),patch.object(app,'_start_command') as run:
                app._browse_studio_media()
                self.assertTrue(app.studio_centre.table.exists('large.mp4'))
                self.assertIn('not measured',app._inspect_studio_artifact('large.mp4'))
                run.assert_not_called()
            app.inspection_exclusions.exclude(root,'large.mp4')
            app._refresh_studio()
            self.assertFalse(app.studio_centre.table.exists('large.mp4'))
            app.project=None


    def test_knowledge_enrollment_snapshot_does_not_read_source(self):
        from deepthort_local.document_knowledge import DocumentKnowledge
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();one=root/'one';two=root/'two';one.mkdir();two.mkdir()
            index=DocumentKnowledge(root/'index.sqlite3')
            (one/'manual.txt').write_text('Exact useful manual reference for project testing.',encoding='utf-8')
            index.index(one,'manual.txt')
            (one/'manual.txt').unlink()
            with patch('deepthort_local.document_knowledge._read',side_effect=AssertionError('Source read prohibited')):
                rows=index.inspection_records(one)
                self.assertEqual([r['path'] for r in rows],['manual.txt'])
                self.assertNotIn('current',rows[0])
                self.assertFalse(index.inspection_records(two))
                self.assertFalse(index.inspection_records(one,exclude=['manual.txt']))

    def test_knowledge_overview_exact_document_navigation(self):
        app=self.app
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();app.project=root
            sample={'path':'manual.txt','sha256':'a'*64,'origin':'explicit','fragments':3,'locator':'line'}
            with patch.object(app.capabilities.knowledge,'inspection_records',return_value=[sample]), \
                 patch.object(app,'_open_project_knowledge') as open_library:
                app._refresh_knowledge_centre()
                self.assertTrue(app.knowledge_centre.library_table.exists('manual.txt'))
                app.knowledge_centre.library_table.selection_set('manual.txt')
                app.knowledge_centre.inspect_library()
                self.assertIn('source not revalidated',app.knowledge_centre.library_detail.get('1.0','end'))
                app._open_indexed_document('manual.txt')
                open_library.assert_called_once_with(selected_path='manual.txt')
                app._open_indexed_document('other.txt')
                open_library.assert_called_once()
            app.project=None
            app._refresh_knowledge_centre()
            self.assertFalse(app.knowledge_centre.library_table.get_children())


    def test_readiness_snapshot_is_local_and_distinguishes_stale_health(self):
        from deepthort_local.readiness_inspection import model_records,integration_records
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            records=dict(model_records(root,{'pid':8,'models':{'janus':{'resident':True,'pid':12}}},9))
            self.assertEqual(records['janus'][3],'Not observed')
            self.assertIn('Missing',records['janus'][2])
            self.assertEqual(len(records),7)
            class Session:
                expires=200
                def token(self):raise AssertionError('No token access')
            rows=dict(integration_records('(general)',root/'missing.sqlite3',Session(),now=100))
            self.assertIn('Unexpired',rows['github'][1])
            self.assertIn('not revalidated',rows['github'][1])
            self.assertFalse((root/'missing.sqlite3').exists())
            app=self.app
            with patch.object(app,'_start_ai') as start,patch.object(app,'_start_command') as run:
                app._refresh_settings_centre()
                start.assert_not_called();run.assert_not_called()
            self.assertEqual(len(app.settings_centre.model_table.get_children()),7)
            self.assertTrue(app.settings_centre.integration_table.exists('github'))


    def test_failed_task_job_studio_and_readiness_snapshots_clear_rows(self):
        import sqlite3
        app=self.app
        app.job_tree.insert('','end',iid='oldjob',values=('queued','build','old','old'))
        app.task_tree.insert('','end',iid='oldtask',values=('Planned','old','old'))
        app.studio_centre.render('old',[('old.txt',('Document','old.txt','.txt'))])
        app.settings_centre.render_readiness([('old',('old','old','old','old'))],[])
        with tempfile.TemporaryDirectory() as tmp:
            app.project=Path(tmp).resolve()
            with patch.object(app.jobs,'items',side_effect=sqlite3.OperationalError('locked')), \
                 patch.object(app.tasks,'links',side_effect=sqlite3.OperationalError('locked')), \
                 patch.object(app.inspection_exclusions,'filter',side_effect=ValueError('invalid exclusion')), \
                 patch('deepthort_local.readiness_inspection.model_records',side_effect=OSError('unavailable')):
                app._refresh_jobs();app._refresh_tasks();app._refresh_studio();app._refresh_settings_centre()
            self.assertFalse(app.job_tree.get_children())
            self.assertFalse(app.task_tree.get_children())
            self.assertFalse(app.studio_centre.table.get_children())
            self.assertFalse(app.settings_centre.model_table.get_children())
            self.assertIn('unavailable',app.queue_summary.get().lower())
            self.assertIn('unavailable',app.task_notice.get().lower())
            self.assertIn('unavailable',app.studio_centre.notice.get().lower())
            self.assertIn('unavailable',app.settings_centre.notice.get().lower())
            app.project=None

    def test_inventory_error_from_other_workspace_is_ignored(self):
        app=self.app
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();app.project=root
            app.inventory={'tools':[]}
            app.inventory_notice.set('Current snapshot')
            app.events.put(('inventory_error','old failure',root/'old'))
            app._handle_events()
            self.assertEqual(app.inventory_notice.get(),'Current snapshot')
            app.events.put(('inventory_error','current failure',root))
            app._handle_events()
            self.assertIsNone(app.inventory)
            self.assertIn('Scan failed',app.inventory_notice.get())
            app.project=None


    def test_display_preferences_allowlist_and_geometry(self):
        from deepthort_local.interface_preferences import SCHEMA,load,save,geometry,sidebar_position
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'display.json'
            self.assertEqual(load(path)['page'],'Chats')
            self.assertTrue(save(path,{'schema':SCHEMA,'width':9000,'height':800,'sidebar':900,
                'page':'Studio','expanded_composer':True,'job_filter':'Waiting / blocked',
                'task_filter':'unrecognized','draft':'private prompt','query':'private filter',
                'approval':True,'follow_activity':'false'}))
            row=load(path)
            self.assertEqual(row['page'],'Studio')
            self.assertEqual(row['job_filter'],'Waiting / blocked')
            self.assertEqual(row['task_filter'],'All states')
            self.assertTrue(row['follow_activity'])
            self.assertNotIn('draft',row);self.assertNotIn('query',row);self.assertNotIn('approval',row)
            self.assertEqual(geometry(row,1138,765),(1066,655))
            self.assertEqual(sidebar_position(row,1000),380)
            path.write_text('{invalid',encoding='utf-8')
            self.assertEqual(load(path)['page'],'Chats')

    def test_desktop_display_preferences_roundtrip_without_user_content(self):
        from deepthort_local.interface_preferences import load
        app=self.app
        app.update_idletasks()
        app.tabs.select(3)
        app.expanded_composer.set(True)
        app.task_filter.set('Done')
        app.task_query.set('private search')
        app.input.insert('1.0','private unsent prompt')
        app._save_display_preferences()
        saved=load(app.display_preferences_file)
        self.assertEqual(saved['page'],'Tasks')
        self.assertEqual(saved['task_filter'],'Done')
        self.assertTrue(saved['expanded_composer'])
        self.assertNotIn('private',app.display_preferences_file.read_text('utf-8'))
        app._display_preferences=saved
        app.tabs.select(0);app.task_filter.set('Planned');app.expanded_composer.set(False)
        app._restore_display_preferences()
        app.update_idletasks()
        self.assertEqual(app.tabs.index('current'),3)
        self.assertEqual(app.task_filter.get(),'Done')
        self.assertTrue(app.expanded_composer.get())
        self.assertEqual(app.input.get('1.0','end-1c'),'private unsent prompt')


    def test_startup_display_restore_never_overrides_subsequent_navigation(self):
        app=self.app
        app._display_preferences=dict(app._display_preferences,page='Tasks')
        app._restore_display_preferences()
        self.assertEqual(app.tabs.index('current'),3)
        app.tabs.select(7)
        app.update_idletasks()
        self.assertEqual(app.tabs.index('current'),7)


    def test_recorded_chat_navigation_protects_unsent_material(self):
        app=self.app
        project=app._project_key()
        other=app.chats.create(project,'Same project navigation fixture')
        app._refresh_chats()
        original=app.current_chat
        app.input.insert('1.0','Unsent draft')
        self.assertFalse(app._navigate_recorded_chat(other,app.queue_summary))
        self.assertEqual(app.current_chat,original)
        self.assertEqual(app.input.get('1.0','end-1c'),'Unsent draft')
        app.input.delete('1.0','end')
        self.assertTrue(app._navigate_recorded_chat(other,app.queue_summary))
        self.assertEqual(app.current_chat,other)
        self.assertFalse(app._navigate_recorded_chat('absent',app.queue_summary))

    def test_memory_record_navigation_requires_unchanged_receipt(self):
        app=self.app
        centre=app.knowledge_centre
        record={'work_id':'exact','receipt_sha':'fixture','job_id':7,'request_id':9}
        centre.project=app._project_key()
        centre.records={'exact':record}
        with patch('deepthort_local.memory_duty.inspection_records',return_value=[dict(record,receipt_sha='changed')]), \
             patch.object(app.jobs,'get') as get:
            app._open_receipt_job('exact')
            get.assert_not_called()
        self.assertIn('changed',centre.notice.get())
        with patch('deepthort_local.memory_duty.inspection_records',return_value=[record]), \
             patch.object(app.conversations,'get',return_value={'project':'another-workspace','chat_id':'other'}) as get:
            app._open_receipt_conversation('exact')
            get.assert_called_once_with(9)
        self.assertIn('unavailable',centre.notice.get())

    def test_job_target_navigation_requires_exact_studio_path(self):
        app=self.app
        job={'id':8,'project':app._project_key(),'target':'folder/clip.mp4'}
        with patch.object(app,'_selected_job',return_value=job), \
             patch.object(app,'_refresh_studio'):
            app.studio_centre.render(app._project_key(),[('clip.mp4',('Video','clip.mp4','.mp4'))])
            app.tabs.select(1)
            app._open_selected_job_artifact()
            self.assertEqual(app.tabs.index('current'),1)
            app.studio_centre.render(app._project_key(),[('folder/clip.mp4',('Video','folder/clip.mp4','.mp4'))])
            app._open_selected_job_artifact()
            self.assertEqual(app.tabs.index('current'),11)
            self.assertEqual(app.studio_centre.table.selection(),('folder/clip.mp4',))


    def test_operation_stop_routes_are_identity_bound_and_not_global(self):
        from types import SimpleNamespace
        app=self.app
        thread=SimpleNamespace(is_alive=lambda:True)
        app._latest_test_thread=thread
        app._render_operations({'queued':3,'waiting_approval':2})
        self.assertIn('waiting_approval: 2',app.operation_notice.get())
        app.operation_table.selection_set('latest')
        with patch.object(app,'_stop_latest_test') as stop,patch.object(app,'_stop_ai') as global_stop, \
             patch.object(app,'_cancel_tool') as broad,patch('desktop_app.messagebox.askyesno',return_value=True):
            app._latest_test_thread=SimpleNamespace(is_alive=lambda:True)
            app._stop_selected_operation()
            stop.assert_not_called()
            app._render_operations({})
            app.operation_table.selection_set('latest')
            app._stop_selected_operation()
            stop.assert_called_once()
            broad.assert_not_called();global_stop.assert_not_called()
        app._latest_test_thread=None
        app._render_operations({})
        self.assertFalse(app.operation_table.exists('latest'))

    def test_operation_shared_process_is_not_individually_cancelled(self):
        from types import SimpleNamespace
        app=self.app
        app.tool_process=SimpleNamespace(pid=123,poll=lambda:None)
        app._render_operations({})
        app.operation_table.selection_set('tool')
        with patch.object(app,'_cancel_tool') as broad,patch.object(app,'_stop_ai') as global_stop:
            app._stop_selected_operation()
            broad.assert_not_called();global_stop.assert_not_called()
        self.assertIn('No independent stop',app.operation_notice.get())
        app.tool_process=None


    def test_unchanged_table_rows_do_not_rewrite_or_reorder(self):
        from deepthort_local.lattice_ui import sync_table
        import tkinter.ttk as ttk
        tree=ttk.Treeview(self.app,columns=('value',),show='headings')
        rows=[(str(i),(i,)) for i in range(200)]
        sync_table(tree,rows)
        tree.selection_set('17')
        original=tree.item
        writes=[]
        def item(ident,*args,**kwargs):
            if kwargs:writes.append(ident)
            return original(ident,*args,**kwargs)
        with patch.object(tree,'item',side_effect=item),patch.object(tree,'move',wraps=tree.move) as move:
            sync_table(tree,rows)
            self.assertEqual(writes,[])
            move.assert_not_called()
            sync_table(tree,[('0',('changed',)),*rows[1:]])
            self.assertEqual(writes,['0'])
        self.assertEqual(tree.selection(),('17',))
        tree.destroy()

    def test_activity_display_bounded_without_dropping_durable_events(self):
        app=self.app
        with patch('desktop_app.record') as log:
            app._log('long fixture '+('z'*10000))
            self.assertIn('display truncated',app.activity.get('1.0','end'))
            self.assertIn('z'*10000,log.call_args.kwargs['message'])
            app.activity.configure(state='normal')
            app.activity.insert('end','fixture line\n'*2500)
            app.activity.configure(state='disabled')
            app._log('trim fixture')
            self.assertLessEqual(int(app.activity.index('end-1c').split('.')[0]),2001)
            self.assertIn('trim fixture',app.activity.get('1.0','end'))

    def test_operation_counts_unavailable_are_not_reported_as_zero(self):
        app=self.app
        app._render_operations(None)
        self.assertIn('unavailable',app.operation_notice.get())
