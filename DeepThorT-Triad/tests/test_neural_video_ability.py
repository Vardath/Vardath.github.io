import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import neural_video as m
from deepthort_local.action_guards import snapshot_file

class NeuralVideoTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve()
        self.spec={'prompt':'a drifting cloud','negative_prompt':'','seed':12,'size':256,'frames':8,'steps':10}
        (self.root/'spec.json').write_text(json.dumps(self.spec),encoding='utf8')
        for n in ('ff','fp'):(self.root/n).write_bytes(n.encode())
        self.tools=tuple(snapshot_file(self.root/n) for n in ('ff','fp'))
        self.inventory=[{'path':'base','inventory_sha':'a'*64,'bytes':123},{'path':'motion','inventory_sha':'b'*64,'bytes':123}]
        self.addCleanup(patch.stopall)
        self.mock_models=patch.object(m,'models',return_value=self.inventory).start()
        patch.object(m,'installed',return_value=self.tools).start()
    def plan(self):
        return m.review(self.root,'spec.json','out.mp4')[0]
    def test_reviewed_backend_and_codec_handoff(self):
        plan=self.plan()
        raw=b''.join(bytes([i,20,40])*(256**2) for i in range(8))
        with patch.object(m,'encode_verified',return_value=b'fixture-video') as codec:
            r=m.execute(self.root,plan,backend=lambda s:raw)
        self.assertEqual(codec.call_args.args[:4],(raw,(256,256),24,8))
        self.assertEqual(r['backend'],'injected_fixture')
        self.assertFalse(r['motion_quality_verified'])
        self.assertEqual((self.root/'out.mp4').read_bytes(),b'fixture-video')
    def test_static_or_wrong_length_rejected(self):
        plan=self.plan()
        for data in (b'x',bytes(256**2*3*8)):
            with self.assertRaises(ValueError):m.execute(self.root,plan,backend=lambda _:data)
        self.assertFalse((self.root/'out.mp4').exists())
        with self.assertRaises(ValueError):m.checked(dict(self.spec,frames=100))
    def test_changed_model_inventory_blocks_before_backend(self):
        plan=self.plan()
        self.mock_models.return_value=[]
        with self.assertRaises(ValueError):m.execute(self.root,plan,backend=lambda _:self.fail('stale approval'))
        self.assertFalse((self.root/'out.mp4').exists())
if __name__=='__main__':unittest.main()
