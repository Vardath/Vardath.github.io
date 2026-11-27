import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.analytical_report import checked,review,execute,render,verify,extract_manifest
class ReportTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.csv=self.root/'data.csv';self.spec=self.root/'spec.json'
        self.raw=b'A,Kind\n1,<script>alert(1)</script>\n2,x\n2,x\n'
        self.csv.write_bytes(self.raw)
        self.data={'title':'Reviewed <report>','expected_source_sha256':hashlib.sha256(self.raw).hexdigest(),'csv':'data.csv','delimiter':',','numeric_columns':['A'],'categorical_columns':['Kind'],'missing_tokens':[],'top_categories':5,'correlations':False}
        self.spec.write_text(json.dumps(self.data),encoding='utf-8')
    def test_deterministic_manifest_and_literal_html(self):
        p,m=render(self.raw,checked(self.data))
        self.assertTrue(verify(self.raw,self.data,p));self.assertEqual(extract_manifest(p),m)
        self.assertNotIn(b'<script>alert',p);self.assertIn(b'&lt;script&gt;',p)
        self.assertEqual(m['analysis']['rows'],3);self.assertEqual(len(m['algorithm_source_sha256']),6)
        self.assertEqual(render(self.raw,self.data)[0],p)
    def test_changed_source_refused(self):
        with self.assertRaises(ValueError):render(self.raw+b'3,x\n',checked(self.data))
        self.data['expected_source_sha256']='bad'
        with self.assertRaises(ValueError):checked(self.data)
    def test_tampered_report(self):
        payload,_=render(self.raw,checked(self.data))
        self.assertFalse(verify(self.raw,self.data,payload.replace(b'Dataset overview',b'False overview')))
    def test_review_output_and_stale(self):
        plan,preview=review(self.root,'spec.json','report.html');receipt=execute(self.root,plan)
        self.assertEqual(extract_manifest((self.root/'report.html').read_bytes()),preview['reproduction_manifest'])
        self.assertEqual(receipt['analysis_sha256'],preview['reproduction_manifest']['analysis_sha256'])
        self.assertEqual(self.csv.read_bytes(),self.raw)
        (self.root/'report.html').unlink();self.csv.write_bytes(self.raw+b'3,x\n')
        with self.assertRaises(ValueError):execute(self.root,plan)
