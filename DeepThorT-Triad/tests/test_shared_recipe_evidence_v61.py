import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local.janus_engine import JanusStore
from deepthort_local.tool_acquisition import ToolAcquisition
from deepthort_local.tool_workflows import artifact,MAX_ARTIFACT
from deepthort_local.action_guards import MAX_HASH_BYTES

class SharedRecipeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.project=self.root/'project';self.project.mkdir()
        self.exe=self.root/'python.exe';self.exe.write_bytes(b'fixture')
        self.janus=JanusStore(self.root/'janus.sqlite')
        self.store=ToolAcquisition(self.root/'tools.sqlite')
        self.store.discover([{'name':'Python','location':str(self.exe),'found':True}])
        a=self.store.authorize_probe('Python',self.project,self.janus,user_approved=True)
        log=self.root/'help.log';log.write_text('Python script.py output')
        self.janus.update_action(a,'succeeded',detail='fixture',returncode=0,output_file=str(log))
        self.source=self.project/'source.py';self.source.write_text('print(1)')

    def recipe(self,output):
        request_id=len(self.janus.actions())+1
        self.store.start_learning(request_id,'Python',self.project,'Produce requested file')
        return self.store.propose_recipe(request_id,json.dumps(dict(title='Generate '+output,purpose='Produce requested file',
                            args=['{{input}}','{{output}}'],artifact=output)))

    def run_recipe(self,ident):
        a=self.store.authorize_recipe(ident,self.project,self.janus,user_approved=True,input_file='source.py')
        log=self.root/'run.log';log.write_text('success')
        self.janus.update_action(a,'succeeded',detail='fixture',returncode=0,output_file=str(log))
        return a

    def test_malformed_native_output_and_legacy_receipt(self):
        ident=self.recipe('out.png');self.run_recipe(ident)
        p=self.project/'out.png';p.write_bytes(b'not a png')
        # Simulate a historical hash-only success without rewriting history.
        import hashlib
        with self.store._db() as db:
            db.execute("UPDATE learned_recipes SET status='artifact_produced',artifact_after=?,log_sha=? WHERE id=?",
                (hashlib.sha256(p.read_bytes()).hexdigest(),hashlib.sha256(b'success').hexdigest(),ident))
        self.assertEqual(self.store.reconcile(ident,self.project,self.janus)['status'],'unverified')
        self.assertEqual(self.store.current_recipes(self.project,self.janus),[])

    def test_large_output_reuses_shared_structural_receipt(self):
        ident=self.recipe('out.wav')
        p=self.project/'out.wav'
        size=MAX_ARTIFACT+1024
        def write_wave(rate):
            header=b'RIFF'+struct.pack('<I',size+36)+b'WAVEfmt '+struct.pack('<IHHIIHH',16,1,1,rate,rate*2,2,16)+b'data'+struct.pack('<I',size)
            with p.open('wb') as f:f.write(header);f.truncate(size+44)
        write_wave(8000)
        self.run_recipe(ident)
        self.assertEqual(self.store.reconcile(ident,self.project,self.janus)['status'],'unverified')
        write_wave(16000)
        receipt=artifact(self.project,p.name)
        outcome=self.store.reconcile(ident,self.project,self.janus)
        self.assertEqual(outcome['status'],'artifact_produced')
        self.assertEqual(outcome['artifact_sha256'],receipt['sha256'])
        self.assertEqual(outcome['artifact_scope'],receipt['scope'])
        self.assertEqual(outcome['artifact_bytes'],receipt['bytes'])
        self.source.write_text('print(2)')
        self.assertEqual(self.store.reconcile(ident,self.project,self.janus)['status'],'unverified')

    def test_unsupported_native_format_not_promoted(self):
        ident=self.recipe('out.blend');self.run_recipe(ident)
        (self.project/'out.blend').write_bytes(b'fixture')
        self.assertIn('format-specific',self.store.reconcile(ident,self.project,self.janus)['evidence'])

    def test_large_input_cannot_fall_back_to_stat_only(self):
        ident=self.recipe('out.txt')
        with self.source.open('wb') as f:f.truncate(MAX_HASH_BYTES+1)
        with self.assertRaises(ValueError):
            self.store.authorize_recipe(ident,self.project,self.janus,user_approved=True,input_file='source.py')
        self.assertEqual(len(self.janus.actions()),1)

    def test_malformed_xml_and_zip_are_reported_as_unverified(self):
        for name,data in [('out.xml',b'<root>'),('out.zip',b'invalid zip')]:
            ident=self.recipe(name);self.run_recipe(ident)
            (self.project/name).write_bytes(data)
            self.assertEqual(self.store.reconcile(ident,self.project,self.janus)['status'],'unverified')

if __name__=='__main__':unittest.main()
