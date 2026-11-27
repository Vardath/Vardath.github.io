from array import array
import io,json,math,tempfile,unittest,wave
from pathlib import Path
from deepthort_local import instrumental_synthesis as m
from deepthort_local.musical_arrangement import midi
from deepthort_local.audio_to_midi import midi as timed_midi
from deepthort_local.creative_core import midi as legacy_midi
SCORE={'bpm':120,'parts':[{'name':'Lead','program':0,'notes':[[480,480,69,127]]}]}
SPEC={'midi':'score.mid','voices':[{'timbre':'sine','gain_db':0,'pan':-1}],'peak_dbfs':-6}
def decoded(raw):
    with wave.open(io.BytesIO(raw),'rb') as f:
        s=array('h');s.frombytes(f.readframes(f.getnframes()));return s,f.getnframes()
class SynthesisTests(unittest.TestCase):
    def test_timing_pitch_pan_and_peak(self):
        raw=midi(SCORE);out,r=m.render(raw,SPEC);s,frames=decoded(out)
        self.assertEqual(frames,m.RATE)
        self.assertTrue(all(v==0 for v in s[:m.RATE]))
        self.assertLessEqual(max(abs(v) for v in s[1::2]),1)
        self.assertLessEqual(r['peak_pcm'],math.ceil(32767*10**(-6/20)))
        left=s[0::2];begin=round(.65*m.RATE);end=round(.9*m.RATE)
        crossings=sum(left[i]<=0<left[i+1] for i in range(begin,end-1))
        self.assertAlmostEqual(crossings/.25,440,delta=8)
        self.assertEqual(m.render(raw,SPEC)[0],out)
    def test_supported_profiles_and_bounds(self):
        for raw in (timed_midi(120,[[0,480,60]]),legacy_midi({'bpm':120,'notes':[[60,480]]*4})):
            self.assertEqual(len(m.score(raw)['parts']),1)
        with self.assertRaises(ValueError):m.schedule(midi(SCORE),dict(SPEC,voices=SPEC['voices']*2))
        with self.assertRaises(ValueError):m.checked(dict(SPEC,peak_dbfs=float('nan')))
        with self.assertRaises(ValueError):m.score(b'bad')
    def test_review_and_stale(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'score.mid';raw=midi(SCORE);src.write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(SPEC));plan,_=m.review(root,'spec.json','render.wav')
            result=m.execute(root,plan);self.assertTrue(result['source_unchanged']);self.assertEqual(src.read_bytes(),raw)
            with self.assertRaises(ValueError):m.execute(root,plan)
            (root/'render.wav').unlink();src.write_bytes(timed_midi(120,[[0,480,60]]))
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'render.wav').exists())
