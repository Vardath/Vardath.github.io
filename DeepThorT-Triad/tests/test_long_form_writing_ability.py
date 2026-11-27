import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.long_form_writing import review,execute,checked

class LongFormTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.src=self.root/'draft.json'
        self.data={'title':'A revised manuscript','outline':[
            {'id':'intro','heading':'Introduction','level':1,'min_words':3},
            {'id':'detail','heading':'Details','level':2,'min_words':2},
            {'id':'end','heading':'Conclusion','level':1,'min_words':2}],
            'drafts':{'end':['Final remarks.'],'intro':['First reviewed paragraph.','Unicode café and 日本語.'],'detail':['Technical details.']}}
        self.save()
    def save(self):self.src.write_text(json.dumps(self.data,ensure_ascii=False),encoding='utf-8')
    def test_complete_order_and_literal_text(self):
        original=self.src.read_bytes();plan,preview=review(self.root,'draft.json','out.txt');r=execute(self.root,plan)
        text=(self.root/'out.txt').read_text(encoding='utf-8')
        self.assertEqual(text,'A revised manuscript\n\n1 Introduction\n\nFirst reviewed paragraph.\n\nUnicode café and 日本語.\n\n1.1 Details\n\nTechnical details.\n\n2 Conclusion\n\nFinal remarks.\n\n')
        self.assertEqual(r['sections'],3);self.assertEqual(r['section_receipts'],preview['section_receipts'])
        self.assertFalse(r['semantic_quality_verified']);self.assertEqual(self.src.read_bytes(),original)
    def test_outline_and_word_requirements(self):
        del self.data['drafts']['detail']
        with self.assertRaises(ValueError):checked(self.data)
        self.data['drafts']['detail']=['Short']
        with self.assertRaises(ValueError):checked(self.data)
        self.data['drafts']['detail']=['Now adequate'];self.data['outline'][1]['level']=3
        with self.assertRaises(ValueError):checked(self.data)
    def test_large_manuscript(self):
        self.data['drafts']['intro']=['word '*999+'end']*30;self.save()
        plan,_=review(self.root,'draft.json','out.txt');r=execute(self.root,plan)
        self.assertGreater((self.root/'out.txt').stat().st_size,100000);self.assertGreater(r['words'],29000)
    def test_stale_and_no_overwrite(self):
        plan,_=review(self.root,'draft.json','out.txt');out=self.root/'out.txt';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink()
        self.data['title']='Changed';self.save()
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertFalse(out.exists())
