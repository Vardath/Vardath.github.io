from array import array
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import song_continuation as m
from deepthort_local.noise_reduction import encode

SPEC={'reference':'song.wav','min_bpm':60,'max_bpm':180,'channel':'left','bars':2,'seed':17,
      'lead_timbre':'sine','backing_timbre':'organ','peak_dbfs':-3,'tail_seconds':3,'fade_ms':40}
PROFILE={'bpm':120,'tonic':'C','mode':'major','tempo_support':1.,'key_margin':.12}

class SongContinuationTests(unittest.TestCase):
    def test_boundary_and_exact_original(self):
        original=array('h',[1000,-2000])*10
        continuation=array('h',[300,-400])*2000
        raw,r=m.append(original,continuation,10,SPEC)
        samples=m.read_pcm(raw,m.RATE,2,2010)
        self.assertEqual(samples[:20],original)
        self.assertEqual(samples[20:22],original[-2:])
        self.assertEqual(samples[-2:],continuation[-2:])
        self.assertTrue(r['original_pcm_preserved'])
    def test_render_and_guard(self):
        original=array('h',[0,0])*(3*m.RATE)
        with tempfile.TemporaryDirectory() as td,patch.object(m.reference,'analyse',return_value=PROFILE):
            root=Path(td).resolve();(root/'song.wav').write_bytes(encode(original,m.RATE,2))
            (root/'spec.json').write_text(json.dumps(SPEC),encoding='utf8')
            plan,_=m.review(root,'spec.json','out.wav');r=m.execute(root,plan)
            out=m.read_pcm((root/'out.wav').read_bytes(),m.RATE,2,r['frames'])
            self.assertEqual(out[:len(original)],original)
            self.assertGreater(r['appended_frames'],0);self.assertTrue(any(out[len(original):]))
            plan,_=m.review(root,'spec.json','other.wav');(root/'song.wav').write_bytes(b'changed')
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'other.wav').exists())
    def test_refuse_ambiguous_or_wrong_format(self):
        raw=encode(array('h',[0,0])*(3*m.RATE),m.RATE,2)
        with self.assertRaises(ValueError):m.generate(raw,SPEC)
        with self.assertRaises(ValueError):m.source(encode(array('h',[0])*24000,8000,1),SPEC)
if __name__=='__main__':unittest.main()
