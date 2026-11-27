import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import video_style as m
from deepthort_local.texture_pixels import encode
from deepthort_local.action_guards import snapshot_file

class VideoStyleTests(unittest.TestCase):
    def spec(self):
        return {'video':'clip.mp4','reference':'ref.png','start_frame':0,'end_frame':2,'strength_percent':100}
    def test_shared_mapping(self):
        raw=bytes([20,40,60,80,100,120,80,100,120,140,160,180])
        ref=bytes([200,210,220])*2
        out,r=m.transfer(raw,ref,(2,1),self.spec())
        self.assertEqual(out,ref*2)
        self.assertTrue(r['shared_temporal_lut'])
        self.assertFalse(r['neural_style_transfer'])
        half,_=m.transfer(raw,ref,(2,1),dict(self.spec(),strength_percent=50))
        self.assertEqual(half[:3],bytes([110,125,140]))
    def test_refusals(self):
        with self.assertRaises(ValueError):m.checked(dict(self.spec(),strength_percent=0))
        with self.assertRaises(ValueError):m.transfer(b'bad',b'abc',(2,1),self.spec())
        with self.assertRaises(ValueError):m.transfer(b'abc'*4,b'abc',(2,1),self.spec())
    def test_review_execute_stale_reference(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'clip.mp4').write_bytes(b'fixture')
            (root/'ref.png').write_bytes(encode(2,1,'RGB',bytes([200,210,220])*2))
            (root/'spec.json').write_text(json.dumps(self.spec()),encoding='utf8')
            for name in ('ff','fp'):(root/name).write_bytes(name.encode())
            tools=tuple(snapshot_file(root/name) for name in ('ff','fp'))
            info={'width':2,'height':1,'fps':24,'frames':2}
            with patch.object(m,'installed',return_value=tools),patch.object(m,'probe',return_value=info),patch.object(m,'decode',return_value=bytes([20,40,60])*4),patch.object(m,'encode_verified',return_value=b'output') as enc:
                plan,_=m.review(root,'spec.json','out.mp4')
                result=m.execute(root,plan)
                self.assertEqual(result['status'],'video_palette_pixels_verified')
                self.assertEqual(bytes(enc.call_args.args[0]),bytes([200,210,220])*4)
                plan,_=m.review(root,'spec.json','other.mp4')
                (root/'ref.png').write_bytes(b'changed')
                with self.assertRaises(ValueError):m.execute(root,plan)
                self.assertFalse((root/'other.mp4').exists())

if __name__=='__main__':unittest.main()
