import copy,json,tempfile,unittest
from pathlib import Path
from deepthort_local import physics_simulation as p
SPEC={'gravity':10,'duration_seconds':2,'fps':20,'floor_y':0,
      'bodies':[{'name':'ball','radius':1,'position':[0,6,0],'velocity':[2,0,0],'restitution':.5}]}
class PhysicsTests(unittest.TestCase):
    def test_analytic_drop_and_bounce(self):
        raw,r=p.simulate(SPEC);track=json.loads(raw)['tracks'][0];rows=track['samples'];hit=track['impacts'][0]
        self.assertAlmostEqual(rows[10]['position'][1],4.75)
        self.assertAlmostEqual(hit['time'],1)
        self.assertAlmostEqual(hit['vertical_before'],-10);self.assertAlmostEqual(hit['vertical_after'],5)
        self.assertAlmostEqual(rows[30]['position'][1],2.25)
        self.assertAlmostEqual(rows[-1]['position'][0],4)
        self.assertTrue(all(row['position'][1]>=1 for row in rows))
        self.assertTrue(r['trajectory_roundtrip_verified']);self.assertFalse(r['inter_body_collisions'])
    def test_rest_and_invalid(self):
        s=copy.deepcopy(SPEC);s['bodies'][0].update(position=[0,1,0],restitution=0)
        raw,_=p.simulate(s);track=json.loads(raw)['tracks'][0]
        self.assertTrue(track['resting_at_end']);self.assertTrue(all(row['position'][1]==1 for row in track['samples']))
        with self.assertRaises(ValueError):p.checked(dict(SPEC,gravity=0))
        s['bodies'][0]['position'][1]=.5
        with self.assertRaises(ValueError):p.checked(s)
    def test_guarded_trajectory(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'spec.json';src.write_text(json.dumps(SPEC))
            plan,_=p.review(root,'spec.json','trajectory.json')
            self.assertEqual(p.execute(root,plan)['status'],'floor_trajectory_verified')
            with self.assertRaises(ValueError):p.execute(root,plan)
            (root/'trajectory.json').unlink();src.write_text(json.dumps(dict(SPEC,gravity=9)))
            with self.assertRaises(ValueError):p.execute(root,plan)
            self.assertFalse((root/'trajectory.json').exists())
