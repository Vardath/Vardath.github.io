import io,json,tempfile,unittest,wave
from pathlib import Path
from unittest.mock import patch
from deepthort_local import lip_sync as m
from deepthort_local.texture_pixels import encode
from deepthort_local.action_guards import snapshot_file

class LipSyncTests(unittest.TestCase):
    def spec(self):
        return {'face':'face.png','audio':'speech.wav','mouth':[1,0,1,1],'sprites':['closed.png','open.png'],
                'cues':[{'frame':0,'sprite':0},{'frame':1,'sprite':1},{'frame':2,'sprite':0}],'fps':24,'frames':3}
    def raws(self):
        b=io.BytesIO()
        with wave.open(b,'wb') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes(b'\x01\x00'*6000)
        return [encode(2,1,'RGB',bytes([50,60,70])*2),b.getvalue(),encode(1,1,'RGB',bytes([0,0,0])),encode(1,1,'RGB',bytes([255,0,0]))]
    def test_cues_and_pcm(self):
        s=self.spec();size,pcm,shapes=m.prepare(self.raws(),s)
        self.assertEqual(size,(2,1));self.assertEqual(len(pcm),12000)
        self.assertEqual(m.sequence(shapes,s),bytes([50,60,70,0,0,0,50,60,70,255,0,0,50,60,70,0,0,0]))
    def test_refusals(self):
        s=self.spec();r=self.raws()
        with self.assertRaises(ValueError):m.prepare(r,dict(s,frames=4))
        with self.assertRaises(ValueError):m.prepare(r[:3]+[r[2]],s)
        with self.assertRaises(ValueError):m.checked(dict(s,cues=[{'frame':1,'sprite':0},{'frame':2,'sprite':1}]))
    def test_review_execute_stale(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();s=self.spec()
            for name,raw in zip([s['face'],s['audio'],*s['sprites']],self.raws()):(root/name).write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(s),encoding='utf8')
            for name in ('ff','fp'):(root/name).write_bytes(name.encode())
            tools=tuple(snapshot_file(root/name) for name in ('ff','fp'))
            with patch.object(m,'installed',return_value=tools),patch.object(m,'mux',return_value=b'output') as render:
                plan,_=m.review(root,'spec.json','out.mp4');r=m.execute(root,plan)
                self.assertEqual(r['status'],'cue_timed_lip_sync_mux_verified')
                self.assertEqual(render.call_args.args[1],(2,1))
                self.assertFalse(r['phoneme_alignment_verified'])
                plan,_=m.review(root,'spec.json','other.mp4')
                (root/'open.png').write_bytes(b'changed')
                with self.assertRaises(ValueError):m.execute(root,plan)
                self.assertFalse((root/'other.mp4').exists())
if __name__=='__main__':unittest.main()
