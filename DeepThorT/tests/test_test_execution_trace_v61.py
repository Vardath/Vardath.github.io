import hashlib
import tempfile
import unittest
from pathlib import Path
from deepthort_local.test_execution_trace import build_trace,named_results

SOURCE='import unittest\nfrom main import add\nclass TestAdd(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(2,3),5)\n'
class TraceTests(unittest.TestCase):
    def test_names_and_duplicate_rejection(self):
        line='test_add (test_main.TestAdd.test_add) ... ok'
        self.assertEqual(named_results([line]),{'test_main.TestAdd.test_add':'passed'})
        self.assertEqual(named_results([line,line]),{})
    def test_requirement_status_and_missing_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'test_main.py').write_text(SOURCE)
            digest=hashlib.sha256((root/'test_main.py').read_bytes()).hexdigest()
            job={'id':1,'project':tmp}
            steps=[{'path':'test_main.py','description':'Test actual addition; verifies: REQ-1'}]
            original='REQ-1. Addition returns the sum.\nREQ-2. Subtraction returns the difference.'
            output={'argv':['python','-m','unittest','discover','-v'],
                    'regression_before':{'test_main.py':digest},'regression_after':{'test_main.py':digest},
                    'lines':['test_add (test_main.TestAdd.test_add) ... ok','Ran 1 test in 0.001s','OK']}
            trace=build_trace(job,steps,original,output,0)
            self.assertEqual(trace['counts'],{'passed':1})
            self.assertEqual(trace['requirement_counts'],{'linked_tests_passed':1,'no_linked_test':1})
            output['lines'][0]=output['lines'][0].replace('ok','FAIL')
            self.assertEqual(build_trace(job,steps,original,output,1)['requirement_counts']['failed'],1)
            output['lines']=['Ran 1 test in 0.001s','OK']
            self.assertEqual(build_trace(job,steps,original,output,0)['requirement_counts']['written_not_confirmed'],1)
            output['regression_after']={}
            with self.assertRaises(ValueError):build_trace(job,steps,original,output,0)
if __name__=='__main__':unittest.main()
