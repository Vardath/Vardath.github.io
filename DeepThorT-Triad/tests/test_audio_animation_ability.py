import io,json,struct,tempfile,unittest,wave
from pathlib import Path
from unittest.mock import patch
from deepthort_local import audio_animation as m
from deepthort_local.texture_pixels import encode
from deepthort_local.action_guards import snapshot_file

class AudioAnimationTests(unittest.TestCase):
    def spec(self):
        return {'background':'bg.png','layer':'layer.png','audio':'sound.wav','fps':24,'frames':3,'anchor':[0,2],'travel_px':2,'reference_rms':1000}
    def raws(self):
        b=io.BytesIO()
        with wave.open(b,'wb') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000)
            f.writeframes(b''.join(struct.pack('<h',v)*2000 for v in (0,500,1000)))
        return [encode(3,3,'RGB',bytes(27)),encode(1,1,'RGB',bytes([255,0,0])),b.getvalue()]
    def test_envelope_and_pixels(self):
        size,pcm,offsets,raw=m.prepare(self.raws(),self.spec(),True)
        self.assertEqual(size,(3,3));self.assertEqual(offsets,[0,1,2])
        self.assertEqual(len(raw),81)
        self.assertEqual([raw[i*27+(2-i)*9] for i in range(3)],[255]*3)
        self.assertEqual([sum(raw[i*27:(i+1)*27]) for i in range(3)],[255]*3)
    def test_bounds(self):
        with self.assertRaises(ValueError):m.prepare(self.raws(),dict(self.spec(),anchor=[0,1]))
        with self.assertRaises(ValueError):m.prepare(self.raws(),dict(self.spec(),frames=4))
        with self.assertRaises(ValueError):m.checked(dict(self.spec(),reference_rms=0))
    def test_exact_review_and_publish(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();s=self.spec()
            for n,raw in zip(('bg.png','layer.png','sound.wav'),self.raws()):(root/n).write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(s),encoding='utf8')
            for n in ('ff','fp'):(root/n).write_bytes(n.encode())
            tools=tuple(snapshot_file(root/n) for n in ('ff','fp'))
            with patch.object(m,'installed',return_value=tools),patch.object(m,'mux',return_value=b'output') as render:
                plan,_=m.review(root,'spec.json','out.mp4');r=m.execute(root,plan)
                self.assertEqual(r['motion_offsets'],[0,1,2]);self.assertEqual(render.call_args.args[1],(3,3))
                plan,_=m.review(root,'spec.json','other.mp4')
                (root/'sound.wav').write_bytes(b'changed')
                with self.assertRaises(ValueError):m.execute(root,plan)
                self.assertFalse((root/'other.mp4').exists())
if __name__=='__main__':unittest.main()
