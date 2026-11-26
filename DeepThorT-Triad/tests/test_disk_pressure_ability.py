import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from deepthort_local.disk_gate import storage_pressure,require_storage,STATE_RESERVE_BYTES,INSTALL_RESERVE_BYTES

class DiskPressureTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve()
        self.state=self.root/'state';self.state.mkdir()
        self.project=self.root/'project';self.project.mkdir()
        self.temp=self.root/'temp';self.temp.mkdir()
        self.values={p:2*INSTALL_RESERVE_BYTES for p in (self.state,self.project,self.temp,self.root)}
    def usage(self,path):
        return SimpleNamespace(free=self.values[path])
    def test_project_and_temp_pressure_separate(self):
        self.values[self.project]=STATE_RESERVE_BYTES-1
        self.values[self.temp]=0
        r=storage_pressure(self.state,self.project,temp=self.temp,usage=self.usage)
        self.assertFalse(r['ready']);self.assertEqual(r['blocked'],['temporary','project'])
        self.assertTrue(self.project.is_dir());self.assertFalse(r['cleanup_performed'])
        with self.assertRaisesRegex(ValueError,'Storage pressure'):
            require_storage(self.state,self.project,temp=self.temp,usage=self.usage)
        self.values[self.project]=self.values[self.temp]=STATE_RESERVE_BYTES
        self.assertTrue(require_storage(self.state,self.project,temp=self.temp,usage=self.usage)['ready'])
    def test_install_reserve_checks_application(self):
        self.values[self.root]=INSTALL_RESERVE_BYTES-1
        r=storage_pressure(self.state,self.project,temp=self.temp,app_root=self.root,install=True,usage=self.usage)
        self.assertEqual(r['blocked'],['application'])
        self.assertEqual(r['reserve_bytes'],INSTALL_RESERVE_BYTES)
    def test_missing_and_unmeasurable_fail_closed(self):
        r=storage_pressure(self.state,self.root/'missing',temp=self.temp,usage=self.usage)
        self.assertEqual(r['targets']['project']['status'],'unknown')
        def broken(path):raise OSError('unavailable')
        r=storage_pressure(self.state,temp=self.temp,usage=broken)
        self.assertFalse(r['ready']);self.assertEqual(r['targets']['state']['status'],'unknown')
    def test_general_scope_and_real_capacity(self):
        r=storage_pressure(self.state,'(general)',temp=self.temp)
        self.assertNotIn('project',r['targets'])
        self.assertIsInstance(r['targets']['state']['free_bytes'],int)
        self.assertFalse(r['io_cap_enforced'])
