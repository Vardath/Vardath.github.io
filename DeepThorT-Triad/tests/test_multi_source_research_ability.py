import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.multi_source_research import collect,checked,assemble,review,execute
from deepthort_local.webpage_retrieval import extract
SPEC={'question':'Quartz engine calibration','urls':['https://example.org/a','https://example.net/b','https://example.com/c','https://example.edu/d']}
TEXT=b'Quartz engine.\nCalibration method.\nNot a verified claim.'
def fetch(url,approved,cancelled):
    if url.endswith('/d'):raise OSError('fixture unavailable')
    raw=TEXT if url.endswith(('/a','/b')) else b'Quartz bearings.'
    return extract(url,raw,'text/plain','utf-8')
def run(s,approved):return collect(s,approved=approved,retrieve=fetch)
class ResearchTests(unittest.TestCase):
    def test_exact_sources_duplicate_and_failed(self):
        urls=[]
        def capture(url,approved,cancelled):
            self.assertTrue(approved);urls.append(url);return fetch(url,approved,cancelled)
        r=collect(SPEC,approved=True,retrieve=capture)
        self.assertEqual(urls,SPEC['urls']);self.assertEqual(r['retrieved_count'],3)
        self.assertEqual(r['distinct_text_count'],2);self.assertEqual(r['sources'][1]['duplicate_text_of'],'S1')
        self.assertEqual(r['sources'][3]['status'],'unavailable')
        self.assertEqual(r['term_source_matrix']['quartz'],['S1','S3'])
        self.assertFalse(r['source_independence_verified']);self.assertFalse(r['claims_verified'])
        for source in r['sources'][:3]:
            for e in source['excerpts']:
                line=source['evidence']['text'].split('\n')[e['line']-1]
                self.assertEqual(line[e['start']:e['start']+len(e['text'])],e['text'])
    def test_missing_coverage_and_bad_hash(self):
        r=assemble(SPEC,[None]*4);self.assertEqual(r['retrieved_count'],0)
        self.assertEqual(r['uncovered_terms'],['calibration','engine','quartz'])
        p=extract(SPEC['urls'][0],TEXT,'text/plain','utf-8');p['text']='tampered'
        with self.assertRaises(ValueError):assemble(SPEC,[p,None,None,None])
    def test_scope_consent_and_cancel(self):
        for s in (dict(SPEC,urls=['https://example.org','https://example.org/']),dict(SPEC,urls=['https://example.org/a','http://example.net/b']),dict(SPEC,urls=SPEC['urls']*2)):
            with self.assertRaises(ValueError):checked(s)
        with self.assertRaises(ValueError):collect(SPEC,retrieve=lambda *_:self.fail('network'))
        with self.assertRaises(TimeoutError):collect(SPEC,approved=True,cancelled=lambda:True,retrieve=lambda *_:self.fail('network'))
    def test_review_publication_and_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'spec.json';p.write_text(json.dumps(SPEC))
            plan,_=review(root,'spec.json','research.json');r=execute(root,plan,run=run)
            self.assertEqual(r['retrieved_count'],3)
            self.assertEqual(json.loads((root/'research.json').read_text())['sources'][0]['id'],'S1')
            with self.assertRaises(ValueError):execute(root,plan,run=run)
            (root/'research.json').unlink();p.write_text(json.dumps(dict(SPEC,question='Changed question')))
            with self.assertRaises(ValueError):execute(root,plan,run=run)
