"""v43 independent post-install evidence, PATH recovery and GUI routing."""
import hashlib
import os
import queue
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from deepthort_local.tool_verification import (
    PROBES, ToolVerificationStore, _candidate_paths, _allowed_basename,
    refreshed_path, verify_catalog_tool)


class CatalogVerifierTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.exe=self.root/'python.exe'
        self.exe.write_bytes(b'fake test executable')
        self.env={'PATH':str(self.root)}
    def tearDown(self):self.tmp.cleanup()

    def test_fixed_known_probe_and_version(self):
        calls=[]
        def run(args,**kw):
            calls.append((args,kw))
            return subprocess.CompletedProcess(args,0,'Python 3.13.1\n','')
        row=verify_catalog_tool('Python',environ=self.env,
            which=lambda x:str(self.exe) if x=='python.exe' else None,runner=run,
            project=str(self.root),install_exit_code=0)
        self.assertEqual(row['status'],'version_verified')
        self.assertEqual(row['version'],'Python 3.13')
        self.assertEqual(row['probe_argv'],[str(self.exe),'--version'])
        self.assertEqual(calls[0][1]['timeout'],12)
        self.assertEqual(calls[0][1]['shell'],False)
        self.assertFalse(row['functional_project_test_passed'])
        self.assertFalse(row['publisher_signature_verified'])

    def test_bad_output_not_verified_despite_zero_exit(self):
        row=verify_catalog_tool('Python',environ=self.env,
            which=lambda _:str(self.exe),
            runner=lambda args,**kw:subprocess.CompletedProcess(args,0,'No matching version',''))
        self.assertEqual(row['status'],'probe_failed')
        self.assertFalse(row['version'])

    def test_failure_or_timeout_not_version_verified(self):
        def bad(args,**kw):
            raise subprocess.TimeoutExpired(args,12)
        row=verify_catalog_tool('Python',environ=self.env,which=lambda _:str(self.exe),runner=bad)
        self.assertEqual(row['status'],'probe_failed')
        row=verify_catalog_tool('Python',environ=self.env,which=lambda _:str(self.exe),
              runner=lambda args,**kw:subprocess.CompletedProcess(args,10,'Python 3.13',''))
        self.assertEqual(row['status'],'probe_failed')

    def test_gui_software_never_started_automatically(self):
        exe=self.root/'studio64.exe';exe.write_bytes(b'android-studio')
        runner=MagicMock(side_effect=AssertionError('MUST NOT execute GUI'))
        row=verify_catalog_tool('Android Studio',environ=self.env,
            which=lambda x:str(exe) if x=='studio64.exe' else None,runner=runner)
        self.assertEqual(row['status'],'located_only')
        runner.assert_not_called()

    def test_no_registry_only_or_missing_file_claim(self):
        row=verify_catalog_tool('Python',environ={'PATH':''},
            which=lambda _:str(self.root/'missing-python.exe'),runner=MagicMock())
        self.assertEqual(row['status'],'not_found')

    def test_only_catalog_tools_and_bounded_timeout(self):
        with self.assertRaises(ValueError):verify_catalog_tool('unreviewed tool')
        with self.assertRaises(ValueError):verify_catalog_tool('Python',timeout=100)
        for name,probe in PROBES.items():
            self.assertIsInstance(probe[0],tuple)
            self.assertNotIn('cmd.exe',str(probe).lower())
            self.assertNotIn('powershell',str(probe).lower())
            self.assertNotIn('--script',str(probe).lower())

    def test_path_refresh_adds_win_get_links_without_global_mutation(self):
        local=self.root/'Local';links=local/'Microsoft'/'WinGet'/'Links'
        links.mkdir(parents=True)
        original=os.environ.get('PATH')
        env=refreshed_path({'PATH':'','LOCALAPPDATA':str(local)},registry_paths=[])
        self.assertIn(str(links),env['PATH'])
        self.assertEqual(os.environ.get('PATH'),original)

    def test_only_named_executables_and_no_symlinks(self):
        other=self.root/'evil.exe';other.write_bytes(b'anything')
        paths=_candidate_paths('Python',environ=self.env,which=lambda _:str(other))
        self.assertFalse(paths)
        self.assertFalse(_allowed_basename('Python',other))
        symlink=self.root/'second'/'python.exe'
        symlink.parent.mkdir()
        try:symlink.symlink_to(other)
        except OSError:self.skipTest('Symlinks unavailable')
        paths=_candidate_paths('Python',environ=self.env,which=lambda _:str(symlink))
        self.assertFalse(paths)

    def test_persist_and_invalidate_changed_executable(self):
        row=verify_catalog_tool('Python',environ=self.env,which=lambda _:str(self.exe),
                runner=lambda a,**k:subprocess.CompletedProcess(a,0,'Python 3.13.1',''))
        store=ToolVerificationStore(self.root/'verification.json')
        store.record(row)
        self.assertIsNotNone(ToolVerificationStore(store.path).current('Python'))
        self.exe.write_bytes(b'changed test executable')
        self.assertIsNone(store.current('Python'))
        self.assertEqual(store.get('Python')['status'],'version_verified')

    def test_store_rejects_forged_tool_rows(self):
        store=ToolVerificationStore(self.root/'verification.json')
        with self.assertRaises(ValueError):store.record({'schema':'bad','tool':'Python'})

    def test_store_has_bounded_history(self):
        store=ToolVerificationStore(self.root/'verification.json')
        row=verify_catalog_tool('Python',environ=self.env,which=lambda _:str(self.exe),
                runner=lambda a,**k:subprocess.CompletedProcess(a,0,'Python 3.13.1',''))
        for _ in range(125):store.record(row)
        import json
        data=json.loads(store.path.read_text())
        self.assertLessEqual(len(data['history']),120)


