import json,tempfile,unittest
from pathlib import Path
from deepthort_local import game_asset_optimisation as g
from deepthort_local.scene_composition import decode
RAW=b'v 0 0 0\nv 0.01 0 0\nv 2 0 0\nv 0 2 0\nf 1 2 4\nf 2 3 4\n'
SPEC={'mesh':'source.obj','triangle_budget':1,'vertex_budget':3,'cell_sizes':[.001,.1,10],
      'max_displacement':.02,'max_position_error':.001,'preserve_boundary':False}
class OptimisationTests(unittest.TestCase):
    def test_select_candidate_meeting_budgets(self):
        payload,r=g.optimise(RAW,SPEC);d,_=decode(payload)
        self.assertEqual(r['selected_cell_size'],.1)
        self.assertEqual((r['output_triangles'],r['output_vertices']),(1,3))
        self.assertEqual(len(d['meshes']),1)
        self.assertLessEqual(r['maximum_cluster_displacement'],.02)
        self.assertTrue(r['budget_verified']);self.assertFalse(r['game_engine_import_verified'])
    def test_refuse_impossible_budget_and_keep_baseline(self):
        for change in ({'preserve_boundary':True},{'max_displacement':.001},{'cell_sizes':[.001]}):
            with self.subTest(change=change),self.assertRaises(ValueError):g.optimise(RAW,dict(SPEC,**change))
        _,r=g.optimise(RAW,dict(SPEC,triangle_budget=2,vertex_budget=4))
        self.assertEqual(r['selected_cell_size'],0)
        with self.assertRaises(ValueError):g.checked(dict(SPEC,cell_sizes=[.1,.1]))
    def test_guarded_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'source.obj';src.write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(SPEC))
            plan,_=g.review(root,'spec.json','asset.glb')
            self.assertEqual(g.execute(root,plan)['status'],'static_asset_budget_verified')
            self.assertEqual(src.read_bytes(),RAW)
            with self.assertRaises(ValueError):g.execute(root,plan)
            (root/'asset.glb').unlink();src.write_bytes(RAW+b'# changed\n')
            with self.assertRaises(ValueError):g.execute(root,plan)
            self.assertFalse((root/'asset.glb').exists())
