import json
import struct
import tempfile
import unittest
from pathlib import Path
from deepthort_local.artifact_types import artifact_type,require_text_target,require_checked_receipt
from deepthort_local.artifact_media_checks import wav,glb,dds,pe
from deepthort_local.agent_plan import parse_build_plan,PlanError

class ArtifactTypeTests(unittest.TestCase):
    def test_binary_output_not_text_plan(self):
        with tempfile.TemporaryDirectory() as t:
            for name in ('mesh.blend','texture.PNG','sound.wav','game.exe','mod.zip','ship.xmf'):
                with self.assertRaises(PlanError):
                    parse_build_plan(json.dumps({'files':[{'path':name,'description':'Produce asset'}]}),t,fragment=True)
            self.assertEqual(require_text_target('mesh.obj')['kind'],'mesh')
            self.assertEqual(require_text_target('game.gd')['producer'],'text')

    def test_typed_receipts_do_not_accept_bytes_only(self):
        task={'output':'mesh.glb','artifact_type':artifact_type('mesh.glb')}
        with self.assertRaises(ValueError):require_checked_receipt(task,{'scope':'nonempty bytes only'})
        self.assertTrue(require_checked_receipt(task,{'scope':'GLB structural check'}))
        task={'output':'scene.blend','artifact_type':artifact_type('scene.blend')}
        with self.assertRaises(ValueError):require_checked_receipt(task,{'scope':'some check'})

    def test_wave_container(self):
        fmt=struct.pack('<HHIIHH',1,1,8000,16000,2,16)
        body=b'WAVEfmt '+struct.pack('<I',16)+fmt+b'data'+struct.pack('<I',4)+b'\0'*4
        valid=b'RIFF'+struct.pack('<I',len(body))+body
        self.assertIn('8000 Hz',wav(valid))
        with self.assertRaises(ValueError):wav(valid[:-1])

    def test_glb_container(self):
        raw=json.dumps({'asset':{'version':'2.0'},'meshes':[{'primitives':[]}],'buffers':[{'byteLength':4}]}).encode()
        raw+=b' '*((-len(raw))%4)
        chunks=struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',4,0x004e4942)+b'\0'*4
        valid=struct.pack('<4sII',b'glTF',2,12+len(chunks))+chunks
        self.assertIn('GLB v2',glb(valid))
        with self.assertRaises(ValueError):glb(valid[:-1])

    def test_invalid_dds_and_pe(self):
        with self.assertRaises(ValueError):dds(b'DDS '+b'\0'*124)
        with self.assertRaises(ValueError):pe(b'MZ'+b'\0'*100)

if __name__=='__main__':unittest.main()