class DesktopToolProbeTests(unittest.TestCase):
    def app(self):
        obj=MagicMock()
        obj._quitting=False;obj._tool_probe_queue=[];obj._tool_probe_active=None
        obj.queue_paused=False;obj._auto_tool_active=None
        obj._auto_verification_in_flight=None
        obj.install_process=None;obj.tool_process=None;obj.media_process=None
        obj.disk_gate.gaming.return_value=False
        obj.events=queue.Queue()
        return obj

    def test_no_probing_during_game_or_paused(self):
        from desktop_app import DeepThorTDesktop
        for flag in ('game','paused','installer','test'):
            obj=self.app();obj._tool_probe_queue=[{'name':'Python','project':''}]
            if flag=='game':obj.disk_gate.gaming.return_value=True
            if flag=='paused':obj.queue_paused=True
            if flag=='installer':
                obj.install_process=MagicMock()
                obj.install_process.poll.return_value=None
            if flag=='test':obj._auto_verification_in_flight=8
            DeepThorTDesktop._tool_probe_tick(obj)
            self.assertEqual(len(obj._tool_probe_queue),1)

    def test_only_catalog_names_enqueue(self):
        from desktop_app import DeepThorTDesktop
        obj=self.app()
        DeepThorTDesktop._queue_catalog_verification(obj,'Unlisted EXE')
        self.assertFalse(obj._tool_probe_queue)
        DeepThorTDesktop._queue_catalog_verification(obj,'Python',project='C:/test')
        DeepThorTDesktop._queue_catalog_verification(obj,'Python',project='C:/test')
        self.assertEqual(len(obj._tool_probe_queue),1)

    def test_finished_probe_persisted_and_exposed_without_claiming_playtest(self):
        from desktop_app import DeepThorTDesktop
        obj=self.app()
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/'python.exe';exe.write_bytes(b'fake')
            row=verify_catalog_tool('Python',environ={'PATH':tmp},which=lambda _:str(exe),
                   runner=lambda a,**k:subprocess.CompletedProcess(a,0,'Python 3.13.1',''))
            obj._tool_verification=ToolVerificationStore(Path(tmp)/'state.json')
            obj._tool_probe_active={'name':'Python'}
            original=os.environ.get('PATH')
            try:DeepThorTDesktop._tool_probe_finished(obj,row)
            finally:os.environ['PATH']=original or ''
            self.assertIsNone(obj._tool_probe_active)
            self.assertIsNotNone(obj._tool_verification.current('Python'))
            obj._refresh_inventory.assert_called_once()
            self.assertIn('version_verified',str(obj._log.call_args_list))

if __name__=='__main__':unittest.main()

class InventoryIntegrityV43(unittest.TestCase):
    def test_registry_install_path_alone_not_treated_as_installed_executable(self):
        from deepthort_local.computer_inventory import detect_tools
        with tempfile.TemporaryDirectory() as tmp:
            inventory=detect_tools(which=lambda _:None,known_locations=[],
                     registry=[('python 3.13',tmp)])
            row=next(r for r in inventory if r.name=='Python')
            self.assertFalse(row.found)
            self.assertEqual(row.source,'Windows installed-app registry')

    def test_existing_exact_program_file_counts_not_registry_text(self):
        from deepthort_local.computer_inventory import detect_tools
        with tempfile.TemporaryDirectory() as tmp:
            candidate=Path(tmp)/'python.exe';candidate.write_bytes(b'executable bytes')
            inventory=detect_tools(which=lambda cmd: str(candidate) if cmd=='python.exe' else None,
                                   known_locations=[],registry=[])
            row=next(r for r in inventory if r.name=='Python')
            self.assertTrue(row.found)
