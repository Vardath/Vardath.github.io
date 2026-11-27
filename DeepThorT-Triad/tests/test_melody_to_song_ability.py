from array import array
import json,math,tempfile,unittest
from pathlib import Path
from deepthort_local import melody_to_song as m
from deepthort_local.noise_reduction import encode

SPEC={'audio':'melody.wav','bpm':120,'min_pitch':48,'max_pitch':80,'gate_dbfs':-45,'tonic':0,'mode':'major',
      'repeats':2,'lead_timbre':'sine','backing_timbre':'organ','peak_dbfs':-3}
def fixture():
    data=array('h')
    for pitch,seconds in [(None,.5),(60,.75),(None,.5),(67,.75),(None,.5)]:
        data.extend(round(12000*math.sin(2*math.pi*m.transcription.frequency(pitch)*i/8000)) if pitch is not None else 0 for i in range(round(seconds*8000)))
    return encode(data,8000,1)

class MelodySongTests(unittest.TestCase):
    def test_preserve_notes_and_repeat(self):
        notes=[[0,480,60],[720,240,64],[960,480,67]]
        raw,settings,chords,phrase=m.compose(notes,SPEC)
        score=m.arrangement.inspect(raw)
        self.assertEqual(phrase,1440)
        self.assertEqual(score['parts'][0]['notes'],[[a+off,b,p,90] for off in (0,1440) for a,b,p in notes])
        self.assertEqual(chords[0]['degree'],1)
        self.assertEqual(len(score['parts']),3)
    def test_actual_audio_to_song(self):
        raw,report=m.generate(fixture(),SPEC)
        self.assertEqual([x[2] for x in report['observed_notes']],[60,67])
        self.assertEqual(report['parts'],3);self.assertEqual(report['channels'],2)
        self.assertTrue(raw.startswith(b'RIFF'));self.assertFalse(report['neural_song_generation'])
        self.assertFalse(report['source_audio_copied'])
    def test_guard_and_bounds(self):
        with self.assertRaises(ValueError):m.compose([[0,30000,60]],SPEC)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'melody.wav').write_bytes(fixture())
            (root/'spec.json').write_text(json.dumps(SPEC),encoding='utf8')
            plan,_=m.review(root,'spec.json','song.wav')
            (root/'melody.wav').write_bytes(b'changed')
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'song.wav').exists())
if __name__=='__main__':unittest.main()
