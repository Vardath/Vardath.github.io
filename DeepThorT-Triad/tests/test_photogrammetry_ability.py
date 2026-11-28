import json,random,tempfile,unittest
from pathlib import Path
from deepthort_local import photogrammetry as m
from deepthort_local.texture_pixels import encode

SPEC={'left':'l.png','right':'r.png','focal_px':100,'baseline_m':.1,'min_disparity':2,
      'max_disparity':8,'step':4,'max_error':0,'min_margin':5}
def pair():
    w,h=64,24;rng=random.Random(87)
    left=bytes(rng.randrange(256) for _ in range(w*h));right=bytearray(w*h)
    for y in range(h):
        right[y*w:y*w+w-4]=left[y*w+4:(y+1)*w]
    return encode(w,h,'L',left),encode(w,h,'L',bytes(right))

class StereoTests(unittest.TestCase):
    def test_known_depth_and_reprojection(self):
        a,b=pair();r=m.reconstruct(a,b,SPEC)
        self.assertGreater(len(r['points']),20)
        for q in r['points']:
            self.assertEqual(q['disparity_px'],4)
            self.assertAlmostEqual(q['xyz_m'][2],2.5)
            self.assertAlmostEqual(100*q['xyz_m'][0]/q['xyz_m'][2]+31.5,q['left_xy'][0])
        self.assertFalse(r['metric_accuracy_verified'])
    def test_ambiguous_and_invalid(self):
        flat=encode(64,24,'L',bytes([100])*64*24)
        with self.assertRaises(ValueError):m.reconstruct(flat,flat,SPEC)
        for bad in (dict(SPEC,baseline_m=0),dict(SPEC,max_disparity=1),dict(SPEC,right='L.PNG')):
            with self.assertRaises(ValueError):m.checked(bad)
    def test_exact_sources_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);a,b=pair();(root/'l.png').write_bytes(a);(root/'r.png').write_bytes(b)
            (root/'spec.json').write_text(json.dumps(SPEC),encoding='utf8')
            plan,_=m.review(root,'spec.json','cloud.json')
            self.assertGreater(m.execute(root,plan)['point_count'],20)
            with self.assertRaises(ValueError):m.execute(root,plan)
            plan,_=m.review(root,'spec.json','other.json');(root/'r.png').write_bytes(a)
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'other.json').exists())
if __name__=='__main__':unittest.main()
