from array import array
import json,math,tempfile,unittest
from pathlib import Path
from deepthort_local import audio_to_music as m
from deepthort_local.noise_reduction import encode

class AudioMusicTests(unittest.TestCase):
    def spec(self):return {'audio':'beat.wav','root_midi':45,'seed':18,'peak_dbfs':-3,'pattern':'electronic'}
    def source(self,positions=(2000,6000,10000,14000,18000,22000)):
        samples=array('h',[0])*24000
        for index,at in enumerate(positions):
            for i in range(400):
                samples[at+i]=round((5000 if index%2 else 10000)*math.sin(2*math.pi*400*i/8000))
        return encode(samples,8000,1)
    def test_actual_rhythm_and_seeded_music(self):
        raw=self.source();out,r=m.generate(raw,self.spec())
        self.assertEqual([x['frame'] for x in r['events']],[6000,18000,30000,42000,54000,66000])
        self.assertGreater(r['events'][0]['accent'],r['events'][1]['accent'])
        self.assertEqual(r['frames'],72000);self.assertTrue(r['pcm_verified'])
        self.assertFalse(r['source_audio_copied'])
        self.assertEqual(m.generate(raw,self.spec())[0],out)
        self.assertNotEqual(m.generate(raw,dict(self.spec(),seed=19))[0],out)
    def test_reject_no_rhythm_and_bad_settings(self):
        with self.assertRaises(ValueError):m.generate(self.source(()),self.spec())
        with self.assertRaises(ValueError):m.checked(dict(self.spec(),root_midi=100))
    def test_review_and_source_guard(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'beat.wav').write_bytes(self.source())
            (root/'spec.json').write_text(json.dumps(self.spec()),encoding='utf8')
            plan,_=m.review(root,'spec.json','song.wav')
            self.assertEqual(m.execute(root,plan)['status'],'rhythm_conditioned_music_pcm_verified')
            plan,_=m.review(root,'spec.json','other.wav')
            (root/'beat.wav').write_bytes(self.source((1000,5000,9000)))
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'other.wav').exists())
if __name__=='__main__':unittest.main()
