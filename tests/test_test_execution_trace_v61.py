import hashlib
import sys
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.test_execution_trace import build_trace,named_results,receipt,describe
from deepthort_local.verification_evidence import assess_verification,attach_verification
from deepthort_local.semantic_reconciliation import capture_verified_sources,verified_sources_current

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
    def test_skip_and_incomplete_verbose_run_not_accepted(self):
        argv=[sys.executable,'-m','unittest','discover','-v']
        for lines in (['Ran 1 test in 0.001s','OK'],
                      ["test_add (test_main.TestAdd.test_add) ... skipped 'later'",'Ran 1 test in 0.001s','OK (skipped=1)']):
            self.assertFalse(assess_verification(argv,0,lines)['accepted'])
    def test_receipt_stale_when_predecessor_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'test_main.py').write_text(SOURCE)
            (root/'main.py').write_text('def add(a,b):return a+b\n')
            hashes={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ('test_main.py','main.py')}
            job={'id':1,'project':tmp,'state':'running'}
            steps=[{'path':'test_main.py','description':'Test addition; verifies: REQ-1'}]
            original='REQ-1. Addition returns the sum.'
            argv=[sys.executable,'-m','unittest','discover','-v']
            lines=['test_add (test_main.TestAdd.test_add) ... ok','Ran 1 test in 0.001s','OK']
            output={'argv':argv,'regression_before':hashes,'regression_after':hashes,'lines':lines}
            trace=build_trace(job,steps,original,output,0)
            check=assess_verification(argv,0,lines);check['named_tests']=receipt(trace,check,argv)
            snap=attach_verification(capture_verified_sources(root,steps),check,argv)
            self.assertTrue(verified_sources_current(root,steps,snap))
            job.update(state='complete',result=json.dumps(snap))
            self.assertIn('Bound to completed',describe(trace,job,original))
            (root/'main.py').write_text('def add(a,b):return a-b\n')
            self.assertFalse(verified_sources_current(root,steps,snap))
            self.assertIn('STALE',describe(trace,job,original))
    def test_missing_approved_case_blocks_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'test_main.py').write_text(SOURCE)
            hashes={'test_main.py':hashlib.sha256((root/'test_main.py').read_bytes()).hexdigest()}
            argv=[sys.executable,'-m','unittest','discover','-v']
            lines=['test_other (test_other.TestOther.test_other) ... ok','Ran 1 test in 0.001s','OK']
            trace=build_trace({'id':1,'project':tmp},[{'path':'test_main.py','description':'Test addition'}],'Add numbers',
                {'argv':argv,'regression_before':hashes,'regression_after':hashes,'lines':lines},0)
            with self.assertRaises(ValueError):receipt(trace,assess_verification(argv,0,lines),argv)
if __name__=='__main__':unittest.main()

