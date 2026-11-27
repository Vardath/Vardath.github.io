import io
import json
import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from deepthort_local.musical_key import checked,estimate,classify,rank,MAJOR,MINOR,review,execute
SPEC={'audio':'track.wav','channel':'left'}
def tones(notes,channels=1):
    rate=8000;data=bytearray()
    for chord in notes:
        frequencies=[440*2**((m-69)/12) for m in chord]
        for i in range(rate//2):
            value=int(10000*sum(math.sin(2*math.pi*f*i/rate) for f in frequencies)/max(1,len(frequencies)))
            for c in range(channels):data.extend(struct.pack('<h',value))
    b=io.BytesIO()
    with wave.open(b,'wb') as f:
        f.setnchannels(channels);f.setsampwidth(2);f.setframerate(rate);f.writeframes(data)
    return b.getvalue()
class KeyTests(unittest.TestCase):
    def test_profiles_and_ambiguous_evidence(self):
        self.assertEqual(rank(MAJOR)[0]['tonic'],'C');self.assertEqual(rank(MAJOR)[0]['mode'],'major')
        self.assertEqual(rank(MINOR)[0]['mode'],'minor')
        self.assertIsNone(classify([1,0,0,0,0,0,0,0,0,0,0,0])['key'])
        self.assertIsNone(classify([1]*12)['key'])
    def test_synthetic_c_major_progression(self):
        raw=tones([[60,64,67],[60,64,67],[65,69,72],[67,71,74],[60,64,67],[60,64,67],[62,65,69],[60,64,67]])
        r=estimate(raw,checked(SPEC))
        self.assertEqual(r['accepted_windows'],8);self.assertGreaterEqual(r['active_pitch_classes'],4)
        self.assertIn({'tonic':'C','mode':'major'},[{k:c[k] for k in ('tonic','mode')} for c in r['candidates'][:2]])
        self.assertAlmostEqual(sum(r['pitch_class_distribution'].values()),1,places=4)
    def test_silence_single_pitch_and_missing_channel(self):
        self.assertIsNone(estimate(tones([[]]*6),SPEC)['key'])
        self.assertIsNone(estimate(tones([[69]]*6),SPEC)['key'])
        with self.assertRaises(ValueError):estimate(tones([[69]]*6),dict(SPEC,channel='right'))
    def test_review_publish_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();audio=root/'track.wav';raw=tones([[60,64,67]]*6);audio.write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(SPEC));plan,_=review(root,'spec.json','key.json')
            execute(root,plan);self.assertEqual(json.loads((root/'key.json').read_text()),estimate(raw,SPEC));self.assertEqual(audio.read_bytes(),raw)
            (root/'key.json').unlink();audio.write_bytes(tones([[69]]*6))
            with self.assertRaises(ValueError):execute(root,plan)
