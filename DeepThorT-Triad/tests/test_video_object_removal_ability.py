import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import video_object_removal as m
from deepthort_local.texture_pixels import encode
from deepthort_local.action_guards import snapshot_file

class VideoRemovalTests(unittest.TestCase):
    def spec(self):return {'video':'clip.mp4','plate':'plate.png','mask':'mask.png','start_frame':0,'end_frame':2}
    def test_mask_and_preservation(self):
        original=bytes([255,0,0,0,255,0])*2;plate=bytes([0,0,255])*2
        out,r=m.remove(original,plate,bytes([255,0]),(2,1),self.spec())
        self.assertEqual(out,bytes([0,0,255,0,255,0])*2)
        self.assertEqual(r['fully_replaced_pixels_per_frame'],1)
        self.assertFalse(r['inpainting'])
        out,_=m.remove(original,plate,bytes([128,0]),(2,1),self.spec())
        self.assertEqual(out[:3],bytes([127,0,128]))
    def test_invalid_mask_and_bounds(self):
        raw=b'abc'*4;plate=b'xyz'*2
        for mask in (b'\0\0',b'\xff\xff',b'\xff'):
            with self.assertRaises(ValueError):m.remove(raw,plate,mask,(2,1),self.spec())
        with self.assertRaises(ValueError):m.checked(dict(self.spec(),end_frame=61))
    def test_review_execute_stale_mask(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'clip.mp4').write_bytes(b'fixture')
            (root/'plate.png').write_bytes(encode(2,1,'RGB',bytes([0,0,255])*2))
            (root/'mask.png').write_bytes(encode(2,1,'L',bytes([255,0])))
            (root/'spec.json').write_text(json.dumps(self.spec()),encoding='utf8')
            for name in ('ff','fp'):(root/name).write_bytes(name.encode())
            tools=tuple(snapshot_file(root/name) for name in ('ff','fp'))
            meta={'width':2,'height':1,'fps':24,'frames':2}
            with patch.object(m,'installed',return_value=tools),patch.object(m,'probe',return_value=meta),patch.object(m,'decode',return_value=bytes([255,0,0,0,255,0])*2),patch.object(m,'encode_verified',return_value=b'output') as enc:
                plan,_=m.review(root,'spec.json','out.mp4');r=m.execute(root,plan)
                self.assertEqual(r['status'],'masked_video_pixels_verified')
                self.assertEqual(bytes(enc.call_args.args[0]),bytes([0,0,255,0,255,0])*2)
                plan,_=m.review(root,'spec.json','other.mp4')
                (root/'mask.png').write_bytes(b'changed')
                with self.assertRaises(ValueError):m.execute(root,plan)
                self.assertFalse((root/'other.mp4').exists())
if __name__=='__main__':unittest.main()
