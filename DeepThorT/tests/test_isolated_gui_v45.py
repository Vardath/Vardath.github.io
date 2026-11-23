"""v45: project-scoped, user-approved Windows GUI smoke tests on a separate desktop."""
from pathlib import Path
import json
import os
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from deepthort_local.isolated_gui import (
    IsolatedGuiError, IsolatedGuiStore, NativeWin32Desktop,
    IsolatedGuiPlan, assert_plan_unchanged, plan_isolated_gui,
    run_isolated_gui, MAX_RUN_SECONDS)


class TestIsolatedGuiPlan(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.project=self.root/'project'
        self.project.mkdir()
        self.binary=self.project/'hello.exe'
        self.binary.write_bytes(b'hello native program')
    def tearDown(self):self.tmp.cleanup()

    def test_exact_binary_is_approved_and_fingerprinted(self):
        p=plan_isolated_gui(self.project,self.binary)
        self.assertEqual(p.kind,'isolated_gui_smoke')
        self.assertEqual(p.run_seconds,25)
        self.assertEqual(p.project,str(self.project.resolve()))
        self.assertEqual(p.executable,str(self.binary.resolve()))
        self.assertEqual(len(p.executable_sha256),64)
        assert_plan_unchanged(p)

    def test_changes_after_approval_are_rejected(self):
        p=plan_isolated_gui(self.project,self.binary)
        self.binary.write_bytes(b'changed')
        with self.assertRaises(IsolatedGuiError):assert_plan_unchanged(p)

    def test_binaries_outside_selected_project_are_rejected(self):
        outsider=self.root/'outside.exe';outsider.write_bytes(b'x')
        with self.assertRaises(IsolatedGuiError):plan_isolated_gui(self.project,outsider)

    def test_non_executable_or_empty_file_rejected(self):
        txt=self.project/'script.bat';txt.write_bytes(b'foo')
        with self.assertRaises(IsolatedGuiError):plan_isolated_gui(self.project,txt)
        self.binary.write_bytes(b'')
        with self.assertRaises(IsolatedGuiError):plan_isolated_gui(self.project,self.binary)

    def test_seconds_are_bounded(self):
        for seconds in (-1, 0, 46, True, 1.0):
            with self.subTest(seconds=seconds):
                with self.assertRaises(IsolatedGuiError):plan_isolated_gui(self.project,self.binary,seconds=seconds)
        self.assertEqual(plan_isolated_gui(self.project,self.binary,seconds=MAX_RUN_SECONDS).run_seconds,45)

    def test_symlinks_do_not_override_file_authorization(self):
        link=self.project/'shortcut.exe'
        try:link.symlink_to(self.binary)
        except OSError:self.skipTest('Symlinks unavailable')
        with self.assertRaises(IsolatedGuiError):plan_isolated_gui(self.project,link)

    def test_missing_project_and_binary(self):
        with self.assertRaises(IsolatedGuiError):plan_isolated_gui(self.root/'missing',self.binary)
        with self.assertRaises(IsolatedGuiError):plan_isolated_gui(self.project,self.project/'missing.exe')

    def test_project_binary_size_cap(self):
        with self.binary.open('wb') as f:f.truncate(512*1024*1024+1)
        with self.assertRaises(IsolatedGuiError):plan_isolated_gui(self.project,self.binary)

    def test_guard_on_non_windows(self):
        if os.name != 'nt':
            with self.assertRaises(IsolatedGuiError):NativeWin32Desktop()
            p=plan_isolated_gui(self.project,self.binary)
            with self.assertRaises(IsolatedGuiError):run_isolated_gui(p,threading.Event())

    def test_mocked_backend_accepts_only_explicit_plan_no_desktop_switch(self):
        p=plan_isolated_gui(self.project,self.binary)
        class Fake:
            def run(self,plan,stop,*,foreground_game=None):
                assert plan==p
                assert not stop.is_set()
                return {'status':'window_observed','pid':567,'windows':[{'title':'Hello','bounds':[1,2,3,4],'hung':False}]}
        result=run_isolated_gui(p,threading.Event(),backend=Fake())
        self.assertEqual(result['status'],'window_observed')
        stop=threading.Event();stop.set()
        self.assertEqual(run_isolated_gui(p,stop,backend=Fake())['status'],'cancelled')


class TestIsolatedGuiReceipts(TestIsolatedGuiPlan):
    def store(self):return IsolatedGuiStore(self.root/'state'/'isolation.json')
    def test_no_replay_after_restart(self):
        p=plan_isolated_gui(self.project,self.binary)
        s=self.store();s.begin(p)
        with self.assertRaises(IsolatedGuiError):s.begin(p)
        fresh=self.store()
        self.assertEqual(fresh.interrupt_stale()['status'],'interrupted_unknown')
        self.assertIsNone(fresh.interrupt_stale())
        self.assertIsNone(fresh.snapshot()['active'])
        self.assertEqual(len(fresh.snapshot()['history']),1)

    def test_persists_observations_without_claiming_visual_pass(self):
        s=self.store();s.begin(plan_isolated_gui(self.project,self.binary))
        row=s.finish({'status':'window_observed','pid':250,'exit_code':0,
                'detail':'Window observed only',
                'windows':[{'title':'Project window','bounds':[0,0,10,10],'hung':False}]})
        self.assertEqual(row['status'],'window_observed')
        self.assertNotIn('passed',row['status'])
        self.assertEqual(row['windows'][0]['title'],'Project window')
        self.assertIsNone(s.snapshot()['active'])

    def test_wrong_or_corrupted_schema_fails_closed(self):
        f=self.store().path;f.parent.mkdir()
        f.write_text('{broken')
        with self.assertRaises(IsolatedGuiError):self.store().begin(plan_isolated_gui(self.project,self.binary))
        f.write_text('{"schema":"future","active":null,"history":[]}')
        with self.assertRaises(IsolatedGuiError):self.store().begin(plan_isolated_gui(self.project,self.binary))

    def test_bounded_history_detail_and_window_count(self):
        s=self.store();p=plan_isolated_gui(self.project,self.binary)
        for i in range(34):
            s.begin(p)
            s.finish({'status':'no_window','detail':'x'*1000,
                      'windows':[{'title':'x'}]*30})
        q=s.snapshot()
        self.assertEqual(len(q['history']),30)
        self.assertLessEqual(len(q['history'][-1]['detail']),300)
        self.assertEqual(len(q['history'][-1]['windows']),12)

    def test_receipt_does_not_allow_unknown_statuses(self):
        s=self.store();s.begin(plan_isolated_gui(self.project,self.binary))
        self.assertEqual(s.finish({'status':'gameplay_passed'})['status'],'launch_failed')

    def test_no_symlinked_receipt_writes(self):
        s=self.store();s.path.parent.mkdir()
        target=self.root/'outside.json';target.write_text('do not modify')
        try:s.path.symlink_to(target)
        except OSError:self.skipTest('Symlinks unavailable')
        with self.assertRaises(IsolatedGuiError):s.begin(plan_isolated_gui(self.project,self.binary))
        self.assertEqual(target.read_text(),'do not modify')


class TestIsolatedGuiDesktop(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requires Tk')
    def test_click_approval_background_receipt_and_no_focus_call(self):
        import desktop_app as m
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);proj=root/'app';proj.mkdir()
            exe=proj/'demo.exe';exe.write_bytes(b'fake-native')
            with patch.object(m,'STATE',root/'state'), \
                 patch.object(m.DeepThorTDesktop,'_refresh_inventory',lambda self:None), \
                 patch.object(m,'is_capped_windows_process',return_value=True), \
                 patch.object(m.filedialog,'askopenfilename',return_value=str(exe)), \
                 patch.object(m.messagebox,'askyesno',return_value=True) as approved, \
                 patch.object(m.messagebox,'showerror') as error, \
                 patch.object(m,'run_isolated_gui',return_value={
                     'status':'window_observed','pid':12,'exit_code':0,
                     'windows':[{'title':'Demo','bounds':[0,0,200,100],'hung':False}],
                     'detail':'observed'}) as runner:
                app=m.DeepThorTDesktop()
                try:
                    app._set_project(proj)
                    app._run_isolated_gui()
                    deadline=time.monotonic()+8
                    while time.monotonic()<deadline:
                        app._handle_events();app.update_idletasks()
                        if app.gui_tests.snapshot()['history']:break
                        time.sleep(.04)
                    rec=app.gui_tests.snapshot()['history'][-1]
                    self.assertEqual(rec['status'],'window_observed')
                    self.assertIn('Demo',rec['windows'][0]['title'])
                    self.assertIsNone(app._gui_test_active)
                    approved.assert_called_once()
                    runner.assert_called_once()
                    error.assert_not_called()
                finally:app._quit()

    @unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requires Tk')
    def test_uncapped_python_launch_cannot_run_test(self):
        import desktop_app as m
        with tempfile.TemporaryDirectory() as td, \
                patch.object(m,'STATE',Path(td)/'state'), \
                patch.object(m.DeepThorTDesktop,'_refresh_inventory',lambda self:None), \
                patch.object(m,'is_capped_windows_process',return_value=False), \
                patch.object(m.filedialog,'askopenfilename') as picker:
            app=m.DeepThorTDesktop()
            try:
                app._run_isolated_gui()
                picker.assert_not_called()
                self.assertFalse(app.gui_tests.snapshot()['history'])
            finally:app._quit()

if __name__=='__main__':unittest.main()
