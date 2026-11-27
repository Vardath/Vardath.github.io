from array import array
import json,math,tempfile,unittest
from pathlib import Path
from deepthort_local import audio_to_midi as m
from deepthort_local.noise_reduction import encode
SPEC={'audio':'melody.wav','bpm':120,'min_pitch':48,'max_pitch':80,'gate_dbfs':-45}
def fixture(rate=8000):
    data=array('h')
    for pitch,seconds in [(None,.5),(60,.75),(None,.5),(67,.75),(None,.5)]:
        data.extend(round(12000*math.sin(2*math.pi*m.frequency(pitch)*i/rate)) if pitch is not None else 0 for i in range(round(seconds*rate)))
    return encode(data,rate,1)
class AudioMidiTests(unittest.TestCase):
    def test_pitch_and_rests(self):
        for rate in (8000,16000):
            notes,seconds=m.detect(fixture(rate),SPEC)
            self.assertEqual([n[2] for n in notes],[60,67])
            self.assertAlmostEqual(seconds,3)
            self.assertGreater(notes[0][0],400)
            self.assertGreater(notes[1][0]-sum(notes[0][:2]),350)
            self.assertEqual(m.inspect(m.midi(120,notes)),{'bpm':120,'notes':notes})
    def test_silence_and_midi_bounds(self):
        with self.assertRaises(ValueError):m.detect(encode(array('h',[0]*24000),8000,1),SPEC)
        with self.assertRaises(ValueError):m.checked(dict(SPEC,gate_dbfs=float('nan')))
        with self.assertRaises(ValueError):m.midi(120,[[0,100,60],[90,100,62]])
        with self.assertRaises(ValueError):m.inspect(m.midi(120,[[100,200,60]])[:-1])
    def test_review_and_stale(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();raw=fixture();audio=root/'melody.wav';audio.write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(SPEC));plan,_=m.review(root,'spec.json','out.mid')
            r=m.execute(root,plan)
            self.assertEqual(r['notes'],2);self.assertTrue(r['source_unchanged'])
            self.assertEqual(m.inspect((root/'out.mid').read_bytes())['notes'],r['timed_notes'])
            with self.assertRaises(ValueError):m.execute(root,plan)
            (root/'out.mid').unlink();audio.write_bytes(fixture(16000))
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'out.mid').exists())
