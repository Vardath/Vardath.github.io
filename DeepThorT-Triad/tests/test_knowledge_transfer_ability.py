import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.document_knowledge import DocumentKnowledge
from deepthort_local.knowledge_transfer import export_manifest,read_manifest,import_manifest,checked

class TransferTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.a=self.root/'a';self.b=self.root/'b';self.a.mkdir();self.b.mkdir()
        for p in (self.a,self.b):
            (p/'manual.md').write_text('Quartz engine calibration uses a sapphire bearing.',encoding='utf-8')
            (p/'notes.txt').write_text('Copper rotor inspection follows the workshop checklist.',encoding='utf-8')
        self.index=DocumentKnowledge(self.root/'knowledge.db')
        for p in ('manual.md','notes.txt'):self.index.index(self.a,p)
    def transfer(self):
        r=export_manifest(self.index,self.a,['manual.md','notes.txt'],'transfer.json')
        raw=(self.a/'transfer.json').read_bytes();(self.b/'transfer.json').write_bytes(raw)
        return r,raw
    def test_export_and_actual_import_search(self):
        r,raw=self.transfer();self.assertFalse(r['contains_document_bodies']);self.assertNotIn(b'sapphire',raw)
        _,sha=read_manifest(self.b,'transfer.json');result=import_manifest(self.index,self.b,'transfer.json',sha)
        self.assertEqual(result['documents'],2)
        hits=self.index.search(self.b,'sapphire bearing')
        self.assertEqual(hits[0]['path'],'manual.md');self.assertIn('sapphire',hits[0]['excerpt'])
    def test_stale_source_atomic_refusal(self):
        self.transfer();_,sha=read_manifest(self.b,'transfer.json')
        (self.b/'notes.txt').write_text('changed',encoding='utf-8')
        with self.assertRaises(ValueError):import_manifest(self.index,self.b,'transfer.json',sha)
        self.assertEqual(self.index.documents(self.b),[])
    def test_exclusions_and_changed_manifest(self):
        self.transfer();m,sha=read_manifest(self.b,'transfer.json')
        with self.assertRaises(ValueError):import_manifest(self.index,self.b,'transfer.json',sha,exclude=['notes.txt'])
        (self.b/'transfer.json').write_text(json.dumps(m))
        with self.assertRaises(ValueError):import_manifest(self.index,self.b,'transfer.json',sha)
        self.assertEqual(self.index.documents(self.b),[])
    def test_no_overwrite_and_unsafe_manifest(self):
        self.transfer()
        with self.assertRaises(ValueError):export_manifest(self.index,self.a,['manual.md'],'transfer.json')
        m,_=read_manifest(self.b,'transfer.json');m['documents'][0]['path']='../manual.md'
        with self.assertRaises(ValueError):checked(m)
