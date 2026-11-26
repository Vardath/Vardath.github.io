import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.creative_core import (
    create_midi, parse_score, midi, budget_ok, GIB, BUDGET, is_midi_request)
from deepthort_local.creative_profile import manifest, REVISION, FILES, MIN_BYTES, installed

SCORE={'bpm':100,'notes':[[60,480],[62,480],[64,480],[65,480]]}


class CreativeCoreTests(unittest.TestCase):
    def test_real_midi_file_from_scripted_worker(self):
        def generate(folder,cancelled,notify):
            req=json.loads((folder/'request.json').read_text('utf-8'))
            self.assertEqual(req['requester'],'janus')
            self.assertIn('ascending',req['brief'])
            return json.dumps(SCORE),42
        with tempfile.TemporaryDirectory() as tmp:
            folder,receipt=create_midi(root=tmp,requester='janus',scope='project:job:1',
                brief='Create ascending MIDI',generate=generate,accept=lambda s:s==SCORE)
            raw=(folder/'score.mid').read_bytes()
            self.assertEqual(raw[:14],bytes.fromhex('4d546864000000060000000101e0'))
            self.assertEqual(int.from_bytes(raw[18:22],'big'),len(raw)-22)
            self.assertIn(bytes.fromhex('00ff51030927c0'),raw)
            self.assertEqual(raw.count(bytes.fromhex('0080')),0)
            for p in (60,62,64,65):
                self.assertIn(bytes([0,0x90,p,80,0x83,0x60,0x80,p,0]),raw)
            self.assertFalse(receipt['native_inference_verified'])
            self.assertFalse(receipt['project_publication_authorized'])
            self.assertEqual(json.loads((folder/'receipt.json').read_text('utf-8')),receipt)

    def test_invalid_or_wrong_output_not_published(self):
        for answer in ('{"bpm":100,"bpm":90,"notes":[]}',json.dumps({'bpm':100,'notes':[[60,480]]*4})):
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(ValueError):
                    create_midi(root=tmp,requester='user',scope='a',brief='MIDI',
                        generate=lambda *x:(answer,42),accept=lambda s:s==SCORE)
                folders=list((Path(tmp)/'state'/'creative-tasks').iterdir())
                self.assertEqual(len(folders),1)
                self.assertFalse((folders[0]/'score.mid').exists())
                self.assertTrue((folders[0]/'failure.json').exists())

    def test_scope_cancel_and_routing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                create_midi(root=tmp,requester='unknown',scope='a',brief='MIDI')
            with self.assertRaises(RuntimeError):
                create_midi(root=tmp,requester='user',scope='a',brief='MIDI',cancelled=lambda:True)
        self.assertTrue(is_midi_request('Compose a short MIDI melody'))
        self.assertFalse(is_midi_request('Explain how to create MIDI'))
        self.assertFalse(is_midi_request('Create a game with MIDI music'))
        self.assertFalse(is_midi_request('Create a MIDI file and edit my project'))

    def test_strict_score_validation(self):
        for invalid in (
            {'bpm':True,'notes':SCORE['notes']},
            {'bpm':100,'notes':[[128,480]]*4},
            {'bpm':100,'notes':[[60,0]]*4},
            {'bpm':100,'notes':SCORE['notes'],'command':'run anything'}):
            with self.assertRaises(ValueError):parse_score(json.dumps(invalid))
        self.assertEqual(parse_score(json.dumps(SCORE)),SCORE)

    def test_memory_admission(self):
        self.assertTrue(budget_ok(20*GIB,20*GIB,40*GIB,10*GIB))
        self.assertFalse(budget_ok(20*GIB,20*GIB,40*GIB,13*GIB))
        self.assertFalse(budget_ok(20*GIB,8*GIB,40*GIB,10*GIB))

    def test_pinned_multimodal_profile(self):
        entries=[{'rfilename':name,'size':MIN_BYTES if name=='openvino_language_model.bin' else 10,
                  'lfs':{'sha256':'a'*64}} for name in FILES]
        data={'sha':REVISION,'siblings':entries}
        self.assertEqual(set(manifest(data)['files']),FILES)
        with self.assertRaises(ValueError):manifest({'sha':'wrong','siblings':entries})
        with self.assertRaises(ValueError):manifest({'sha':REVISION,'siblings':entries[:-1]})
        with tempfile.TemporaryDirectory() as tmp:self.assertFalse(installed(tmp))


if __name__=='__main__':
    unittest.main()
