import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from deepthort_local.integration_suite import review,validate

SCRIPT=Path(__file__).resolve().parents[1]/'deepthort_local'/'integration_suite.py'

class TestCoverageAbility(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve()
        self.tests=self.root/'tests';self.tests.mkdir()
        self.source=self.root/'app.py'
        self.source.write_text('def choice(flag):\n    if flag:\n        return 1\n    return 2\n',encoding='utf-8')
        (self.root/'unused.py').write_text('value = 7\n',encoding='utf-8')
        self.test=self.tests/'test_app.py'
    def execute(self,source):
        self.test.write_text(source,encoding='utf-8')
        plan=review(self.root,'tests',coverage=True)
        run=subprocess.run([sys.executable,'-I','-B',str(SCRIPT),'--root',str(self.root),'--plan',json.dumps(plan)],
                           cwd=self.root,capture_output=True,text=True,timeout=30)
        return run.returncode,json.loads(run.stdout.splitlines()[-1])
    def test_real_line_hits_include_unimported_files(self):
        code,result=self.execute('import unittest\nfrom app import choice\nclass T(unittest.TestCase):\n def test_choice(self): self.assertEqual(choice(True),1)\n')
        self.assertEqual(code,0,result)
        cov=result['coverage'];self.assertEqual(cov['status'],'measured')
        self.assertEqual(cov['source_files'],2)
        self.assertGreater(cov['percent'],0);self.assertLess(cov['percent'],100)
        rows={r['path']:r for r in cov['details']}
        self.assertIn(4,rows['app.py']['missing_lines'])
        self.assertEqual(rows['unused.py']['covered_lines'],0)
        self.assertNotIn('tests/test_app.py',rows)
        self.assertFalse(cov['branch_coverage']);self.assertFalse(cov['complete_application_verified'])
    def test_failing_and_mutating_suites_are_inconclusive(self):
        code,result=self.execute('import unittest\nfrom app import choice\nclass T(unittest.TestCase):\n def test_choice(self): self.assertEqual(choice(True),2)\n')
        self.assertNotEqual(code,0);self.assertIsNone(result['coverage']['percent'])
        code,result=self.execute('import unittest\nfrom pathlib import Path\nclass T(unittest.TestCase):\n def test_write(self): Path("app.py").write_text("changed")\n')
        self.assertNotEqual(code,0);self.assertFalse(result['source_stable'])
        self.assertEqual(result['coverage']['status'],'inconclusive')
    def test_unparseable_and_trace_disabled(self):
        (self.root/'bad.py').write_text('def missing(',encoding='utf-8')
        code,result=self.execute('import unittest\nfrom app import choice\nclass T(unittest.TestCase):\n def test_choice(self): self.assertEqual(choice(True),1)\n')
        self.assertEqual(code,0,result)
        self.assertEqual(result['coverage']['status'],'partial')
        self.assertEqual(result['coverage']['omitted_source_files'],1)
        code,result=self.execute('import unittest,sys\nclass T(unittest.TestCase):\n def test_trace(self): sys.settrace(None)\n')
        self.assertNotEqual(code,0);self.assertFalse(result['coverage']['trace_intact'])
        self.assertIsNone(result['coverage']['percent'])
    def test_stale_review_rejected(self):
        self.test.write_text('import unittest\n',encoding='utf-8')
        plan=review(self.root,'tests',coverage=True)
        self.source.write_text('changed=1',encoding='utf-8')
        with self.assertRaises(ValueError):validate(self.root,plan)
