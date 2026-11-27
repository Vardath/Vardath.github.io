import copy,json,tempfile,unittest
from pathlib import Path
from deepthort_local import musical_arrangement as m
from deepthort_local.artifact_media_checks import media_scope
SPEC={'bpm':120,'parts':[{'name':'Keys','program':0,'notes':[[0,480,60,90],[0,480,64,80],[0,480,67,80],[480,240,60,70]]},
    {'name':'Bass','program':33,'notes':[[240,720,36,100]]}]}
class ArrangementTests(unittest.TestCase):
    def test_polyphony_timing_and_parts(self):
        raw=m.midi(SPEC)
        self.assertEqual(m.inspect(raw),SPEC)
        self.assertEqual(raw[8:14],b'\x00\x01\x00\x03\x01\xe0')
        self.assertIn('2 parts',media_scope('.mid',raw))
    def test_invalid_and_truncated(self):
        for bad in ([[0,480,60,90],[200,480,60,80]],[[0,480,60,90],[0,480,60,80]],[[0,480,60,0]]):
            spec=copy.deepcopy(SPEC);spec['parts'][0]['notes']=bad
            with self.assertRaises(ValueError):m.midi(spec)
        with self.assertRaises(ValueError):m.inspect(m.midi(SPEC)[:-1])
        spec=copy.deepcopy(SPEC);spec['parts'][1]['name']='KEYS'
        with self.assertRaises(ValueError):m.midi(spec)
    def test_review_publish_and_stale(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'score.json';src.write_text(json.dumps(SPEC))
            plan,_=m.review(root,'score.json','arrangement.mid')
            result=m.execute(root,plan);self.assertEqual((result['parts'],result['notes']),(2,5))
            self.assertEqual(m.inspect((root/'arrangement.mid').read_bytes()),SPEC)
            with self.assertRaises(ValueError):m.execute(root,plan)
            (root/'arrangement.mid').unlink();src.write_text(json.dumps(dict(SPEC,bpm=100)))
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'arrangement.mid').exists())
