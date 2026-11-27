import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import image_motion as m
from deepthort_local.texture_pixels import encode
from deepthort_local.action_guards import snapshot_file

class ImageMotionTests(unittest.TestCase):
    def spec(self):
        return {'image':'still.png','width':16,'height':16,'fps':24,'frames':3,'start':[0,0,16,16],'end':[16,16,16,16]}
    def image(self):
        return encode(32,32,'RGB',bytes(v for y in range(32) for x in range(32) for v in (x*8,y*8,64)))
    def test_crop_endpoints_and_motion(self):
        s=self.spec();raw,report=m.frames(self.image(),s)
        self.assertEqual(m.crop_at(s,0),(0,0,16,16))
        self.assertEqual(m.crop_at(s,2),(16,16,32,32))
        self.assertEqual(m.crop_at(s,1),(8,8,24,24))
        self.assertEqual(len(raw),3*16*16*3)
        self.assertNotEqual(raw[:768],raw[-768:])
        self.assertFalse(report['neural_motion_generated'])
    def test_geometry_and_static_refusal(self):
        s=self.spec()
        for change in ({'end':[0,0,16,16]},{'end':[0,0,16,15]},{'fps':60},{'frames':1}):
            with self.assertRaises(ValueError):m.checked(dict(s,**change))
        with self.assertRaises(ValueError):m.frames(self.image(),dict(s,end=[20,20,16,16]))
        flat=encode(32,32,'RGB',bytes([50])*32*32*3)
        with self.assertRaises(ValueError):m.frames(flat,s)
    def test_review_execution_and_stale_guard(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();raw=self.image();(root/'still.png').write_bytes(raw)
            (root/'motion.json').write_text(json.dumps(self.spec()),encoding='utf8')
            for n in ('ff','fp'):(root/n).write_bytes(n.encode())
            tools=tuple(snapshot_file(root/n) for n in ('ff','fp'))
            with patch.object(m,'installed',return_value=tools),patch.object(m,'encode_verified',return_value=b'fixture-mp4') as enc:
                plan,_=m.review(root,'motion.json','out.mp4')
                result=m.execute(root,plan)
                self.assertEqual(enc.call_args.args[1:4],((16,16),24,3))
                self.assertEqual(result['status'],'image_motion_pixels_verified')
                self.assertEqual((root/'still.png').read_bytes(),raw)
                with self.assertRaises(ValueError):m.execute(root,plan)
                plan,_=m.review(root,'motion.json','other.mp4')
                (root/'still.png').write_bytes(b'changed')
                with self.assertRaises(ValueError):m.execute(root,plan)
                self.assertFalse((root/'other.mp4').exists())

if __name__=='__main__':unittest.main()
