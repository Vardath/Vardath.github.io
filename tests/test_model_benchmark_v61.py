import unittest
from model_benchmark_score import CASES, code_result, score_case, score, Unsupported

class BenchmarkTests(unittest.TestCase):
    def test_independent_oracles(self):
        answers={
            'cargo':'def transfer(stock, capacity, requested):\n return min(stock,capacity,requested)',
            'ledger':'def balance(initial,payments):\n return initial+sum(payments)',
            'repair':'def eligible(hull,hostile):\n return hull<25 and hostile',
            'queue':'def next_job(jobs):\n for i, job in enumerate(jobs):\n  if job=="ready": return i\n return -1'}
        import json
        for c in CASES:
            a=answers[c['id']] if c['kind']=='code' else json.dumps(c['expected']) if c['kind']=='json' else c['expected']
            self.assertEqual(score_case(c,{'answer':a}),'pass',c['id'])
    def test_wrong_code_and_type_mismatch(self):
        c=next(c for c in CASES if c['id']=='cargo')
        self.assertEqual(score_case(c,{'answer':'def transfer(stock,capacity,requested): return requested'}),'fail')
        c=next(c for c in CASES if c['id']=='repair')
        self.assertEqual(score_case(c,{'answer':'def eligible(hull,hostile): return 1'}),'fail')
    def test_untrusted_source_not_executed(self):
        for text in ('import os\ndef f(x): return x','def f(x): return __import__("os")',
                     'def f(x): return x.__class__','def f(x): return [0]*1000000000'):
            with self.assertRaises(Unsupported):code_result(text,'f',[2])
    def test_absent_results_not_passed(self):
        s=score({'profile':'baseline','results':[]})
        self.assertEqual(s['passed'],0)
        self.assertTrue(all(x['status']=='not_run' for x in s['cases']))
    def test_json_duplicate_keys_and_ambiguous_review(self):
        c=next(c for c in CASES if c['id']=='tool_verify')
        self.assertEqual(score_case(c,{'answer':'{"tool":"done","tool":"request_verification","args":{}}'}),'fail')
        c=next(c for c in CASES if c['id']=='scope')
        self.assertEqual(score_case(c,{'answer':'REJECT or ACCEPT'}),'fail')
