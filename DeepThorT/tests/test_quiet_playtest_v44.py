"""v44: fixed, quiet headless game smoke testing under the single existing CPU job."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from deepthort_local.quiet_playtest import (
    QuietPlaytestError, QuietTestStore, is_capped_windows_process,
    quiet_creationflags, plan_godot_scene, PLAYTEST_FRAMES)

class QuietPlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.project=self.root/'project'
        self.project.mkdir()
        self.exe=self.root/'godot.exe'
        self.exe.write_bytes(b'fake godot')
        self.scene=self.project/'main.tscn'
        self.scene.write_text('[gd_scene format=3]\n')
        self.config=self.project/'project.godot'
        self.config.write_text('[application]\nrun/main_scene="res://main.tscn"\n')
    def tearDown(self): self.tmp.cleanup()
    def plan(self):return plan_godot_scene(self.project,self.exe)

    def test_fixed_headless_argv_only(self):
        p=self.plan()
        self.assertEqual(p.argv,(str(self.exe),'--headless','--path',str(self.project),
                                 '--quit-after',str(PLAYTEST_FRAMES)))
        self.assertEqual(p.kind,'godot_headless_scene')
        self.assertIn('res://main.tscn',p.display())
        self.assertNotIn('--editor',p.argv)
        self.assertNotIn('--audio-driver',p.argv)  # headless supplies Dummy automatically

    def test_missing_declared_scene_blocked(self):
        self.config.write_text('[application]\n')
        with self.assertRaises(QuietPlaytestError):self.plan()
        self.config.write_text('[application]\nrun/main_scene="res://missing.tscn"\n')
        with self.assertRaises(QuietPlaytestError):self.plan()

    def test_no_path_traversal_symlink_or_fake_engine(self):
        self.config.write_text('[application]\nrun/main_scene="res://../evil.tscn"\n')
        with self.assertRaises(QuietPlaytestError):self.plan()
        self.config.write_text('[application]\nrun/main_scene="res://main.tscn"\n')
        self.scene.unlink()
        try:self.scene.symlink_to(self.exe)
        except OSError:self.skipTest('symlink unavailable')
        with self.assertRaises(QuietPlaytestError):self.plan()
        self.scene.unlink()
        self.scene.write_text('real scene')
        bad=self.root/'malware.exe';bad.write_bytes(b'fake')
        with self.assertRaises(QuietPlaytestError):plan_godot_scene(self.project,bad)

    def test_frame_timeout_and_path_bound(self):
        with self.assertRaises(QuietPlaytestError):plan_godot_scene(self.project,self.exe,frames=10000)
        with self.assertRaises(QuietPlaytestError):plan_godot_scene(self.project,self.exe,frames=0)
        self.assertTrue(plan_godot_scene(self.project,self.exe,frames=12))

    def test_uid_main_scene_accepted_as_engine_resolved_not_visual_proof(self):
        self.config.write_text('[application]\nrun/main_scene="uid://abcdef"\n')
        self.assertEqual(self.plan().main_scene,'uid://abcdef')

    def test_windows_guard_fails_closed_and_shared_budget_flags(self):
        self.assertFalse(is_capped_windows_process(os_name='posix',probe=lambda: True))
        self.assertFalse(is_capped_windows_process(os_name='nt',probe=lambda: False))
        with patch.dict(os.environ,{'DEEPTHORT_UNCAPPED_TEST':'1'}):
            self.assertFalse(is_capped_windows_process(os_name='nt',probe=lambda: True))
        self.assertTrue(is_capped_windows_process(os_name='nt',probe=lambda: True))
        self.assertEqual(quiet_creationflags(os_name='nt') & 0x08000040,0x08000040)
        self.assertEqual(quiet_creationflags(os_name='posix'),0)

    def test_receipt_persistence_interrupt_and_no_auto_replay(self):
        store=QuietTestStore(self.root/'state'/'quiet.json')
        p=self.plan();store.begin(p)
        with self.assertRaises(QuietPlaytestError):store.begin(p)
        fresh=QuietTestStore(store.path)
        stale=fresh.interrupt_stale()
        self.assertEqual(stale['status'],'interrupted_unknown')
        self.assertIsNone(fresh.snapshot()['active'])
        self.assertEqual(len(fresh.snapshot()['history']),1)
        self.assertIsNone(fresh.interrupt_stale())
        fresh.begin(p)
        row=fresh.finish(0,lines=['scene ready','Godot quit'])
        self.assertEqual(row['status'],'headless_smoke_passed')
        self.assertNotIn('visual',row['status'])
        self.assertEqual(len(fresh.snapshot()['history']),2)

    def test_corrupted_receipt_blocks_new_test(self):
        p=self.root/'quiet.json'
        p.write_text('{broken')
        with self.assertRaises(QuietPlaytestError): QuietTestStore(p).begin(self.plan())

    def test_low_priority_pressure_preemption(self):
        from deepthort_local.quiet_playtest import QuietPressureGuard
        g=QuietPressureGuard()
        self.assertEqual(g.should_preempt(game_active=True,cpu_busy_percent=94,ram_available_percent=20),'')
        self.assertEqual(g.should_preempt(game_active=True,cpu_busy_percent=94,ram_available_percent=20),'')
        self.assertIn('CPU',g.should_preempt(game_active=True,cpu_busy_percent=94,ram_available_percent=20))
        self.assertEqual(g.should_preempt(game_active=False,cpu_busy_percent=99,ram_available_percent=20),'')
        self.assertIn('RAM',g.should_preempt(game_active=True,cpu_busy_percent=40,ram_available_percent=5))
        self.assertIn('verify',g.should_preempt(game_active=True,cpu_busy_percent=None,ram_available_percent=None))

    def test_cpu_warmup_does_not_preempt_healthy_ram(self):
        from deepthort_local.quiet_playtest import QuietPressureGuard
        g=QuietPressureGuard()
        self.assertEqual(g.should_preempt(game_active=True,cpu_busy_percent=None,ram_available_percent=30),'')

    def test_receipt_failure_stop_bounded_history(self):
        store=QuietTestStore(self.root/'quiet.json')
        p=self.plan()
        for index in range(37):
            store.begin(p)
            store.finish(2 if index%2 else None,lines=['x'*1000]*80,
                         stopped=(index%3==0),error='launch failed' if index%3==1 else '')
        result=store.snapshot()
        self.assertEqual(len(result['history']),30)
        self.assertLessEqual(len(result['history'][-1]['lines']),40)
        self.assertLessEqual(len(result['history'][-1]['lines'][-1]),350)


class QuietDesktopTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requires Tk')
    def test_manual_headless_project_and_no_game_focus_or_modal(self):
        import desktop_app as m
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);proj=root/'project';proj.mkdir()
            (proj/'project.godot').write_text('[application]\nrun/main_scene="res://main.tscn"\n')
            (proj/'main.tscn').write_text('[gd_scene format=3]')
            engine=root/'godot.exe';engine.write_bytes(b'fake')
            with patch.object(m,'STATE',root/'state'), \
                 patch.object(m.DeepThorTDesktop,'_refresh_inventory',lambda self:None), \
                 patch.object(m,'godot_executable',return_value=str(engine)), \
                 patch.object(m,'is_capped_windows_process',return_value=True), \
                 patch.object(m.messagebox,'showerror') as error, \
                 patch.object(m.messagebox,'showwarning') as warning:
                app=m.DeepThorTDesktop()
                try:
                    app._set_project(proj)
                    captured=[]
                    app._start_command=lambda cmd,**kw: captured.append((cmd,kw)) or True
                    app._run_quiet_scene()
                    self.assertEqual(len(captured),1)
                    self.assertEqual(captured[0][1]['kind'],'quiet_playtest')
                    self.assertEqual(captured[0][0][1],'--headless')
                    self.assertEqual(app.quiet_tests.snapshot()['active']['main_scene'],'res://main.tscn')
                    app.events.put(('tool_end','Quiet Godot scene simulation','quiet_playtest',0,None,
                                    {'argv':captured[0][0],'lines':['Scene ran']}))
                    app._handle_events()
                    self.assertIsNone(app.quiet_tests.snapshot()['active'])
                    self.assertEqual(app.quiet_tests.snapshot()['history'][-1]['status'],'headless_smoke_passed')
                    error.assert_not_called();warning.assert_not_called()
                finally: app._quit()

    @unittest.skipUnless(os.environ.get('DISPLAY') and os.name!='nt','Simulated engine on Linux')
    def test_real_headless_process_while_foreground_game_detected(self):
        import desktop_app as m
        import time
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);proj=root/'project';proj.mkdir()
            (proj/'project.godot').write_text('[application]\nrun/main_scene="res://main.tscn"\n')
            (proj/'main.tscn').write_text('[gd_scene format=3]')
            engine=root/'godot';engine.write_text('#!/bin/sh\necho "Simulated headless scene launched"\nexit 0\n')
            engine.chmod(0o755)
            with patch.object(m,'STATE',root/'state'), \
                 patch.object(m.DeepThorTDesktop,'_refresh_inventory',lambda self:None), \
                 patch.object(m,'godot_executable',return_value=str(engine)), \
                 patch.object(m,'is_capped_windows_process',return_value=True), \
                 patch.object(m.messagebox,'showerror') as err:
                app=m.DeepThorTDesktop()
                try:
                    app._set_project(proj)
                    app.disk_gate.gaming=lambda:True
                    app._run_quiet_scene()
                    deadline=time.monotonic()+8
                    while time.monotonic()<deadline:
                        app._handle_events();app.update_idletasks()
                        if app.quiet_tests.snapshot()['history']:break
                        time.sleep(0.03)
                    history=app.quiet_tests.snapshot()['history']
                    self.assertEqual(len(history),1)
                    self.assertEqual(history[0]['status'],'headless_smoke_passed')
                    self.assertIn('Simulated headless',str(history[0]['lines']))
                    err.assert_not_called()
                finally:app._quit()

    @unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requires Tk')
    def test_uncapped_gui_cannot_launch_hidden_game(self):
        import desktop_app as m
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with patch.object(m,'STATE',root/'state'), \
                 patch.object(m.DeepThorTDesktop,'_refresh_inventory',lambda self:None), \
                 patch.object(m,'is_capped_windows_process',return_value=False):
                app=m.DeepThorTDesktop()
                try:
                    app._start_command=MagicMock(return_value=True)
                    app._run_quiet_scene()
                    app._start_command.assert_not_called()
                finally: app._quit()

if __name__=='__main__': unittest.main()
