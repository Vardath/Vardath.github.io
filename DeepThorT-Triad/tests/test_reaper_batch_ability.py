import io,tempfile,unittest,wave
from pathlib import Path
from deepthort_local import reaper_batch as m
def wav(rate,frames):
    buf=io.BytesIO()
    with wave.open(buf,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(b'\x01\x00'*frames)
    return buf.getvalue()
class Backend:
    def run(self,plan,raw,cancelled):
        return wav(plan['target'],480)
class ReaperTests(unittest.TestCase):
    def test_review_and_publish(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td).resolve();root=base/'project';root.mkdir();exe=base/m.EXE;exe.write_bytes(b'fixture')
            src=root/'input.wav';raw=wav(44100,441);src.write_bytes(raw)
            plan=m.review(root,'input.wav','out.wav',str(exe),48000)
            self.assertIn('-newinst',m.command(plan,root));self.assertIn('-cfgfile',m.command(plan,root))
            self.assertIn('SRATE 48000',m.config(plan,root))
            self.assertNotIn('FXCHAIN',m.config(plan,root))
            with self.assertRaises(PermissionError):m.render(root,plan,backend=Backend())
            result=m.render(root,plan,approved=True,backend=Backend())
            self.assertFalse(result['native_engine_used']);self.assertEqual(result['audio']['frames'],480)
            self.assertEqual(src.read_bytes(),raw)
            with self.assertRaises(ValueError):m.render(root,plan,approved=True,backend=Backend())
    def test_stale_and_cancel(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td).resolve();root=base/'project';root.mkdir();exe=base/m.EXE;exe.write_bytes(b'fixture')
            (root/'input.wav').write_bytes(wav(44100,441));plan=m.review(root,'input.wav','out.wav',str(exe),48000)
            with self.assertRaises(ValueError):m.render(root,plan,lambda:True,approved=True,backend=Backend())
            exe.write_bytes(b'changed')
            with self.assertRaises(ValueError):m.render(root,plan,approved=True,backend=Backend())
            self.assertFalse((root/'out.wav').exists())
    def test_output_contract(self):
        p={'input':m.audio(wav(44100,441)),'target':48000}
        for raw in (wav(44100,441),wav(48000,400),b'broken'):
            with self.assertRaises(ValueError):m.verify(p,raw)
        self.assertEqual(m.verify(p,wav(48000,480))['rate'],48000)

if __name__=='__main__':unittest.main()
