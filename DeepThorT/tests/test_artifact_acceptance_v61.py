import json
import tempfile
import unittest
import struct
import zlib
import zipfile
from pathlib import Path
from deepthort_local.artifact_acceptance import validate,verify
from deepthort_local.tool_workflows import artifact,freeze,ToolWorkflows
from deepthort_local.janus_engine import JanusStore
from deepthort_local.mixed_roadmap import parse_tasks
from tests.test_tool_workflows_v61 import Recipes

def png(width,height):
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,0,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\0'*width)*height))+chunk(b'IEND',b'')

class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
    def test_exact_dimensions_and_changed_evidence(self):
        p=self.root/'image.png';p.write_bytes(png(4,8))
        rec=artifact(self.root,p.name)
        self.assertEqual(verify(self.root,p.name,{'width':4,'height':8},rec)['observed'],{'width':4,'height':8})
        with self.assertRaisesRegex(ValueError,'acceptance failed'):verify(self.root,p.name,{'width':8},rec)
        p.write_bytes(png(8,4))
        with self.assertRaises(ValueError):verify(self.root,p.name,{'width':8},rec)
    def test_geometry_and_archive_contract(self):
        p=self.root/'mesh.obj';p.write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n')
        self.assertEqual(verify(self.root,p.name,{'min_vertices':3,'min_faces':1},artifact(self.root,p.name))['observed']['min_faces'],1)
        with self.assertRaises(ValueError):verify(self.root,p.name,{'min_faces':2},artifact(self.root,p.name))
        z=self.root/'pack.zip'
        with zipfile.ZipFile(z,'w') as f:f.writestr('assets/mesh.obj','data')
        rec=artifact(self.root,z.name)
        verify(self.root,z.name,{'required_members':['assets/mesh.obj']},rec)
        with self.assertRaises(ValueError):verify(self.root,z.name,{'required_members':['missing']},rec)
    def test_unsupported_and_invalid_criteria(self):
        for checks in ({'width':True},{'width':0},{'eval':'code'},{}, {'min_faces':1}):
            with self.assertRaises(ValueError):validate('image.png',checks)
        with self.assertRaises(ValueError):validate('pack.zip',{'required_members':['../file']})
    def test_specification_parsing_keeps_exact_checks(self):
        plan={'project':str(self.root),'schedule':[]}
        task={'after':0,'goal':'Create 4 by 8 image','output':'image.png','acceptance':{'width':4,'height':8}}
        parsed=parse_tasks(json.dumps({'artifacts':[task]}),plan,1)
        self.assertEqual(parsed[0]['acceptance'],task['acceptance'])
    def test_workflow_rejects_valid_structure_wrong_properties(self):
        j=JanusStore(self.root/'janus.sqlite');w=ToolWorkflows(j);r=Recipes(self.root)
        original=r._recipe_row
        def recipe(ident,root):
            row=original(ident,root)
            return {**row,'artifact':'image.png'}
        r._recipe_row=recipe
        manifest=freeze(r,self.root,[{'recipe_id':1,'input':''}],continuation=True)
        manifest['mixed_task']={'output':'image.png','acceptance':{'width':8}}
        ident=w.approve(manifest,user_approved=True)
        self.assertIn('queued',w.tick())
        a=j.claim_next_action();self.assertIsNotNone(a)
        (self.root/'image.png').write_bytes(png(4,8))
        log=self.root/'run.log';log.write_text('ok')
        j.update_action(a['id'],'succeeded',detail='ok',returncode=0,output_file=str(log))
        self.assertIn('acceptance failed',w.tick())
        self.assertEqual(w.get(ident)['state'],'blocked')
        self.assertIsNone(w.stages(ident)[0]['receipt'])
if __name__=='__main__':unittest.main()
