import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from deepthort_local.integration_suite import review,validate

SCRIPT=Path(__file__).resolve().parents[1]/'deepthort_local'/'integration_suite.py'

class PerformanceProfileTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();(self.root/'tests').mkdir()
        self.source=self.root/'app.py'
        self.source.write_text('def inner():\n    return sum(range(500))\ndef outer():\n    return inner()+inner()\n',encoding='utf-8')
        self.test=self.root/'tests'/'test_app.py'
    def execute(self,source):
        self.test.write_text(source,encoding='utf-8')
        plan=review(self.root,'tests',profile=True)
        run=subprocess.run([sys.executable,'-I','-B',str(SCRIPT),'--root',str(self.root),'--plan',json.dumps(plan)],
                           cwd=self.root,capture_output=True,text=True,timeout=30)
        return run.returncode,json.loads(run.stdout.splitlines()[-1])
    def test_actual_calls_and_scoped_timings(self):
        code,result=self.execute('import unittest\nfrom app import outer\nclass T(unittest.TestCase):\n def test_outer(self): self.assertEqual(outer(),249500)\n')
        self.assertEqual(code,0,result)
        p=result['profile'];self.assertEqual(p['status'],'measured')
        self.assertTrue(p['profile_intact'])
        self.assertGreater(p['elapsed_seconds'],0)
        self.assertGreaterEqual(p['process_cpu_seconds'],0)
        rows={r['function']:r for r in p['hotspots']}
        self.assertEqual(rows['inner']['calls'],2);self.assertEqual(rows['outer']['calls'],1)
        self.assertTrue(all(r['path']=='app.py' for r in rows.values()))
        self.assertGreaterEqual(rows['outer']['cumulative_seconds'],rows['outer']['self_seconds'])
        self.assertFalse(p['production_benchmark']);self.assertFalse(p['other_thread_function_profile'])
    def test_failed_and_mutated_runs_inconclusive(self):
        code,result=self.execute('import unittest\nfrom app import outer\nclass T(unittest.TestCase):\n def test_outer(self): self.assertEqual(outer(),0)\n')
        self.assertNotEqual(code,0);self.assertEqual(result['profile']['status'],'inconclusive')
        code,result=self.execute('import unittest\nfrom pathlib import Path\nfrom app import outer\nclass T(unittest.TestCase):\n def test_write(self): outer();Path("app.py").write_text("changed")\n')
        self.assertNotEqual(code,0);self.assertFalse(result['source_stable'])
        self.assertEqual(result['profile']['status'],'inconclusive')
    def test_disabled_profile_and_no_application_calls(self):
        code,result=self.execute('import unittest,sys\nfrom app import outer\nclass T(unittest.TestCase):\n def test_disable(self): outer();sys.setprofile(None)\n')
        self.assertNotEqual(code,0);self.assertFalse(result['profile']['profile_intact'])
        code,result=self.execute('import unittest\nclass T(unittest.TestCase):\n def test_empty_scope(self): self.assertTrue(True)\n')
        self.assertNotEqual(code,0);self.assertEqual(result['profile']['observed_project_functions'],0)
    def test_stale_and_conflicting_modes(self):
        self.test.write_text('import unittest\n',encoding='utf-8')
        with self.assertRaises(ValueError):review(self.root,'tests',coverage=True,profile=True)
        plan=review(self.root,'tests',profile=True)
        self.source.write_text('changed=1',encoding='utf-8')
        with self.assertRaises(ValueError):validate(self.root,plan)
