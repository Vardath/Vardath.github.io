import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from deepthort_local.contract_policy_review import analyze,review,execute,checked
SPEC={'document':'terms.txt','topics':['obligations','termination','privacy'],
      'custom_checks':[{'id':'access','label':'Access review','phrases':['access log']}]}
RAW=b'The supplier must deliver.\nTermination requires notice.\nMaintain an access log.\nThe mustard is optional.\n'
class ContractTests(unittest.TestCase):
    def test_literal_evidence_and_absence(self):
        r=analyze(RAW,SPEC);checks=r['checks']
        self.assertEqual([x['matched_rows'] for x in checks],[1,1,0,1])
        self.assertEqual(checks[2]['status'],'no_literal_match_not_proof_of_absence')
        self.assertFalse(r['legal_conclusions_verified']);self.assertFalse(r['compliance_verified'])
        self.assertEqual(checks[0]['examples'][0]['quote'],'The supplier must deliver.')
    def test_pdf_exact_page_and_missing_text(self):
        b=io.BytesIO();c=Canvas(b);c.drawString(30,700,'The supplier must deliver.');c.showPage();c.showPage();c.save()
        r=analyze(b.getvalue(),dict(SPEC,document='terms.pdf'))
        self.assertEqual(r['unreadable_pdf_pages'],[2])
        self.assertEqual(r['checks'][0]['examples'][0]['location'],'page 1, extracted line 1')
    def test_stale_source_and_validation(self):
        s=copy.deepcopy(SPEC);s['custom_checks'][0]['id']='privacy'
        with self.assertRaises(ValueError):checked(s)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'terms.txt').write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(SPEC),encoding='utf-8')
            plan,_=review(root,'spec.json','evidence.json')
            self.assertEqual(execute(root,plan)['checks'],4)
            self.assertEqual(json.loads((root/'evidence.json').read_text()),analyze(RAW,SPEC))
            plan,_=review(root,'spec.json','later.json')
            (root/'terms.txt').write_bytes(RAW+b'changed')
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'later.json').exists())
