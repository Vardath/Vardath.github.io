import io,tempfile,unittest,wave
from pathlib import Path
from deepthort_local import audio_transcription as t
def audio(seconds):
    b=io.BytesIO()
    with wave.open(b,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\x01\x00'*int(seconds*16000))
    return b.getvalue()
class Backend:
    def __init__(self):self.n=0
    def recognize(self,raw,culture,cancelled):
        self.n+=1
        return {'culture':culture,'recognizer_id':'fixture','segments':[{'text':'window '+str(self.n),'confidence':.8,'start_seconds':.1,'duration_seconds':.5}]}
class TranscriptionTests(unittest.TestCase):
    def test_balanced_windows_and_timing(self):
        raw=audio(60.25);chunks=list(t.windows(raw))
        self.assertEqual(len(chunks),3);self.assertAlmostEqual(sum(c[1] for c in chunks),60.25)
        self.assertTrue(all(1<=c[1]<=30 for c in chunks))
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'input.wav';src.write_bytes(raw);plan,_=t.review(td,'input.wav','result.json','en-AU')
            backend=Backend()
            with self.assertRaises(PermissionError):t.transcribe(td,plan,backend=backend)
            result=t.transcribe(td,plan,approved=True,backend=backend)
            self.assertEqual(backend.n,3);self.assertFalse(result['accuracy_verified'])
            self.assertAlmostEqual(result['segments'][2]['start_seconds'],chunks[2][0]+.1,places=4)
            with self.assertRaises(PermissionError):t.save(td,plan,result)
            t.save(td,plan,result,approved=True)
            self.assertTrue((Path(td)/'result.json').is_file());self.assertEqual(src.read_bytes(),raw)
            with self.assertRaises(ValueError):t.save(td,plan,result,approved=True)
    def test_stale_and_cancel(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'input.wav';p.write_bytes(audio(2))
            plan,_=t.review(td,'input.wav','result.json','en-US')
            with self.assertRaises(ValueError):t.transcribe(td,plan,lambda:True,approved=True,backend=Backend())
            p.write_bytes(audio(3))
            with self.assertRaises(ValueError):t.transcribe(td,plan,approved=True,backend=Backend())
            self.assertFalse((Path(td)/'result.json').exists())
    def test_bad_format_and_bounds(self):
        for raw in (b'bad',audio(.5),audio(121)):
            with self.assertRaises(ValueError):list(t.windows(raw))
