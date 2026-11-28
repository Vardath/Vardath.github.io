import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import camera_motion as m
from deepthort_local.action_guards import snapshot_file

class CameraMotionTests(unittest.TestCase):
    def spec(self):
        return {'video':'clip.mp4','start_frame':2,'end_frame':7,'width':16,'height':16,'keyframes':[
            {'frame':0,'crop':[0,0,16,16]},{'frame':2,'crop':[16,0,16,16]},{'frame':4,'crop':[0,16,16,16]}]}
    def pixels(self):
        return bytes(v for y in range(32) for x in range(32) for v in (x*8,y*8,64))
    def test_keyframes_and_pixels(self):
        s=self.spec()
        self.assertEqual(m.crop_at(s,0),(0,0,16,16))
        self.assertEqual(m.crop_at(s,1),(8,0,24,16))
        self.assertEqual(m.crop_at(s,2),(16,0,32,16))
        self.assertEqual(m.crop_at(s,4),(0,16,16,32))
        raw=m.reframe(self.pixels()*5,(32,32),s)
        self.assertEqual(len(raw),5*16*16*3)
        self.assertEqual(raw[:3],bytes([0,0,64]))
        self.assertEqual(raw[2*768:2*768+3],bytes([128,0,64]))
        self.assertEqual(raw[-768:-765],bytes([0,128,64]))
    def test_invalid_geometry(self):
        s=self.spec()
        with self.assertRaises(ValueError):m.geometry(s,(24,24))
        with self.assertRaises(ValueError):m.checked(dict(s,keyframes=s['keyframes'][:-1]))
        with self.assertRaises(ValueError):m.reframe(b'bad',(32,32),s)
    def test_review_execute_stale(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'clip.mp4').write_bytes(b'fixture')
            (root/'spec.json').write_text(json.dumps(self.spec()),encoding='utf8')
            for name in ('ff','fp'):(root/name).write_bytes(name.encode())
            tools=tuple(snapshot_file(root/name) for name in ('ff','fp'))
            meta={'width':32,'height':32,'fps':24,'frames':10}
            with patch.object(m,'installed',return_value=tools),patch.object(m,'probe',return_value=meta),patch.object(m,'decode',return_value=self.pixels()*5),patch.object(m,'encode_verified',return_value=b'output') as enc:
                plan,_=m.review(root,'spec.json','out.mp4');r=m.execute(root,plan)
                self.assertEqual(r['status'],'camera_motion_pixels_verified')
                self.assertEqual(enc.call_args.args[1:4],((16,16),24,5))
                plan,_=m.review(root,'spec.json','other.mp4')
                (root/'clip.mp4').write_bytes(b'changed')
                with self.assertRaises(ValueError):m.execute(root,plan)
                self.assertFalse((root/'other.mp4').exists())

if __name__=='__main__':unittest.main()
