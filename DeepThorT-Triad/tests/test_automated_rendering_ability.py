import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import automated_rendering as r
from deepthort_local.texture_pixels import decode
RAW=b'v -1 -1 0\nv 1 -1 0\nv 0 1 0\nf 1 2 3\n'
A={'name':'back','mesh':'a.obj','translation':[0,0,0],'rotation_xyzw':[0,0,0,1],'scale':[1,1,1]}
B=dict(A,name='front',mesh='b.obj',translation=[0,0,1])
SPEC={'objects':[B,A],'max_position_error':.001,'view_azimuth_deg':0,'elevation_deg':0,
      'key_lux':1000,'preset':'neutral','width':64,'height':64,'colors':[[240,0,0],[0,0,240]],'background':[5,6,7]}
class RenderTests(unittest.TestCase):
    def test_actual_pixels_and_depth(self):
        raw,receipt=r.render([RAW,RAW],SPEC)
        w,h,mode,pixels=decode(raw,('RGB',));self.assertEqual((w,h,mode),(64,64,'RGB'))
        self.assertEqual(pixels[:3],bytes([5,6,7]))
        center=pixels[3*(32*64+32):3*(32*64+32)+3]
        self.assertGreater(center[0],0);self.assertEqual(center[2],0)
        self.assertGreater(receipt['visible_pixels'],500)
        self.assertTrue(receipt['render_verified']);self.assertFalse(receipt['visual_quality_verified'])
        reverse=dict(SPEC,objects=[A,B],colors=[[0,0,240],[240,0,0]])
        self.assertEqual(r.render([RAW,RAW],reverse)[0],raw)
    def test_limits(self):
        for k,v in [('width',513),('height',True),('elevation_deg',90),('colors',[[256,0,0],[0,0,0]])]:
            with self.subTest(k=k),self.assertRaises(ValueError):r.checked(dict(SPEC,**{k:v}))
        with patch.object(r,'MAX_WORK',100),self.assertRaises(ValueError):r.render([RAW,RAW],SPEC)
    def test_source_and_output_guards(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'a.obj').write_bytes(RAW);(root/'b.obj').write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(SPEC))
            plan,_=r.review(root,'spec.json','preview.png')
            self.assertEqual(r.execute(root,plan)['status'],'static_preview_rendered')
            with self.assertRaises(ValueError):r.execute(root,plan)
            (root/'preview.png').unlink();(root/'b.obj').write_bytes(RAW+b'# changed\n')
            with self.assertRaises(ValueError):r.execute(root,plan)
            self.assertFalse((root/'preview.png').exists())
