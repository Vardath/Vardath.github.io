from array import array
import json,tempfile,unittest
from pathlib import Path
from deepthort_local import song_section_edit as m
from deepthort_local.noise_reduction import encode

SPEC={'audio':'song.wav','start_frame':10,'end_frame':30,'fade_frames':4,
    'mode':'replace','gain_db':0,'replacement':'part.wav'}
class SectionEditTests(unittest.TestCase):
    def setUp(self):
        self.source=array('h',[1000,-1000])*40
        self.part=array('h',[4000,-3000])*20
        self.raw=encode(self.source,24000,2);self.replacement=encode(self.part,24000,2)
    def test_replace_exact_outside_and_inside_fades(self):
        raw,r=m.render(self.raw,SPEC,self.replacement)
        out=m.read_pcm(raw,24000,2,40)
        self.assertEqual(out[:20],self.source[:20]);self.assertEqual(out[60:],self.source[60:])
        self.assertEqual(out[20:22],self.source[20:22]);self.assertEqual(out[58:60],self.source[58:60])
        self.assertEqual(out[28:52],self.part[8:32])
        self.assertTrue(r['outside_interval_pcm_preserved'])
    def test_gain_and_reject_clip_or_wrong_length(self):
        gain={k:v for k,v in SPEC.items() if k!='replacement'};gain.update(mode='gain',gain_db=-6)
        out,r=m.render(self.raw,gain);self.assertTrue(r['duration_preserved'])
        self.assertEqual(m.read_pcm(out,24000,2,40)[28],501)
        with self.assertRaises(ValueError):m.render(self.raw,SPEC,encode(self.part[:-2],24000,2))
        with self.assertRaises(ValueError):m.render(self.raw,dict(SPEC,gain_db=12),encode(array('h',[30000,-30000])*20,24000,2))
    def test_review_execute_and_changed_replacement(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'song.wav').write_bytes(self.raw);(root/'part.wav').write_bytes(self.replacement)
            (root/'spec.json').write_text(json.dumps(SPEC),encoding='utf8')
            plan,_=m.review(root,'spec.json','out.wav')
            self.assertEqual(m.execute(root,plan)['status'],'song_section_edit_pcm_verified')
            plan,_=m.review(root,'spec.json','other.wav')
            (root/'part.wav').write_bytes(b'changed')
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'other.wav').exists())
if __name__=='__main__':unittest.main()
