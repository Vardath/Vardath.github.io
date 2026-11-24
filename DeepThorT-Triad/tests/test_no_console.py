"""Regression coverage for focus-stealing watchdog/game polling."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import disk_gate, win_cpu_cap


class NoConsolePollingTests(unittest.TestCase):
    def test_native_process_match_casefold_without_spawning_tasklist(self):
        with patch.object(disk_gate.os, 'name', 'nt'):
            with patch.object(disk_gate, '_windows_process_names',
                              return_value=frozenset({'explorer.exe', 'rimworldwin64.exe'})) as scan:
                self.assertTrue(disk_gate.games_running(frozenset({'rimworldwin64.exe'})))
                self.assertFalse(disk_gate.games_running(frozenset({'x4.exe'})))
                self.assertEqual(scan.call_count, 2)

    def test_process_inspection_error_pauses_background_io(self):
        with patch.object(disk_gate.os, 'name', 'nt'):
            with patch.object(disk_gate, '_windows_process_names', side_effect=OSError('blocked')):
                self.assertTrue(disk_gate.games_running(frozenset({'x4.exe'})))

    def test_missing_game_configuration_does_not_scan(self):
        with patch.object(disk_gate, '_windows_process_names', side_effect=AssertionError('should not scan')):
            self.assertFalse(disk_gate.games_running(frozenset()))

    def test_gaming_detection_uses_short_cache_and_flag(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            flag=base/'game-active.flag'
            checks=[]
            def probe():
                checks.append(1)
                return False
            gate=disk_gate.DiskGate(game_flag=flag, game_names_path=base/'games',game_probe=probe)
            self.assertFalse(gate.gaming())
            self.assertFalse(gate.gaming())
            self.assertEqual(len(checks),1)
            flag.touch()
            self.assertTrue(gate.gaming())

    def test_supervised_console_program_receives_no_window_flag(self):
        # CreateProcessW flags in the actual resource-capped launcher.
        from inspect import getsource
        self.assertEqual(win_cpu_cap.CREATE_NO_WINDOW,0x08000000)
        self.assertIn('CREATE_SUSPENDED | IDLE_PRIORITY_CLASS | CREATE_NO_WINDOW,',
                      getsource(win_cpu_cap.run_capped))

    def test_no_command_shell_dependency_in_background_game_detection(self):
        from inspect import getsource
        source=getsource(disk_gate.games_running)+getsource(disk_gate._windows_process_names)
        self.assertNotIn('subprocess.',source)
        self.assertNotIn('tasklist.exe',source.replace('tasklist.exe, PowerShell, cmd.exe',''))

if __name__=='__main__':unittest.main()
