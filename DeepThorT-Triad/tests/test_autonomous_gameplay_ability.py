import unittest
from deepthort_local.autonomous_gameplay import route, expected, fixture, assess_log, MARKER

class AutonomousGameplayTests(unittest.TestCase):
    def spec(self):
        return {'title':'Test','width':5,'height':5,'cell_size':24,
                'start':[0,0],'goal':[4,4],'walls':[[1,0],[1,1]],
                'collectibles':[[0,2],[3,2]]}

    def test_route_avoids_walls_and_reaches_objective(self):
        s=self.spec();steps=route(s)
        self.assertEqual(steps[-1][1:],((4,4),0,True))
        self.assertTrue(all(list(step[1]) not in s['walls'] for step in steps))
        self.assertEqual(steps[0][0],'KEY_DOWN')
        script,receipt=fixture(s)
        self.assertIn('Input.parse_input_event',script)
        self.assertNotIn('game._move',script)
        self.assertEqual(receipt['input_steps'],len(steps))

    def test_exact_ordered_native_trace(self):
        s=self.spec();rows=expected(s)
        log='\n'.join(MARKER+x for x in rows)
        self.assertTrue(assess_log(s,log)['native_grid_objective_verified'])
        for invalid in (log+'\nERROR: broken', '\n'.join(MARKER+x for x in rows[:-1]), log+'\n'+MARKER+rows[-1]):
            with self.assertRaises(ValueError):
                assess_log(s,invalid)

if __name__=='__main__':unittest.main()
