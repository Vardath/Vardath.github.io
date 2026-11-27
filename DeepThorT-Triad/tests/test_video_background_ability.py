import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import video_background as m
from deepthort_local.texture_pixels import encode
from deepthort_local.action_guards import snapshot_file

class VideoBackgroundTests(unittest.TestCase):
    def spec(self):
        return {'video':'clip.mp4','background':'bg.png','start_frame':0,'end_frame':2,'key':[0,255,0],'tolerance':0,'feather':0}
    def test_exact_replacement_and_foreground(self):
        green=bytes([0,255,0]);red=bytes([255,0,0]);blue=bytes([0,0,255])
        result,r=m.composite((green+red)*2,blue*2,(2,1),self.spec())
        self.assertEqual(result,(blue+red)*2);self.assertEqual(r['fully_replaced_pixels'],2)
        self.assertFalse(r['semantic_segmentation'])
    def test_feather_and_refusal(self):
        s=dict(self.spec(),end_frame=1,feather=100)
        result,r=m.composite(bytes([50,255,0]),bytes([0,0,200]),(1,1),s)
        self.assertEqual(result,bytes([25,128,100]));self.assertEqual(r['partial_pixels'],1)
        with self.assertRaises(ValueError):m.composite(bytes([255,0,0]),bytes([0,0,200]),(1,1),s)
        with self.assertRaises(ValueError):m.checked(dict(s,tolerance=255))
    def test_review_and_stale_source(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();s=self.spec()
            (root/'clip.mp4').write_bytes(b'fixture')
            (root/'bg.png').write_bytes(encode(2,1,'RGB',bytes([0,0,255])*2))
            (root/'spec.json').write_text(json.dumps(s),encoding='utf8')
            for n in ('ff','fp'):(root/n).write_bytes(n.encode())
            tools=tuple(snapshot_file(root/n) for n in ('ff','fp'))
            info={'width':2,'height':1,'fps':24,'frames':2}
            pixels=bytes([0,255,0,255,0,0])*2
            with patch.object(m,'installed',return_value=tools),patch.object(m,'probe',return_value=info),patch.object(m,'decode',return_value=pixels),patch.object(m,'encode_verified',return_value=b'output') as enc:
                plan,_=m.review(root,'spec.json','out.mp4')
                r=m.execute(root,plan)
                self.assertEqual(r['fully_replaced_pixels'],2)
                self.assertEqual(bytes(enc.call_args.args[0]),bytes([0,0,255,255,0,0])*2)
                plan,_=m.review(root,'spec.json','other.mp4')
                (root/'bg.png').write_bytes(b'changed')
                with self.assertRaises(ValueError):m.execute(root,plan)
                self.assertFalse((root/'other.mp4').exists())

if __name__=='__main__':unittest.main()
