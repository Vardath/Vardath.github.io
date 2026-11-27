import json,tempfile,unittest,wave
from pathlib import Path
from deepthort_local import speaker_diarisation as d

LOG=b'Started\n0.000 -- 0.750 speaker_03\n0.500 -- 1.000 speaker_09\n1.250 -- 1.900 speaker_03\n'
class Backend:
    def __init__(self):self.calls=0
    def run(self,plan,raw,cancelled):
        self.calls+=1;return LOG

class DiarisationTests(unittest.TestCase):
    def fixture(self,folder):
        root=folder/'project';root.mkdir()
        exe=folder/d.EXE;seg=folder/'seg.onnx';emb=folder/'emb.onnx'
        for p,value in ((exe,b'fixture-exe'),(seg,b'fixture-seg'),(emb,b'fixture-emb')):p.write_bytes(value)
        with wave.open(str(root/'clip.wav'),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\0\0'*32000)
        plan=d.review(root,'clip.wav','report.json',str(exe),str(seg),str(emb),2)
        return root,plan,seg
    def test_report_and_anonymous_labels(self):
        with tempfile.TemporaryDirectory() as td:
            root,plan,_=self.fixture(Path(td).resolve());backend=Backend()
            with self.assertRaises(PermissionError):d.render(root,plan,backend=backend)
            result=d.render(root,plan,approved=True,backend=backend)
            self.assertEqual(backend.calls,1)
            self.assertEqual(result['observed_labels'],2)
            report=json.loads((root/'report.json').read_text())
            self.assertEqual([r['speaker'] for r in report['segments']],['Speaker 1','Speaker 2','Speaker 1'])
            self.assertFalse(report['speaker_identification']);self.assertFalse(report['voiceprints_retained'])
            self.assertFalse(report['audio_separated']);self.assertFalse(report['accuracy_verified'])
            self.assertIn('--clustering.num-clusters=2',d.command(plan,root/'clip.wav'))
            self.assertIn('--embedding.num-threads=1',d.command(plan,root/'clip.wav'))
            self.assertEqual(d.MEMORY_LIMIT,512*1024**2)
            with self.assertRaises(ValueError):d.render(root,plan,approved=True,backend=backend)
    def test_strict_log(self):
        for log in (b'Started\n',b'0.000 -- 1.000 speaker_00\n',
                    b'Started\n0.000 -- 3.000 speaker_00\n',
                    b'Started\n0.000 -- 1.000 speaker_00\n0.500 -- 1.500 speaker_00\n',
                    b'Started\n0.000 -- 1.000 speaker_00\n1.000 -- 1.500 speaker_xx\n'):
            with self.assertRaises(ValueError):d.parse(log,2)
        self.assertEqual(len(d.parse(LOG,2)),3)
    def test_cancel_and_stale_model(self):
        with tempfile.TemporaryDirectory() as td:
            root,plan,seg=self.fixture(Path(td).resolve());backend=Backend()
            with self.assertRaises(ValueError):d.render(root,plan,lambda:True,approved=True,backend=backend)
            seg.write_bytes(b'changed')
            with self.assertRaises(ValueError):d.render(root,plan,approved=True,backend=backend)
            self.assertEqual(backend.calls,0);self.assertFalse((root/'report.json').exists())
