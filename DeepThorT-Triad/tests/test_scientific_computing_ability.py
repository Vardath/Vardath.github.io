import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.scientific_computing import calculate,review,execute
SYSTEM={'operation':'solve_linear_system','matrix':[['2','1'],['1','-1']],'rhs':['7','2']}
INTEGRAL={'operation':'integrate_polynomial','coefficients':['1','2','3'],'lower':'0','upper':'2'}
class ScientificTests(unittest.TestCase):
    def test_exact_system_and_pivot(self):
        r=calculate(SYSTEM);self.assertEqual([v['exact'] for v in r['solution']],['3','1'])
        self.assertTrue(r['substitution_verified'])
        r=calculate(dict(SYSTEM,matrix=[['0','1'],['1','0']],rhs=['5','2']))
        self.assertEqual([v['exact'] for v in r['solution']],['2','5'])
    def test_singular_and_inconsistent(self):
        r=calculate(dict(SYSTEM,matrix=[['1','2'],['2','4']],rhs=['3','6']))
        self.assertEqual(r['status'],'non_unique');self.assertIsNone(r['solution'])
        self.assertEqual(calculate(dict(SYSTEM,matrix=[['1','2'],['2','4']],rhs=['3','7']))['status'],'inconsistent')
    def test_polynomial_and_reversed_bounds(self):
        r=calculate(INTEGRAL);self.assertEqual(r['integral']['exact'],'14')
        self.assertTrue(r['independent_evaluation_verified'])
        self.assertEqual(calculate(dict(INTEGRAL,lower='2',upper='0'))['integral']['exact'],'-14')
    def test_source_guard_and_exact_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'spec.json').write_text(json.dumps(SYSTEM),encoding='utf-8')
            plan,_=review(root,'spec.json','result.json')
            self.assertEqual(execute(root,plan)['result_status'],'unique')
            self.assertEqual(json.loads((root/'result.json').read_text()),calculate(SYSTEM))
            plan,_=review(root,'spec.json','later.json')
            (root/'spec.json').write_text(json.dumps(INTEGRAL),encoding='utf-8')
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'later.json').exists())
