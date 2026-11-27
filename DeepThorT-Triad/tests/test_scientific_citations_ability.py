import copy
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.scientific_citations import checked,verify,compare,review,execute

SPEC={'doi':'10.1234/TEST.1','title':'Quartz engine calibration','first_author_family':'Smith','year':2025}
DATA={'status':'ok','message-type':'work','message':{'DOI':'10.1234/test.1','title':['Quartz engine calibration'],
      'author':[{'family':'Smith','given':'A'}],'issued':{'date-parts':[[2025,1,2]]},
      'container-title':['Engineering Journal'],'type':'journal-article','publisher':'Example'}}
def lookup(host,path,**kw):return DATA,json.dumps(DATA).encode()
class CitationTests(unittest.TestCase):
    def test_exact_doi_lookup_and_local_fields(self):
        def transport(host,path,**kw):
            self.assertEqual(host,'api.crossref.org');self.assertEqual(path,'/works/10.1234/test.1')
            return lookup(host,path,**kw)
        r=verify(SPEC,approved=True,transport=transport)
        self.assertEqual(r['metadata_result'],'matches');self.assertTrue(r['doi_record_returned'])
        self.assertFalse(r['scientific_claim_support_verified']);self.assertFalse(r['full_text_read'])
        self.assertTrue(all(f['status']=='match' for f in r['comparison'].values()))
    def test_missing_and_mismatch(self):
        data=copy.deepcopy(DATA);del data['message']['author']
        self.assertEqual(compare(SPEC,data,b'{}')['metadata_result'],'incomplete')
        data['message']['issued']={'date-parts':[[2024]]}
        r=compare(SPEC,data,b'{}');self.assertEqual(r['metadata_result'],'differs')
        self.assertEqual(r['comparison']['first_author_family']['status'],'unavailable')
        data['message']['DOI']='10.1234/another'
        with self.assertRaises(ValueError):compare(SPEC,data,b'{}')
    def test_consent_and_path_validation(self):
        for doi in ('https://doi.org/10.1234/test','10.1234/../test','10.1234/test?x=1','10.1234/test%2f'):
            with self.assertRaises(ValueError):checked(dict(SPEC,doi=doi))
        with self.assertRaises(ValueError):verify(SPEC,transport=lambda *_:self.fail('network'))
    def test_review_publish_and_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'spec.json';p.write_text(json.dumps(SPEC))
            plan,_=review(root,'spec.json','citation.json')
            def fetch(s,approved):return verify(s,approved=approved,transport=lookup)
            r=execute(root,plan,lookup=fetch)
            self.assertEqual(r['metadata_result'],'matches')
            self.assertEqual(json.loads((root/'citation.json').read_text())['doi'],'10.1234/test.1')
            with self.assertRaises(ValueError):execute(root,plan,lookup=fetch)
            (root/'citation.json').unlink();p.write_text(json.dumps(dict(SPEC,year=2024)))
            with self.assertRaises(ValueError):execute(root,plan,lookup=fetch)
