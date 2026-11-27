import io
import json
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from deepthort_local.tempo_detection import estimate,checked,review,execute
def clicks(times,seconds=8,channels=1,width=2):
    rate=8000;frames=bytearray(rate*seconds*channels*width)
    if width==2:
        for t in times:
            for i in range(int(t*rate),int(t*rate)+80):
                for c in range(channels):struct.pack_into('<h',frames,(i*channels+c)*2,15000)
    b=io.BytesIO()
    with wave.open(b,'wb') as f:
        f.setnchannels(channels);f.setsampwidth(width);f.setframerate(rate);f.writeframes(frames)
    return b.getvalue()
SPEC={'audio':'audio.wav','min_bpm':40,'max_bpm':240}
class TempoTests(unittest.TestCase):
    def test_observed_click_tempos(self):
        for bpm,interval,channels in ((120,.5,1),(75,.8,2)):
            r=estimate(clicks([.2+i*interval for i in range(8)],channels=channels),checked(SPEC))
            self.assertEqual(r['status'],'steady_tempo_estimate');self.assertAlmostEqual(r['tempo_bpm'],bpm,delta=1)
            self.assertGreaterEqual(r['interval_support'],6)
    def test_silence_and_irregular(self):
        self.assertIsNone(estimate(clicks([]),SPEC)['tempo_bpm'])
        r=estimate(clicks([.1,.4,1.1,2.1,3.4,4.9,6.6]),SPEC)
        self.assertIsNone(r['tempo_bpm'])
    def test_unsupported_format_and_range(self):
        with self.assertRaises(ValueError):estimate(clicks([],width=1),SPEC)
        with self.assertRaises(ValueError):checked(dict(SPEC,min_bpm=200,max_bpm=100))
    def test_review_output_and_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();audio=root/'audio.wav';raw=clicks([.2+i*.5 for i in range(8)]);audio.write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(SPEC));plan,_=review(root,'spec.json','out.json');execute(root,plan)
            self.assertEqual(json.loads((root/'out.json').read_text())['tempo_bpm'],120)
            self.assertEqual(audio.read_bytes(),raw)
            (root/'out.json').unlink();audio.write_bytes(clicks([]))
            with self.assertRaises(ValueError):execute(root,plan)
