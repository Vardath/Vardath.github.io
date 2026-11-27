import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.source_credibility import assess,review,execute,load_report
from deepthort_local.multi_source_research import assemble
from deepthort_local.webpage_retrieval import extract

Q={'question':'Quartz calibration','urls':['https://example.org/a','https://example.net/b','https://example.com/c']}
TEXT=b'Quartz calibration\nWritten by Alice Smith\nPublished 2025-01-10\nMethods: sample size 20\nFunded by Fixture Corp\nReferences\nCorrection policy'
PAGES=[extract(url,TEXT,'text/plain','utf-8') for url in Q['urls'][:2]]+[None]
RAW=json.dumps(assemble(Q,PAGES)).encode()
F={'source_id':'S1','dimension':'conflicts_funding','assessment':'raises_concern','line':5,'start':0,
   'quote':'Funded by Fixture Corp','reason':'Review potential funding influence.'}
SPEC={'research':'research.json','findings':[F]}
class CredibilityTests(unittest.TestCase):
    def test_observed_cues_and_reviewed_finding(self):
        r=assess(SPEC,RAW);a,b,c=r['sources']
        for name,d in a['dimensions'].items():
            self.assertEqual(d['cue_status'],'literal_cue_found',name)
            self.assertFalse(d['verified_as_true'])
            for e in d['observed_excerpts']:
                line=PAGES[0]['text'].split('\n')[e['line']-1]
                self.assertEqual(line[e['start']:e['start']+len(e['quote'])],e['quote'])
        self.assertEqual(a['dimensions']['conflicts_funding']['reviewer_finding'],F)
        self.assertEqual(b['duplicate_text_of'],'S1');self.assertEqual(c['assessment_status'],'unavailable')
        self.assertFalse(r['credibility_independently_verified']);self.assertFalse(r['claims_verified'])
    def test_missing_not_negative_and_exact_quote(self):
        p=extract(Q['urls'][0],b'Quartz calibration only','text/plain','utf-8')
        r=assess(dict(SPEC,findings=[]),json.dumps(assemble(Q,[p,None,None])).encode())
        self.assertTrue(all(v['cue_status']=='no_literal_cue_detected' for v in r['sources'][0]['dimensions'].values()))
        for f in (dict(F,quote='Fabricated'),dict(F,start=1),dict(F,source_id='S3')):
            with self.assertRaises(ValueError):assess(dict(SPEC,findings=[f]),RAW)
    def test_tampered_report_and_duplicate_review(self):
        report=json.loads(RAW);report['sources'][0]['evidence']['text']='tampered'
        with self.assertRaises(ValueError):load_report(json.dumps(report).encode())
        report=json.loads(RAW);report['distinct_text_count']=3
        with self.assertRaises(ValueError):load_report(json.dumps(report).encode())
        with self.assertRaises(ValueError):assess(dict(SPEC,findings=[F,F]),RAW)
    def test_guarded_publication_and_changed_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'research.json';p.write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(SPEC))
            plan,_=review(root,'spec.json','credibility.json')
            r=execute(root,plan);self.assertEqual(r['reviewer_findings_count'],1)
            self.assertFalse(json.loads((root/'credibility.json').read_text())['claims_verified'])
            with self.assertRaises(ValueError):execute(root,plan)
            (root/'credibility.json').unlink();p.write_bytes(RAW+b'\n')
            with self.assertRaises(ValueError):execute(root,plan)
