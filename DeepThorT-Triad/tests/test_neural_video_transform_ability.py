import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import neural_video_transform as m
from deepthort_local.action_guards import snapshot_file

class VideoTransformTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve()
        self.spec={'video':'clip.mp4','start_frame':2,'prompt':'painted landscape','negative_prompt':'',
            'seed':12,'size':256,'frames':8,'steps':10,'strength_percent':50}
        (self.root/'spec.json').write_text(json.dumps(self.spec),encoding='utf8')
        for n in ('clip.mp4','ff','fp'):(self.root/n).write_bytes(n.encode())
        self.tools=tuple(snapshot_file(self.root/n) for n in ('ff','fp'))
        self.raw=b''.join(bytes([i,10,20])*(256**2) for i in range(8))
        self.out=b''.join(bytes([i,20,30])*(256**2) for i in range(8))
        self.info={'width':256,'height':256,'frames':12,'fps':25}
        self.addCleanup(patch.stopall)
        patch.object(m.neural,'models',return_value=[{'path':'fixture'}]).start()
        patch.object(m,'installed',return_value=self.tools).start()
        patch.object(m.video,'probe',return_value=self.info).start()
        self.decode=patch.object(m.video,'decode',return_value=self.raw).start()
    def plan(self):return m.review(self.root,'spec.json','out.mp4')[0]
    def test_exact_interval_backend_and_rate(self):
        plan=self.plan()
        def transform(s,raw):
            self.assertEqual(s,self.spec);self.assertEqual(raw,self.raw);return self.out
        with patch.object(m.video,'encode_verified',return_value=b'film') as enc:
            r=m.execute(self.root,plan,backend=transform)
        self.assertEqual(self.decode.call_args.args[2:],(2,10,256,256))
        self.assertEqual(enc.call_args.args[:4],(self.out,(256,256),25,8))
        self.assertEqual(r['backend'],'injected_fixture')
        self.assertFalse(r['identity_preservation_verified'])
    def test_refuses_static_unchanged_or_short_output(self):
        plan=self.plan()
        for out in (self.raw,b'x',bytes(len(self.raw))):
            with self.assertRaises(ValueError):m.execute(self.root,plan,backend=lambda s,raw:out)
        self.assertFalse((self.root/'out.mp4').exists())
    def test_stale_input_and_invalid_strength(self):
        plan=self.plan();(self.root/'clip.mp4').write_bytes(b'changed')
        with self.assertRaises(ValueError):m.execute(self.root,plan,backend=lambda *_:self.fail('stale input'))
        with self.assertRaises(ValueError):m.checked(dict(self.spec,strength_percent=100))
        self.assertFalse((self.root/'out.mp4').exists())
if __name__=='__main__':unittest.main()
