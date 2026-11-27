import io,json,math,tempfile,unittest,wave,zipfile,hashlib
from array import array
from pathlib import Path
from deepthort_local import audiobook_generation as a
VOICE={'id':'en','name':'Narrator','culture':'en-AU','gender':'Female'}
SPEC={'title':'Fixture book','author':'Author','culture':'en-AU','voice_id':'en','pause_ms':250,'chapters':[
    {'title':'First','passages':['First passage','Second passage']},{'title':'Second','passages':['Third passage']}]}
class Backend:
    def __init__(self):self.calls=[]
    def voices(self,cancelled):return [VOICE]
    def synthesize(self,text,voice,dest,cancelled):
        from deepthort_local.local_speech import inspect_audio
        self.calls.append((text,voice['id']))
        samples=array('h',(int(1000*math.sin(i*.2)) for i in range(a.RATE)))
        with wave.open(str(dest),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(a.RATE);w.writeframes(samples.tobytes())
        return inspect_audio(dest)
class AudiobookTests(unittest.TestCase):
    def test_chapter_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'manuscript.json';path.write_text(json.dumps(SPEC),encoding='utf-8')
            plan,_=a.review(td,'manuscript.json','book.zip',[VOICE]);b=Backend();stages=[]
            with self.assertRaises(PermissionError):a.render(td,plan,backend=b)
            r=a.render(td,plan,approved=True,backend=b,stage=stages.append)
            self.assertEqual(stages,[1,2,3]);self.assertEqual(len(b.calls),3)
            self.assertAlmostEqual(r['duration_seconds'],3.25,places=3)
            with zipfile.ZipFile(Path(td)/'book.zip') as z:
                m=json.loads(z.read('book.json'))
                self.assertEqual(m['chapters'][1]['title'],'Second')
                self.assertAlmostEqual(m['chapters'][1]['start_seconds'],2.25,places=3)
                for row in m['chapters']:
                    raw=z.read(row['file'])
                    self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
                    with wave.open(io.BytesIO(raw),'rb') as w:self.assertAlmostEqual(w.getnframes()/a.RATE,row['duration_seconds'],places=3)
                self.assertIn('Third passage',z.read('manuscript.txt').decode())
            self.assertFalse(r['published_online']);self.assertFalse(r['listening_verified'])
            with self.assertRaises(ValueError):a.render(td,plan,approved=True,backend=b)
    def test_bounds_and_stale(self):
        with self.assertRaises(ValueError):a.checked(dict(SPEC,chapters=[SPEC['chapters'][0]]*2))
        with self.assertRaises(ValueError):a.checked(dict(SPEC,chapters=[{'title':'x','passages':['a'*1001]}]))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'manuscript.json';path.write_text(json.dumps(SPEC),encoding='utf-8')
            with self.assertRaises(ValueError):a.review(td,'manuscript.json','book.zip',[])
            plan,_=a.review(td,'manuscript.json','book.zip',[VOICE])
            with self.assertRaises(ValueError):a.render(td,plan,lambda:True,approved=True,backend=Backend())
            path.write_text('{}',encoding='utf-8')
            with self.assertRaises(ValueError):a.render(td,plan,approved=True,backend=Backend())
            self.assertFalse((Path(td)/'book.zip').exists())
