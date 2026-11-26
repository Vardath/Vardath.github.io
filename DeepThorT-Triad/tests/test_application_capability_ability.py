import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local.tool_acquisition import ToolAcquisition
from deepthort_local.janus_engine import JanusStore

class AppCapabilityDiscoveryTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve()
        self.store=ToolAcquisition(self.root/'tools.db')
        self.janus=JanusStore(self.root/'janus.db')
        self.exe=self.root/'ffmpeg.exe';self.exe.write_bytes(b'test-binary')
        self.store.discover([{'name':'FFmpeg','location':str(self.exe),'found':True}])
    def probe(self):
        action=self.store.authorize_probe('FFmpeg',self.root,self.janus,user_approved=True)
        log=self.root/'probe.log'
        log.write_text('Options:\n-filter:a apply audio filter\n--codec specify codec\nsecret token do not show\n',encoding='utf-8')
        self.janus.update_action(action,'succeeded',detail='fixture',returncode=0,output_file=str(log))
        return log
    def test_no_unapproved_help_or_execution(self):
        with patch('subprocess.Popen',side_effect=AssertionError('no launch')):
            self.assertEqual(self.store.search_capabilities(self.janus,'audio filter'),[])
            self.assertEqual(self.janus.actions(),[])
        self.assertEqual(self.store.probe_command('FFmpeg'),[str(self.exe.resolve()),'-h'])
    def test_current_help_and_context(self):
        log=self.probe()
        with patch('subprocess.Popen',side_effect=AssertionError('no launch')):
            rows=self.store.search_capabilities(self.janus,'audio filter')
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['name'],'FFmpeg')
            self.assertIn('task unverified',rows[0]['scope'])
            self.assertIn('UNTRUSTED LOCAL HELP',self.store.discovery_context(self.janus,'audio filter'))
            self.assertEqual(self.store.search_capabilities(self.janus,'secret token'),[])
            self.assertEqual(len(self.janus.actions()),1)
            log.write_text('modified audio filter',encoding='utf-8')
            self.assertEqual(self.store.search_capabilities(self.janus,'audio filter'),[])
    def test_stale_executable_cancellation_and_limits(self):
        self.probe()
        self.assertEqual(self.store.search_capabilities(self.janus,'audio filter',cancelled=lambda:True),[])
        self.assertEqual(self.store.discovery_context(self.janus,'audio filter',max_chars=10),'')
        with self.assertRaises(ValueError):self.store.search_capabilities(self.janus,'audio',limit=9)
        with self.assertRaises(ValueError):self.store.search_capabilities(self.janus,'x'*2001)
        self.exe.write_bytes(b'updated binary with changed size')
        self.assertEqual(self.store.search_capabilities(self.janus,'audio filter'),[])
