import tempfile
import unittest
from pathlib import Path
from deepthort_local.source_security import review,scan,indicators

class SourceSecurityTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve()
        self.source=self.root/'example.py'
    def test_indicators_and_safe_alternatives(self):
        raw=b"""import subprocess as sp
from pickle import loads
import yaml
import requests
import tempfile
sp.run(['echo','hello'],shell=True)
loads(b'x')
yaml.load('x',Loader=yaml.SafeLoader)
yaml.load('x',Loader=yaml.Loader)
requests.get('https://example.com',verify=False)
tempfile.mktemp()
eval('2')
sp.run(['echo','hello'],shell=False)
"""
        rules={i['rule'] for i in indicators(raw)}
        self.assertEqual(rules,{'SHELL_EXECUTION','UNSAFE_DESERIALIZATION','YAML_REVIEW_LOADER','TLS_VERIFICATION_DISABLED','UNSAFE_TEMP_NAME','DYNAMIC_CODE'})
        self.assertEqual(len(indicators(raw)),6)
    def test_exclusions_and_no_execution(self):
        self.source.write_text("raise RuntimeError('must not execute')\neval('2')\n",encoding='utf-8')
        (self.root/'secrets.py').write_text("eval('3')",encoding='utf-8')
        private=self.root/'private';private.mkdir()
        (private/'hidden.py').write_text("eval('4')",encoding='utf-8')
        plan=review(self.root,['private'])
        result=scan(self.root,plan)
        self.assertEqual(result['finding_count'],1)
        self.assertEqual(result['findings'][0]['path'],'example.py')
        self.assertEqual(result['findings'][0]['line'],2)
        self.assertFalse(result['source_executed'])
        self.assertFalse(result['complete_security_verified'])
    def test_stale_and_unparsed(self):
        self.source.write_text('def bad(',encoding='utf-8')
        plan=review(self.root)
        result=scan(self.root,plan)
        self.assertEqual(result['status'],'inconclusive')
        self.assertEqual(result['unparsed_files'],1)
        self.source.write_text('print(2)',encoding='utf-8')
        with self.assertRaises(ValueError):scan(self.root,plan)
        self.assertEqual(scan(self.root,review(self.root))['status'],'no_indicators_in_scanned_python')
    def test_truncated_findings(self):
        self.source.write_text("eval('2')\n"*250,encoding='utf-8')
        result=scan(self.root,review(self.root))
        self.assertEqual(result['finding_count'],250)
        self.assertTrue(result['truncated'])
        self.assertEqual(len(result['findings']),200)
