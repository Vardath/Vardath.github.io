import copy
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.research_report import render,review,execute
from deepthort_local.multi_source_research import assemble
from deepthort_local.webpage_retrieval import extract
Q={'question':'Quartz calibration','urls':['https://example.org/a','https://example.net/b']}
RAW=json.dumps(assemble(Q,[extract(Q['urls'][0],b'Quartz calibration succeeds.','text/plain','utf-8'),None])).encode()
REF={'source_id':'S1','line':1,'start':0,'quote':'Quartz calibration succeeds.'}
SPEC={'research':'research.json','title':'Quartz <report>','sections':[{'heading':'Evidence','paragraphs':[
      {'text':'The retrieved source reports success. [[S1]]','evidence':[REF]}]}],
      'limitations':['One source unavailable.']}
class ReportTests(unittest.TestCase):
    def test_html_source_links_and_quote(self):
        data,count=render(SPEC,RAW);h=data.decode()
        self.assertEqual(count,1);self.assertIn('Quartz &lt;report&gt;',h)
        self.assertIn('href="#source-S1"',h);self.assertIn('id="source-S1"',h)
        self.assertIn('Quartz calibration succeeds.',h);self.assertIn('unavailable',h)
        self.assertIn('Content-Security-Policy',h);self.assertNotIn('href="https:',h)
    def test_invalid_quote_and_citation(self):
        for k,v in [('quote','Invented'),('start',1),('source_id','S2')]:
            s=copy.deepcopy(SPEC);s['sections'][0]['paragraphs'][0]['evidence'][0][k]=v
            if k=='source_id':s['sections'][0]['paragraphs'][0]['text']='Missing. [[S2]]'
            with self.assertRaises(ValueError):render(s,RAW)
        s=copy.deepcopy(SPEC);s['sections'][0]['paragraphs'][0]['text']='No citation'
        with self.assertRaises(ValueError):render(s,RAW)
    def test_escaping_and_untrusted_content(self):
        s=copy.deepcopy(SPEC);s['sections'][0]['paragraphs'][0]['text']='<script>alert(1)</script> [[S1]]'
        data,_=render(s,RAW)
        self.assertIn(b'&lt;script&gt;',data);self.assertNotIn(b'<script>',data)
    def test_guarded_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'research.json';p.write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(SPEC))
            plan,_=review(root,'spec.json','report.html');r=execute(root,plan)
            self.assertEqual(r['verified_quote_count'],1);self.assertFalse(r['claims_verified'])
            self.assertEqual((root/'report.html').read_bytes(),render(SPEC,RAW)[0])
            with self.assertRaises(ValueError):execute(root,plan)
            (root/'report.html').unlink();p.write_bytes(RAW+b'\n')
            with self.assertRaises(ValueError):execute(root,plan)
