import io,json,math,tempfile,unittest,wave
from array import array
from pathlib import Path
from deepthort_local import singing_voice_generation as m

SPEC={'notes':[{'midi':69,'vowel':'ah','duration_ms':400},{'midi':None,'vowel':None,'duration_ms':200},
               {'midi':72,'vowel':'oo','duration_ms':400}],'vibrato_hz':5,'vibrato_cents':0,'peak_dbfs':-6}
def samples(raw):
    with wave.open(io.BytesIO(raw),'rb') as f:
        a=array('h');a.frombytes(f.readframes(f.getnframes()))
        return a,f.getframerate()
def energy(a,frequency,rate):
    return abs(sum(x*complex(math.cos(2*math.pi*frequency*i/rate),math.sin(2*math.pi*frequency*i/rate)) for i,x in enumerate(a)))

class SingingTests(unittest.TestCase):
    def test_score_rest_pitch_and_bounds(self):
        raw,r=m.generate(SPEC);a,rate=samples(raw)
        self.assertEqual((rate,len(a)),(24000,24000))
        self.assertFalse(any(a[9600:14400]))
        self.assertEqual([n['start_frame'] for n in r['notes']],[0,9600,14400])
        center=a[2400:7200]
        self.assertGreater(energy(center,440,rate),10*energy(center,500,rate))
        self.assertLessEqual(r['peak_pcm'],16423)
        self.assertFalse(r['lyric_synthesis'])
    def test_vowel_vibrato_and_invalid_controls(self):
        self.assertNotEqual(m.weights(220,'ah',0),m.weights(220,'ee',0))
        raw,_=m.generate(SPEC)
        self.assertNotEqual(raw,m.generate(dict(SPEC,vibrato_cents=50))[0])
        for bad in (dict(SPEC,vibrato_hz=12),dict(SPEC,notes=[{'midi':None,'vowel':None,'duration_ms':500}]),
                    dict(SPEC,notes=[{'midi':90,'vowel':'ah','duration_ms':500}])):
            with self.assertRaises(ValueError):m.checked(bad)
    def test_review_and_source_guards(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'spec.json';p.write_text(json.dumps(SPEC),encoding='utf8')
            plan,_=m.review(root,'spec.json','song.wav')
            self.assertTrue(m.execute(root,plan)['pcm_verified'])
            with self.assertRaises(ValueError):m.execute(root,plan)
            plan,_=m.review(root,'spec.json','other.wav');p.write_text(json.dumps(dict(SPEC,vibrato_cents=5)),encoding='utf8')
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'other.wav').exists())
if __name__=='__main__':unittest.main()
