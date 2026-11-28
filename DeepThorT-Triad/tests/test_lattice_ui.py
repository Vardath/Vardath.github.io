"""Native Tk shelf regression with no inference or tool execution."""
import tkinter as tk
from tkinter import ttk
import unittest
from deepthort_local.lattice_ui import ToolShelf, PALETTE, dragon_mark, action_menu, scroll_text, composer_rows, SearchPicker, matches_query, sync_table, filter_status_rows, SourceNavigator, source_scrollbars, proposal_code, highlight_diff, measured_process_rows, replace_readonly, operative_rows, SocietyLattice, inventory_rows, CommandCentre, command_job_rows, ApprovalCentre, approval_job_rows, pc_action_rows, KnowledgeMemoryCentre, StudioCentre, studio_artifact_rows, SettingsCentre, settings_policy_rows


class LatticeShelfTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.geometry('450x280')
        self.shelf = ToolShelf(self.root)
        self.shelf.pack(fill='both', expand=True)
        self.calls = []
        self.buttons = []
        for labels in [('Search internet…', 'Create PDF…'),
                       ('Test OS restricted-token boundary…', 'Generate image from prompt')]:
            row = ttk.Frame(self.shelf.rows)
            row.pack(fill='x')
            for label in labels:
                button = ttk.Button(row, text=label, command=lambda label=label: self.calls.append(label))
                button.pack(side='left')
                self.buttons.append(button)
        self.shelf.index_buttons()
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def labels(self):
        return [b.cget('text') for b in self.buttons if b.winfo_manager() == 'pack']

    def test_filter_empty_restore_and_exact_callback(self):
        original = self.labels()
        self.shelf.query.set('restricted-token')
        self.root.update()
        self.assertEqual(self.labels(), ['Test OS restricted-token boundary…'])
        self.assertEqual(self.shelf.count.get(), '1 / 4 tools')
        self.assertEqual(self.calls, [])
        self.buttons[2].invoke()
        self.assertEqual(self.calls, ['Test OS restricted-token boundary…'])
        self.shelf.query.set('no such operation')
        self.root.update()
        self.assertEqual(self.labels(), [])
        self.assertEqual(self.shelf.count.get(), '0 / 4 tools')
        self.shelf.query.set('')
        self.root.update()
        self.assertEqual(self.labels(), original)
        self.assertEqual(self.shelf.count.get(), '4 / 4 tools')

    def test_scroll_region_includes_original_controls(self):
        self.root.geometry('180x120')
        self.root.update()
        self.assertTrue(self.shelf.canvas.winfo_ismapped())
        box = self.shelf.canvas.bbox('all')
        self.assertGreater(box[2], self.shelf.canvas.winfo_width())
        self.shelf.canvas.xview_moveto(1)
        self.assertGreater(self.shelf.canvas.xview()[0], 0)

    def test_palette_and_mark(self):
        mark = dragon_mark(self.root)
        self.assertGreaterEqual(len(mark.find_all()), 4)
        self.assertEqual(mark.cget('bg'), PALETTE['base'])
        mark.destroy()


    def test_action_menu_is_inert_until_exact_choice(self):
        control = action_menu(self.root, 'System', [
            ('Start', lambda: self.calls.append('start')),
            ('Stop', lambda: self.calls.append('stop'))])
        menu = control.nametowidget(control.cget('menu'))
        self.assertEqual(self.calls, [])
        self.assertEqual(menu.entrycget(1, 'label'), 'Stop')
        menu.invoke(1)
        self.assertEqual(self.calls, ['stop'])

    def test_composer_resize_preserves_draft_and_scroll(self):
        frame = ttk.Frame(self.root)
        text = tk.Text(frame, height=5, undo=True)
        bar = scroll_text(frame, text)
        text.insert('1.0', 'unsent draft')
        for height, expanded, expected in [(860, False, 5), (860, True, 12),
                                           (650, True, 3), (765, False, 3)]:
            self.assertEqual(composer_rows(height, expanded), expected)
            text.configure(height=expected)
        self.assertEqual(text.get('1.0', 'end-1c'), 'unsent draft')
        self.assertTrue(text.cget('yscrollcommand'))
        self.assertTrue(bar.cget('command'))


    def test_picker_does_not_confuse_duplicate_titles_or_auto_open(self):
        picker = SearchPicker(self.root, 'Search', [('a','Same title'), ('b','Same title'),
                                                    ('c','Other project')], self.calls.append)
        picker.query.set('SAME')
        self.root.update()
        self.assertEqual(picker.summary.get(), '2 / 3')
        self.assertEqual(self.calls, [])
        picker.open_selected()
        self.assertEqual(self.calls, [])
        picker.items.selection_set(1)
        picker.open_selected()
        self.assertEqual(self.calls, ['b'])

    def test_path_filter_and_recent_project_identity(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from deepthort_local.job_queue import ChatRegistry
        self.assertTrue(matches_query('src/Big Ship.xml','ship SRC'))
        self.assertFalse(matches_query('src/Big Ship.xml','ship png'))
        with TemporaryDirectory() as tmp:
            registry = ChatRegistry(Path(tmp)/'chats.db')
            registry.create('one','chat')
            registry.create('(general)','chat')
            registry.create('two','chat')
            registry.create('one','new chat')
            self.assertEqual(registry.recent_projects(),['one','two'])


    def test_queue_filter_preserves_exact_selection_and_never_auto_selects(self):
        table = ttk.Treeview(self.root, columns=('state','detail'), show='headings')
        rows = [('1',('running','Build ship')),('2',('waiting_approval','Review ship')),
                ('3',('completed','Test ship')),('4',('failed','Repair engine'))]
        sync_table(table,rows)
        self.assertEqual(table.selection(),())
        table.selection_set('2')
        sync_table(table,filter_status_rows(rows,'Waiting / blocked','SHIP'))
        self.assertEqual(table.selection(),('2',))
        self.assertEqual(table.get_children(),('2',))
        sync_table(table,filter_status_rows(rows,'Active','ship'))
        self.assertEqual(table.get_children(),('1',))
        self.assertEqual(table.selection(),())
        sync_table(table,rows)
        self.assertEqual(table.get_children(),('1','2','3','4'))
        self.assertEqual(table.selection(),())
        self.assertEqual(filter_status_rows([('a',('Done','task'))],'Planned',''),[])


    def test_source_inspection_navigation_is_read_only(self):
        frame=ttk.Frame(self.root)
        text=tk.Text(frame,wrap='none')
        source_scrollbars(frame,text)
        text.insert('1.0','first\nneedle\nlast needle')
        text.configure(state='disabled')
        nav=SourceNavigator(self.root,text)
        before=text.get('1.0','end-1c')
        nav.term.set('needle')
        nav.find()
        self.assertEqual(nav.notice.get(),'Line 2')
        nav.find()
        self.assertEqual(nav.notice.get(),'Line 3')
        nav.find()
        self.assertEqual(nav.notice.get(),'Line 2')
        nav.line.set('1')
        nav.goto()
        self.assertEqual(nav.notice.get(),'Line 1')
        nav.line.set('100')
        nav.goto()
        self.assertEqual(nav.notice.get(),'Invalid line')
        self.assertEqual(text.get('1.0','end-1c'),before)
        self.assertEqual(text.cget('state'),'disabled')

    def test_diff_colours_preserve_exact_text(self):
        text=tk.Text(self.root)
        diff='--- before\n+++ after\n@@ -1 +1 @@\n-old\n+new'
        text.insert('1.0',diff)
        highlight_diff(text)
        self.assertEqual(text.get('1.0','end-1c'),diff)
        self.assertTrue(text.tag_ranges('diff_add'))
        self.assertTrue(text.tag_ranges('diff_remove'))
        self.assertEqual(proposal_code('PROPOSED CODE — edit below before approving\n\nnew'),'new')
        self.assertEqual(proposal_code('ordinary source'),'ordinary source')


    def test_process_samples_remain_observed_and_distinct(self):
        rows=measured_process_rows([{'name':'Granite','pid':42,'system_cpu_percent':3.25,
                                    'working_set_bytes':2**20*3,'private_bytes':2**20*5}])
        self.assertEqual(rows,[('42:Granite',('Granite',42,'3.2','3.0','5.0'))])
        self.assertEqual(measured_process_rows([]),[])

    def test_process_refresh_preserves_readonly_buffer(self):
        text=tk.Text(self.root,height=3)
        text.pack()
        text.configure(state='disabled')
        first='\n'.join(str(i) for i in range(80))
        replace_readonly(text,first)
        self.root.update()
        text.yview_moveto(.4)
        before=text.yview()[0]
        replace_readonly(text,first+'\nnext')
        self.root.update()
        self.assertEqual(text.get('1.0','end-1c'),first+'\nnext')
        self.assertEqual(text.cget('state'),'disabled')
        self.assertAlmostEqual(text.yview()[0],before,delta=.06)


    def test_operative_status_rejects_stale_broker_and_does_not_invent_gemma_pid(self):
        health={'pid':42,'models':{'implementation':{'resident':True,'pid':43,'generating':True}},
                'memory_model':{'resident':True,'pid':44,'busy':True}}
        current=dict(operative_rows(health,42,True))
        self.assertEqual(current['implementation'][2:],('Generating',43))
        self.assertEqual(current['memory'][2:],('Busy',44))
        self.assertEqual(current['gemma'][2:],('Creative lane active','—'))
        self.assertEqual(dict(operative_rows(health,99))['implementation'][2:],('Not observed','—'))

    def test_society_lattice_uses_separate_recorded_core_states(self):
        lattice=SocietyLattice(self.root)
        lattice.pack(fill='both',expand=True)
        lattice.update_records({'Front':{'focus':'project evidence'}},{'Front':{'focus':'oversight evidence'}})
        self.root.update()
        self.assertEqual(len(lattice.names),11)
        self.assertIn('project evidence',lattice.detail.get('1.0','end'))
        lattice.society.set('Sentinel')
        lattice.redraw()
        self.assertIn('oversight evidence',lattice.detail.get('1.0','end'))
        self.assertNotIn('project evidence',lattice.detail.get('1.0','end'))
        lattice.select('Memory')
        self.assertIn('No recorded appraisal',lattice.detail.get('1.0','end'))


    def test_inventory_distinguishes_discovery_and_verification(self):
        rows=dict(inventory_rows([{'name':'Godot','found':True,'location':'C:/Godot','purpose':'Games'},
                                  {'name':'Blender','found':False,'purpose':'Meshes'}],{'Godot':'Stale / changed'}))
        self.assertEqual(rows['Godot'][1:5],('Found','Games','C:/Godot','Stale / changed'))
        self.assertEqual(rows['Blender'][1:5],('Missing','Meshes','—','Not verified'))


    def test_command_centre_snapshot_and_job_selection_are_inert(self):
        centre=CommandCentre(self.root,lambda:self.calls.append('refresh'),
                             self.calls.append,[],lambda:self.calls.append('queue'))
        rows=command_job_rows([{'id':7,'state':'waiting_approval','mode':'build','target':'main.py','detail':'Review only'},
                               {'id':8,'state':'complete','mode':'build','detail':'Saved'}])
        centre.render('workspace',[],rows,{'waiting_approval':1,'complete':1})
        self.assertEqual(self.calls,[])
        centre.state.set('Waiting / blocked')
        centre.filter_jobs()
        self.assertEqual(centre.jobs.get_children(),('7',))
        centre._open_selected()
        self.assertEqual(self.calls,[])
        centre.jobs.selection_set('7')
        centre._open_selected()
        self.assertEqual(self.calls,['7'])
        centre.render('another workspace',[],rows,{'complete':1})
        self.assertEqual(centre.jobs.selection(),())


    def test_approval_centre_separates_job_review_and_action_identity(self):
        centre=ApprovalCentre(self.root,lambda:None,lambda ident:self.calls.append(('job',ident)),
                               lambda ident:self.calls.append(('action',ident)),[])
        jobs=approval_job_rows([{'id':5,'state':'waiting_approval','target':'main.py'},
                                {'id':6,'state':'complete'}])
        actions=pc_action_rows([{'id':5,'status':'approved','label':'Check','approval_source':'user'}])
        centre.render('workspace',jobs,actions)
        self.assertEqual(centre.job_table.get_children(),('5',))
        self.assertEqual(centre.action_table.get_children(),('5',))
        self.assertEqual(self.calls,[])
        self.assertEqual(centre.job_table.selection(),())
        self.assertEqual(centre.action_table.selection(),())
        centre.job_table.selection_set('5')
        centre.render('other workspace',[],actions)
        self.assertEqual(centre.job_table.selection(),())


    def test_memory_centre_preserves_scope_and_advisory_status(self):
        centre=KnowledgeMemoryCentre(self.root,lambda:self.calls.append('refresh'),lambda:self.calls.append('library'))
        sample={'thread_alive':True,'active':False,'pending':2,'cached_reports':1}
        record={'work_id':'a','job_id':1,'request_id':2,'outcome':'findings','focus':'engine',
                'finding_count':1,'receipt_sha':'abc','findings':[{'id':'N1'}]}
        centre.render('workspace',[record],sample)
        self.assertEqual(self.calls,[])
        centre.table.selection_set('a')
        centre.inspect()
        self.assertIn('no authority',centre.detail.get('1.0','end'))
        centre.render('other workspace',[],sample)
        self.assertEqual(centre.table.get_children(),())
        self.assertNotIn('N1',centre.detail.get('1.0','end'))


    def test_studio_categories_and_artifact_scope(self):
        shelf=ToolShelf(self.root)
        row=ttk.Frame(shelf.rows);row.pack()
        button=ttk.Button(row,text='Generate song',command=lambda:self.calls.append('song'));button.pack()
        shelf.set_category(row,'Music & audio')
        shelf.index_buttons()
        shelf.category.set('Images & textures')
        self.assertEqual(shelf.count.get(),'0 / 1 tools')
        shelf.category.set('Music & audio')
        self.assertEqual(shelf.count.get(),'1 / 1 tools')
        self.assertEqual(self.calls,[])
        studio=StudioCentre(self.root,lambda:None,self.calls.append,lambda path:'Metadata '+path)
        studio.render('workspace',studio_artifact_rows(['song.mid','image.png','source.py']))
        self.assertEqual(set(studio.table.get_children()),{'song.mid','image.png'})
        studio.category.set('Audio');studio.filter()
        self.assertEqual(studio.table.get_children(),('song.mid',))
        studio.table.selection_set('song.mid');studio.inspect()
        self.assertIn('Metadata song.mid',studio.detail.get('1.0','end'))
        studio.render('other',[])
        self.assertNotIn('song.mid',studio.detail.get('1.0','end'))


    def test_settings_overview_is_inert_and_accurately_labels_policy(self):
        centre=SettingsCentre(self.root,lambda:self.calls.append('refresh'),
                              [('Permissions',[('Configure',lambda:self.calls.append('configure'))])])
        rows=settings_policy_rows({'enabled':True},{'enabled':False,'allow_upgrades':True},'blocked')
        centre.render(rows,'AI: stopped','workspace')
        self.assertEqual(self.calls,[])
        self.assertEqual(dict(rows)['project'][1],'Enabled')
        self.assertEqual(dict(rows)['tools'][1],'Disabled')
        self.assertIn('only',dict(rows)['upgrades'][2])
        self.assertEqual(dict(rows)['network'][1],'blocked')
        self.assertIn('not runtime verification',centre.notice.get())
