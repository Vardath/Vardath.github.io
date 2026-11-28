import json,random,tempfile,unittest
from pathlib import Path
from deepthort_local import multi_view_reconstruction as m
from deepthort_local.texture_pixels import encode

SPEC={'reference':'ref.png','views':[{'image':'a.png','baseline_m':.1},{'image':'b.png','baseline_m':.2}],
      'focal_px':100,'min_disparity':2,'max_disparity':10,'step':4,'max_error':0,'min_margin':5,
      'max_depth_error_m':.01,'max_reprojection_px':.1}
def images(second=8):
    w,h=64,24;rng=random.Random(87);ref=bytes(rng.randrange(256) for _ in range(w*h))
    out=[encode(w,h,'L',ref)]
    for shift in (4,second):
        data=bytearray(w*h)
        for y in range(h):data[y*w:y*w+w-shift]=ref[y*w+shift:(y+1)*w]
        out.append(encode(w,h,'L',bytes(data)))
    return out

class MultiViewTests(unittest.TestCase):
    def test_known_depth_and_consensus(self):
        r=m.reconstruct(images(),SPEC)
        self.assertGreater(len(r['points']),20)
        for q in r['points']:
            self.assertAlmostEqual(q['xyz_m'][2],2.5)
            self.assertEqual(len(q['views']),2)
            for v in q['views']:self.assertAlmostEqual(v['reprojection_error_px'],0)
        self.assertFalse(r['metric_accuracy_verified'])
    def test_inconsistent_views_and_baselines(self):
        with self.assertRaises(ValueError):m.reconstruct(images(6),SPEC)
        bad=dict(SPEC,views=[dict(SPEC['views'][0]),dict(SPEC['views'][1],baseline_m=.1)])
        with self.assertRaises(ValueError):m.checked(bad)
    def test_review_and_stale_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for name,data in zip(('ref.png','a.png','b.png'),images()):(root/name).write_bytes(data)
            (root/'spec.json').write_text(json.dumps(SPEC),encoding='utf8')
            plan,_=m.review(root,'spec.json','cloud.json')
            self.assertGreater(m.execute(root,plan)['point_count'],20)
            with self.assertRaises(ValueError):m.execute(root,plan)
            plan,_=m.review(root,'spec.json','other.json');(root/'b.png').write_bytes(images(6)[2])
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'other.json').exists())
if __name__=='__main__':unittest.main()
