from array import array
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import reference_music as m
from deepthort_local.noise_reduction import encode

SPEC={'reference':'ref.wav','min_bpm':60,'max_bpm':180,'channel':'left','bars':2,'seed':17,
      'lead_timbre':'sine','backing_timbre':'organ','peak_dbfs':-3}
PROFILE={'bpm':120,'tonic':'C','mode':'major','tempo_support':1.,'key_margin':.12}

class ReferenceMusicTests(unittest.TestCase):
    def test_new_score_deterministic_and_conditioned(self):
        midi,settings,progression=m.compose(PROFILE,SPEC)
        score=m.arrangement.inspect(midi)
        self.assertEqual(score['bpm'],120);self.assertEqual(progression,[1,1])
        self.assertEqual(m.compose(PROFILE,SPEC)[0],midi)
        self.assertNotEqual(m.compose(dict(PROFILE,tonic='D'),SPEC)[0],midi)
        self.assertEqual(len(score['parts']),3)
        self.assertNotEqual(m.compose(PROFILE,dict(SPEC,seed=18))[0],midi)
    def test_ambiguous_reference_refused(self):
        raw=encode(array('h',[0])*24000,8000,1)
        with self.assertRaises(ValueError):m.analyse(raw,SPEC)
    def test_review_render_and_stale_source(self):
        raw=encode(array('h',[0])*24000,8000,1)
        with tempfile.TemporaryDirectory() as td,patch.object(m,'analyse',return_value=PROFILE):
            root=Path(td).resolve();(root/'ref.wav').write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(SPEC),encoding='utf8')
            plan,_=m.review(root,'spec.json','out.wav')
            receipt=m.execute(root,plan)
            self.assertEqual(receipt['status'],'reference_conditioned_music_pcm_verified')
            self.assertFalse(receipt['source_samples_copied'])
            self.assertFalse(receipt['style_similarity_verified'])
            plan,_=m.review(root,'spec.json','other.wav')
            (root/'ref.wav').write_bytes(b'changed')
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'other.wav').exists())
if __name__=='__main__':unittest.main()
