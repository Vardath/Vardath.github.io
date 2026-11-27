import copy
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.source_contradictions import compare,review,execute,checked
from deepthort_local.multi_source_research import assemble
from deepthort_local.webpage_retrieval import extract
Q={'question':'Quartz calibration','urls':['https://example.org/a','https://example.net/b','https://example.com/c','https://example.edu/d']}
PAGES=[extract(Q['urls'][0],b'Quartz calibration succeeds.','text/plain','utf-8'),
       extract(Q['urls'][1],b'Quartz calibration fails.','text/plain','utf-8'),
       extract(Q['urls'][2],b'Quartz calibration succeeds.','text/plain','utf-8'),None]
RAW=json.dumps(assemble(Q,PAGES)).encode()
def observation(source,position,quote):
    return dict(source_id=source,position=position,line=1,start=0,quote=quote,reason='Reviewer interpretation.')
SPEC={'research':'research.json','claims':[{'id':'calibration','claim':'Calibration succeeds','context':'Same reported test conditions',
    'observations':[observation('S1','supports','Quartz calibration succeeds.'),
                    observation('S2','opposes','Quartz calibration fails.'),
                    observation('S3','supports','Quartz calibration succeeds.')]}]}
class ContradictionTests(unittest.TestCase):
    def test_quote_bound_disagreement(self):
        r=compare(SPEC,RAW);c=r['claims'][0]
        self.assertEqual([p['status'] for p in c['pairs']],['reported_disagreement','duplicate_evidence','reported_disagreement'])
        self.assertEqual(c['resolution'],'unresolved');self.assertFalse(r['semantic_contradictions_verified'])
        self.assertEqual(c['observations'][0]['url'],Q['urls'][0])
    def test_qualification_not_contradiction(self):
        s=copy.deepcopy(SPEC);s['claims'][0]['observations'][1]['position']='qualifies'
        r=compare(s,RAW);self.assertEqual(r['reported_disagreement_count'],0)
        self.assertEqual(r['claims'][0]['pairs'][0]['status'],'qualification')
    def test_false_quote_unavailable_and_duplicate(self):
        for field,value in (('quote','fabricated'),('start',1),('source_id','S4'),('source_id','S1')):
            s=copy.deepcopy(SPEC);s['claims'][0]['observations'][1][field]=value
            with self.assertRaises(ValueError):compare(s,RAW)
        s=copy.deepcopy(SPEC);s['claims'].append(s['claims'][0])
        with self.assertRaises(ValueError):checked(s)
    def test_publication_and_review_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'research.json';p.write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(SPEC))
            plan,_=review(root,'spec.json','comparison.json');r=execute(root,plan)
            self.assertEqual(r['reported_disagreement_count'],2)
            self.assertFalse(json.loads((root/'comparison.json').read_text())['claims_verified'])
            with self.assertRaises(ValueError):execute(root,plan)
            (root/'comparison.json').unlink();p.write_bytes(RAW+b'\n')
            with self.assertRaises(ValueError):execute(root,plan)
