import json,math,tempfile,unittest
from pathlib import Path
from deepthort_local import vocal_harmony_generation as m

SPEC={'score':{'notes':[{'midi':69,'vowel':'ah','duration_ms':400},{'midi':None,'vowel':None,'duration_ms':200}],
               'vibrato_hz':5,'vibrato_cents':0,'peak_dbfs':-6},
      'parts':[{'semitones':0,'gain_db':0,'pan_percent':-100},{'semitones':7,'gain_db':0,'pan_percent':100}],
      'peak_dbfs':-9}
def energy(a,f):
    return abs(sum(x*complex(math.cos(2*math.pi*f*i/m.RATE),math.sin(2*math.pi*f*i/m.RATE)) for i,x in enumerate(a)))

class HarmonyTests(unittest.TestCase):
    def test_exact_intervals_pan_and_rest(self):
        raw,r=m.generate(SPEC);a,n=m.decode(raw,2)
        self.assertEqual(n,14400)
        self.assertFalse(any(a[19200:]))
        self.assertEqual(r['parts'][1]['notes'][0]['midi'],76)
        left,right=a[::2][2400:7200],a[1::2][2400:7200]
        self.assertGreater(energy(left,440),10*energy(left,440*2**(7/12)))
        self.assertGreater(energy(right,440*2**(7/12)),10*energy(right,440))
        self.assertLessEqual(r['peak_pcm'],11626)
        self.assertFalse(r['key_aware_harmonization'])
    def test_invalid_parts(self):
        for parts in ([SPEC['parts'][0]], [SPEC['parts'][1],dict(SPEC['parts'][1],semitones=5)],
                      [SPEC['parts'][0],dict(SPEC['parts'][0],pan_percent=50)]):
            with self.assertRaises(ValueError):m.checked(dict(SPEC,parts=parts))
        high=dict(SPEC['score'],notes=[{'midi':84,'vowel':'ah','duration_ms':400}])
        with self.assertRaises(ValueError):m.checked(dict(SPEC,score=high))
    def test_review_and_source_guards(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'spec.json';p.write_text(json.dumps(SPEC),encoding='utf8')
            plan,_=m.review(root,'spec.json','harmony.wav')
            self.assertTrue(m.execute(root,plan)['pcm_verified'])
            with self.assertRaises(ValueError):m.execute(root,plan)
            plan,_=m.review(root,'spec.json','other.wav');p.write_text(json.dumps(dict(SPEC,peak_dbfs=-10)),encoding='utf8')
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'other.wav').exists())
if __name__=='__main__':unittest.main()
