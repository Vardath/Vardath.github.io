import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.bibliography import review,execute,checked

class BibliographyTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.src=self.root/'draft.txt';self.spec=self.root/'refs.json'
        self.src.write_bytes(b'A claim [[cite:b]]. Another [[cite:a]]. Again [[cite:b]].\r\n')
        self.data={'manuscript':'draft.txt','style':'numeric','references':[
            {'id':'a','authors':['Ada Example'],'year':2022,'title':'Source A','publication':'Journal','locator':'pp. 1–2'},
            {'id':'b','authors':['Ben Example','C. Example'],'year':None,'title':'Source B','publication':'','locator':'https://example.com/b'}]}
        self.save()
    def save(self):self.spec.write_text(json.dumps(self.data,ensure_ascii=False),encoding='utf-8')
    def test_numeric_order_and_source_preservation(self):
        original=self.src.read_bytes();plan,preview=review(self.root,'refs.json','out.txt');r=execute(self.root,plan)
        out=(self.root/'out.txt').read_text(encoding='utf-8')
        self.assertTrue(out.startswith('A claim [1]. Another [2]. Again [1].\n'))
        self.assertLess(out.index('[1] Ben Example'),out.index('[2] Ada Example'))
        self.assertEqual(out,preview['resolved_document']);self.assertEqual(r['citation_occurrences'],3)
        self.assertFalse(r['metadata_independently_verified']);self.assertFalse(r['claim_support_verified'])
        self.assertEqual(self.src.read_bytes(),original)
    def test_author_year(self):
        self.data['style']='author_year';self.save();plan,_=review(self.root,'refs.json','out.txt');execute(self.root,plan)
        out=(self.root/'out.txt').read_text(encoding='utf-8')
        self.assertIn('(Ben Example et al., n.d.)',out);self.assertIn('(Ada Example, 2022)',out)
        self.data['references'][1]['authors']=['Ada Example'];self.data['references'][1]['year']=2022
        with self.assertRaises(ValueError):checked(self.data)
    def test_invalid_markers_and_unused_records(self):
        for text in ('[[cite:unknown]]','[[cite:a]]','[[cite:a]] [[cite:b]] [[cite:broken','No citations'):
            self.src.write_text(text,encoding='utf-8')
            with self.assertRaises(ValueError):review(self.root,'refs.json','out.txt')
    def test_stale_and_no_overwrite(self):
        plan,_=review(self.root,'refs.json','out.txt');out=self.root/'out.txt';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink();self.src.write_text('Changed',encoding='utf-8')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertFalse(out.exists())
