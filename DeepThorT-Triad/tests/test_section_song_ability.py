import copy,json,tempfile,unittest
from pathlib import Path
from deepthort_local import section_song as m

class SectionSongTests(unittest.TestCase):
    def spec(self):
        def section(name,pitch,voiced):
            return {'name':name,'arrangement':{'bpm':120,'parts':[{'name':'Backing','program':0,'notes':[[0,480,pitch-12,85]]}]},
                'voices':[{'timbre':'sine','gain_db':-6,'pan':0}],'vocal_gain_db':-6,
                'vocal':{'notes':[{'midi':pitch,'vowel':'ah','duration_ms':500}],'vibrato_hz':5,'vibrato_cents':15,'peak_dbfs':-9} if voiced else None}
        return {'title':'Test song','sections':[section('intro',60,False),section('chorus',64,True)],
            'order':['intro','chorus','chorus'],'peak_dbfs':-3}
    def test_real_synthesis_and_exact_repeated_section(self):
        s=self.spec();payload,r=m.generate(s)
        self.assertEqual((r['frames'],r['channels']),(36000,2))
        decoded=m.read_pcm(payload,24000,2,36000)
        self.assertEqual(decoded[24000:48000],decoded[48000:])
        self.assertTrue(any(decoded));self.assertTrue(r['pcm_verified'])
        self.assertFalse(r['lyric_synthesis'])
        self.assertEqual([x['start_frame'] for x in r['timeline']],[0,12000,24000])
    def test_mismatched_duration_and_missing_section(self):
        s=self.spec();s['sections'][1]['vocal']['notes'][0]['duration_ms']=600
        with self.assertRaises(ValueError):m.checked(s)
        s=self.spec();s['order']=['chorus','chorus']
        with self.assertRaises(ValueError):m.checked(s)
        s=self.spec();s['sections'][1]['vocal']=None
        with self.assertRaises(ValueError):m.checked(s)
    def test_review_execute_and_stale_spec(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();s=self.spec()
            (root/'spec.json').write_text(json.dumps(s),encoding='utf8')
            plan,_=m.review(root,'spec.json','song.wav')
            r=m.execute(root,plan);self.assertEqual(r['status'],'section_song_pcm_verified')
            plan,_=m.review(root,'spec.json','other.wav')
            s['title']='Changed';(root/'spec.json').write_text(json.dumps(s),encoding='utf8')
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'other.wav').exists())
if __name__=='__main__':unittest.main()
