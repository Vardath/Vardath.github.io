from array import array
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import cinematic_assembly as m
from deepthort_local.action_guards import snapshot_file
from deepthort_local.noise_reduction import encode

class CinematicAssemblyTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve()
        self.spec={'title':'A film','sequence':{'fps':24,'clips':[{'video':'a.mp4','start_frame':0,'end_frame':3},
            {'video':'b.mp4','start_frame':0,'end_frame':3}],'transitions':[{'kind':'crossfade','frames':1}]},
            'soundtrack':'score.wav','audio_start_ms':10}
        self.audio=encode(array('h',[2000,-1000])*12000,48000,2)
        for n,raw in (('a.mp4',b'a'),('b.mp4',b'b'),('score.wav',self.audio),('ff',b'ff'),('fp',b'fp')):
            (self.root/n).write_bytes(raw)
        (self.root/'spec.json').write_text(json.dumps(self.spec),encoding='utf8')
        self.tools=tuple(snapshot_file(self.root/n) for n in ('ff','fp'))
        self.addCleanup(patch.stopall);patch.object(m,'installed',return_value=self.tools).start()
        def observe(raws,s,tools,folder,*,render):
            self.assertEqual(raws,[b'a',b'b'])
            return (b'picture' if render else None),{'width':2,'height':2,'fps':24,
                ('frames' if render else 'output_frames'):5}
        patch.object(m.video,'observe',side_effect=observe).start()
    def test_exact_soundtrack_selection(self):
        wav,raw,ch,n=m.soundtrack(self.audio,self.spec,5)
        self.assertEqual((ch,n,len(raw)),(2,10000,40000))
        with self.assertRaises(ValueError):m.soundtrack(self.audio,self.spec,10)
    def test_reviewed_production_handoff(self):
        plan,_=m.review(self.root,'spec.json','out.mp4')
        with patch.object(m,'mux',return_value=b'film') as mux:
            r=m.execute(self.root,plan)
        self.assertEqual(mux.call_args.args[-2:],(2,10000))
        self.assertEqual(r['status'],'cinematic_picture_audio_verified')
        self.assertFalse(r['cinematic_quality_verified'])
        self.assertEqual((self.root/'out.mp4').read_bytes(),b'film')
    def test_stale_audio_and_invalid_sequence(self):
        plan,_=m.review(self.root,'spec.json','out.mp4')
        (self.root/'score.wav').write_bytes(b'changed')
        with self.assertRaises(ValueError):m.execute(self.root,plan)
        with self.assertRaises(ValueError):m.checked(dict(self.spec,audio_start_ms=-1))
        self.assertFalse((self.root/'out.mp4').exists())
if __name__=='__main__':unittest.main()
