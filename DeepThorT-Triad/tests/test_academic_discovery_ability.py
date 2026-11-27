import copy
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from deepthort_local.academic_discovery import checked,discover,normalize,review,execute

SPEC={'query':'quartz engine calibration','count':5,'from_year':2020,'to_year':2025}
WORK={'DOI':'10.1234/test.1','title':['Quartz engine calibration'],
      'author':[{'family':'Smith'}],'issued':{'date-parts':[[2024]]},
      'container-title':['Engineering Journal'],'type':'journal-article','publisher':'Example'}
DATA={'status':'ok','message-type':'work-list','message':{'total-results':40,'items':[WORK,dict(WORK,DOI='10.1234/test.2',title=['Quartz bearing'])]}}
def transport(host,path,**kw):return DATA,json.dumps(DATA).encode()
class AcademicTests(unittest.TestCase):
    def test_fixed_query_and_metadata(self):
        def capture(host,path,**kw):
            self.assertEqual(host,'api.crossref.org')
            p=urlsplit(path);self.assertEqual(p.path,'/works')
            q=parse_qs(p.query);self.assertEqual(q['query.bibliographic'],[SPEC['query']])
            self.assertEqual(q['filter'],['from-pub-date:2020-01-01,until-pub-date:2025-12-31'])
            self.assertEqual(q['rows'],['5'])
            return transport(host,path,**kw)
        r=discover(SPEC,approved=True,transport=capture)
        self.assertEqual(r['provider_reported_total'],40);self.assertEqual(len(r['results']),2)
        self.assertEqual(r['results'][0]['matched_title_terms'],['calibration','engine','quartz'])
        self.assertEqual(r['results'][0]['doi_url'],'https://doi.org/10.1234/test.1')
        self.assertFalse(r['systematic_review_complete']);self.assertFalse(r['claims_verified'])
    def test_duplicate_missing_and_date_difference(self):
        data=copy.deepcopy(DATA);data['message']['items']=[WORK,WORK,dict(WORK,DOI='10.1234/test.3',issued={'date-parts':[[2019]]}),{}]
        r=normalize(SPEC,data,b'{}')
        self.assertEqual(r['omitted_count'],2);self.assertEqual(r['results'][1]['original_rank'],3)
        self.assertFalse(r['results'][1]['issued_year_within_requested_bounds'])
        data['message']['items']=[];self.assertEqual(normalize(SPEC,data,b'{}')['results'],[])
    def test_invalid_and_no_consent(self):
        with self.assertRaises(ValueError):discover(SPEC,transport=lambda *_:self.fail('network'))
        for s in (dict(SPEC,count=11),dict(SPEC,from_year=2026),dict(SPEC,to_year=True),dict(SPEC,query='the and')):
            with self.assertRaises(ValueError):checked(s)
        with self.assertRaises(ValueError):normalize(SPEC,{'status':'ok','message-type':'work'},b'{}')
    def test_exact_report_and_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'spec.json';p.write_text(json.dumps(SPEC))
            plan,_=review(root,'spec.json','literature.json')
            def search(s,approved):return discover(s,approved=approved,transport=transport)
            r=execute(root,plan,search=search)
            self.assertEqual(r['result_count'],2)
            self.assertFalse(json.loads((root/'literature.json').read_text())['full_text_read'])
            with self.assertRaises(ValueError):execute(root,plan,search=search)
            (root/'literature.json').unlink();p.write_text(json.dumps(dict(SPEC,count=4)))
            with self.assertRaises(ValueError):execute(root,plan,search=search)
