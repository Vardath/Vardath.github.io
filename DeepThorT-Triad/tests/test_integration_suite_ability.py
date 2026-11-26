import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from deepthort_local.integration_suite import review,validate,fingerprint
SCRIPT=Path(__file__).resolve().parents[1]/'deepthort_local'/'integration_suite.py'
class IntegrationSuiteTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);(self.root/'integration_tests').mkdir()
        (self.root/'library.py').write_text('def value(): return 7\n',encoding='utf-8')
        self.test=self.root/'integration_tests'/'test_flow.py'
    def execute(self,source):
        self.test.write_text(source,encoding='utf-8')
        plan=review(self.root,'integration_tests')
        result=subprocess.run([sys.executable,'-I','-B',str(SCRIPT),'--root',str(self.root),'--plan',json.dumps(plan)],
                              cwd=self.root,capture_output=True,text=True,timeout=30)
        return result.returncode,json.loads(result.stdout.splitlines()[-1])
    def test_actual_cross_module_integration(self):
        code,result=self.execute('import unittest\nfrom library import value\nclass Flow(unittest.TestCase):\n def test_flow(self): self.assertEqual(value(),7)\n')
        self.assertEqual(code,0);self.assertEqual(result['status'],'passed')
        self.assertEqual(result['counts']['passed'],1);self.assertTrue(result['source_stable'])
        self.assertFalse(result['full_application_verified'])
    def test_failure_empty_and_skipped(self):
        code,result=self.execute('import unittest\nclass Flow(unittest.TestCase):\n def test_flow(self): self.assertEqual(1,2)\n')
        self.assertNotEqual(code,0);self.assertEqual(result['counts']['failed'],1)
        code,result=self.execute('# no tests\n')
        self.assertNotEqual(code,0);self.assertEqual(result['status'],'inconclusive')
        code,result=self.execute('import unittest\nclass Flow(unittest.TestCase):\n @unittest.skip("not available")\n def test_flow(self): pass\n')
        self.assertNotEqual(code,0);self.assertEqual(result['counts']['skipped'],1)
    def test_source_mutation_is_not_success(self):
        code,result=self.execute('import unittest\nfrom pathlib import Path\nclass Flow(unittest.TestCase):\n def test_flow(self): Path("library.py").write_text("changed",encoding="utf-8")\n')
        self.assertNotEqual(code,0);self.assertFalse(result['source_stable'])
    def test_stale_plan_and_unapproved_suite(self):
        self.test.write_text('import unittest\n',encoding='utf-8')
        plan=review(self.root,'integration_tests')
        (self.root/'library.py').write_text('changed',encoding='utf-8')
        with self.assertRaises(ValueError):validate(self.root,plan)
        with self.assertRaises(ValueError):review(self.root,'../other')
if __name__=='__main__':unittest.main()
