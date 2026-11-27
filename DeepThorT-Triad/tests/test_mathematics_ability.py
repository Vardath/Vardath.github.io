import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.mathematics import calculate,review,execute
def n(x):return {'number':x}
def op(name,a,b):return {'op':name,'args':[a,b]}
X={'variable':'x'}
class MathTests(unittest.TestCase):
    def test_exact_arithmetic(self):
        r=calculate({'expression':op('add',n('0.1'),n('1/3'))})
        self.assertEqual(r['result'],'13/30')
    def test_equations(self):
        r=calculate({'left':op('add',op('multiply',n('3'),X),n('1')),'right':n('8')})
        self.assertEqual(r['solution'],'7/3');self.assertEqual(r['left_at_solution'],'8')
        self.assertEqual(calculate({'left':X,'right':X})['solution'],'all_rationals')
        self.assertEqual(calculate({'left':X,'right':op('add',X,n('1'))})['solution'],'none')
    def test_invalid_and_bounds(self):
        for spec in ({'expression':op('divide',n('1'),n('0'))},{'left':op('multiply',X,X),'right':n('4')},{'expression':n('1e5')},{'expression':X}):
            with self.assertRaises(ValueError):calculate(spec)
        deep=n('1')
        for _ in range(18):deep=op('add',deep,n('1'))
        with self.assertRaises(ValueError):calculate({'expression':deep})
    def test_review_publish_and_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();src=root/'math.json';src.write_text(json.dumps({'expression':n('2/3')}))
            plan,preview=review(root,'math.json','out.json');execute(root,plan)
            self.assertEqual(json.loads((root/'out.json').read_text()),preview['exact_result'])
            (root/'out.json').unlink();src.write_text(json.dumps({'expression':n('5')}))
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'out.json').exists())
