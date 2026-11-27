import io,json,tempfile,unittest,wave
from pathlib import Path
from unittest.mock import patch
from deepthort_local import video_dubbing as m
from deepthort_local.action_guards import snapshot_file

class DubbingTests(unittest.TestCase):
    def spec(self):return {'video':'clip.mp4','audio':'dub.wav','start_frame':2,'end_frame':5}
    def wav(self,n=6000):
        b=io.BytesIO()
        with wave.open(b,'wb') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes(b'\x01\x00'*n)
        return b.getvalue()
    def setup_inputs(self,root):
        (root/'clip.mp4').write_bytes(b'fixture');(root/'dub.wav').write_bytes(self.wav())
        (root/'spec.json').write_text(json.dumps(self.spec()),encoding='utf8')
        for n in ('ff','fp'):(root/n).write_bytes(n.encode())
        return tuple(snapshot_file(root/n) for n in ('ff','fp'))
    def test_review_and_exact_streams(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();tools=self.setup_inputs(root);meta={'width':2,'height':2,'fps':24,'frames':6}
            rgb=bytes(range(36))
            with patch.object(m,'installed',return_value=tools),patch.object(m,'probe',return_value=meta),patch.object(m,'decode',return_value=rgb) as dec,patch.object(m,'mux',return_value=b'output') as render:
                plan,review=m.review(root,'spec.json','out.mp4')
                self.assertEqual(review['observations']['speech_samples'],6000)
                self.assertFalse(dec.called)
                r=m.execute(root,plan);self.assertEqual(r['status'],'reviewed_dub_mux_verified')
                self.assertEqual(dec.call_args.args[2:],(2,5,2,2))
                self.assertEqual(render.call_args.args[:4],(rgb,(2,2),b'\x01\x00'*6000,{'fps':24,'frames':3}))
                self.assertFalse(r['automatic_alignment'])
                with self.assertRaises(ValueError):m.execute(root,plan)
    def test_duration_and_interval(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();tools=self.setup_inputs(root)
            with patch.object(m,'installed',return_value=tools),patch.object(m,'probe',return_value={'width':2,'height':2,'fps':24,'frames':4}):
                with self.assertRaises(ValueError):m.review(root,'spec.json','out.mp4')
            (root/'dub.wav').write_bytes(self.wav(5999))
            with patch.object(m,'installed',return_value=tools),patch.object(m,'probe',return_value={'width':2,'height':2,'fps':24,'frames':6}):
                with self.assertRaises(ValueError):m.review(root,'spec.json','out.mp4')
    def test_stale_audio(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();tools=self.setup_inputs(root)
            with patch.object(m,'installed',return_value=tools),patch.object(m,'probe',return_value={'width':2,'height':2,'fps':24,'frames':6}):
                plan,_=m.review(root,'spec.json','out.mp4');(root/'dub.wav').write_bytes(self.wav(6001))
                with self.assertRaises(ValueError):m.execute(root,plan)
                self.assertFalse((root/'out.mp4').exists())
if __name__=='__main__':unittest.main()
