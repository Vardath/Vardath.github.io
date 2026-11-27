import copy
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.relationship_discovery import discover,review,execute

RAW=b'Granite implements code.\nJANUS coordinates Granite.\nJANUS reviews Granite.\nGemma creates art.\nJANUS and Gemma collaborate.\nGranites and Gemma are unrelated words.\n'
def node(ident,label,line,quote):
    return {'id':ident,'label':label,'kind':'worker','evidence':{'line':line,'start':0,'quote':quote}}
SPEC={'document':'source.txt','nodes':[node('granite','Granite',1,'Granite implements code.'),
    node('janus','JANUS',2,'JANUS coordinates Granite.'),node('gemma','Gemma',4,'Gemma creates art.')],
    'max_candidates':10}
class RelationshipTests(unittest.TestCase):
    def test_exact_cooccurrence_candidates(self):
        r=discover(SPEC,RAW)
        self.assertEqual([x['entities'] for x in r['candidates']],[['granite','janus'],['gemma','janus']])
        self.assertEqual(r['candidates'][0]['supporting_lines'],2)
        self.assertFalse(r['claims_verified']);self.assertIsNone(r['candidates'][0]['direction'])
        lines=RAW.decode().splitlines()
        for candidate in r['candidates']:
            for e in candidate['examples']:
                self.assertEqual(lines[e['line']-1][e['start']:e['start']+len(e['quote'])],e['quote'])
    def test_bounds_and_literal_word_matching(self):
        s=copy.deepcopy(SPEC);s['max_candidates']=1
        raw=RAW+b'JANUS '+b'x'*501+b' Gemma\n'+b'Granite '*130+b'Gemma\n'
        r=discover(s,raw)
        self.assertEqual(r['qualifying_pairs'],2)
        self.assertEqual(r['omitted_pairs'],1);self.assertEqual(r['skipped_dense_lines'],1)
        self.assertEqual(r['candidates'][0]['supporting_lines'],2)
    def test_review_publication_and_stale_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'source.txt').write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(SPEC),encoding='utf-8')
            plan,_=review(root,'spec.json','relationships.json')
            result=execute(root,plan)
            self.assertEqual(result['candidates'],2)
            self.assertEqual(json.loads((root/'relationships.json').read_text()),discover(SPEC,RAW))
            plan,_=review(root,'spec.json','later.json')
            (root/'source.txt').write_bytes(RAW+b'Changed.')
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'later.json').exists())
if __name__=='__main__':unittest.main()
