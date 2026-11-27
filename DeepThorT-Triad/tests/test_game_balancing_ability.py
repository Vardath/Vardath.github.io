import copy
import json
from pathlib import Path
import tempfile
import unittest
from deepthort_local import game_balancing as tool

class GridBalancingTests(unittest.TestCase):
    def spec(self):
        return {'target_steps':10,'level':{'title':'Balance','width':5,'height':5,'cell_size':24,
            'start':[0,0],'goal':[4,0],'walls':[],'collectibles':[[2,4]]}}

    def test_candidate_improves_without_mutating_input(self):
        s=self.spec();original=copy.deepcopy(s);r=tool.balance(s)
        self.assertEqual(s,original)
        self.assertEqual(r['baseline_steps'],12)
        self.assertEqual(r['candidate_steps'],10)
        self.assertTrue(r['target_met'])
        self.assertTrue(r['improved'])
        self.assertEqual(r['candidate_level']['collectibles'],[[2,3]])
        self.assertFalse(r['human_difficulty_verified'])

    def test_exact_and_unattainable_targets(self):
        s=self.spec();s['target_steps']=12;r=tool.balance(s)
        self.assertEqual(r['candidates_evaluated'],0);self.assertFalse(r['improved'])
        s['target_steps']=1;r=tool.balance(s)
        self.assertFalse(r['target_met']);self.assertLessEqual(r['candidates_evaluated'],32)
        s['target_steps']=True
        with self.assertRaises(ValueError):tool.balance(s)

    def test_review_publish_and_stale_source(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();src=root/'input.json';src.write_text(json.dumps(self.spec()))
            plan,_=tool.review(root,'input.json','output.json')
            src.write_text(json.dumps(self.spec())+' ')
            with self.assertRaises(ValueError):tool.execute(root,plan)
            plan,_=tool.review(root,'input.json','output.json')
            result=tool.execute(root,plan)
            self.assertEqual(result['candidate_steps'],10)
            self.assertEqual(json.loads((root/'output.json').read_text())['candidate_level']['collectibles'],[[2,3]])
            with self.assertRaises(ValueError):tool.execute(root,plan)

if __name__=='__main__':unittest.main()
