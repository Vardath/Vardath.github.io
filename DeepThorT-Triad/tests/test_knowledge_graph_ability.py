import copy
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.knowledge_graph import build,review,execute

RAW=b'Granite implements source code.\nJANUS coordinates Granite.\n'
def loc(line,quote):return {'line':line,'start':0,'quote':quote}
SPEC={'document':'source.txt','nodes':[
    {'id':'granite','label':'Granite','kind':'worker','evidence':loc(1,'Granite implements source code.')},
    {'id':'janus','label':'JANUS','kind':'worker','evidence':loc(2,'JANUS coordinates Granite.')}],
    'edges':[{'from':'janus','to':'granite','predicate':'coordinates','evidence':loc(2,'JANUS coordinates Granite.')}]}
class GraphTests(unittest.TestCase):
    def test_graph_and_adjacency(self):
        g=build(SPEC,RAW)
        self.assertEqual(g['adjacency']['janus']['outgoing'],['e1'])
        self.assertEqual(g['adjacency']['granite']['incoming'],['e1'])
        self.assertEqual(g['edges'][0]['status'],'reviewed_assertion_not_verified')
        self.assertFalse(g['claims_verified']);self.assertFalse(g['authority'])
    def test_bad_evidence_and_dangling_edge(self):
        for field,value in [('line',1),('start',1),('quote','Invented')]:
            s=copy.deepcopy(SPEC);s['edges'][0]['evidence'][field]=value
            with self.assertRaises(ValueError):build(s,RAW)
        s=copy.deepcopy(SPEC);s['edges'][0]['to']='missing'
        with self.assertRaises(ValueError):build(s,RAW)
        s=copy.deepcopy(SPEC);s['edges'].append(s['edges'][0])
        with self.assertRaises(ValueError):build(s,RAW)
    def test_review_publication_and_stale_source(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'source.txt').write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(SPEC),encoding='utf-8')
            plan,preview=review(root,'spec.json','graph.json')
            result=execute(root,plan)
            self.assertEqual(result['edges'],1)
            self.assertEqual(json.loads((root/'graph.json').read_text()),preview)
            plan,_=review(root,'spec.json','later.json')
            (root/'source.txt').write_bytes(RAW+b'Changed.')
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'later.json').exists())
if __name__=='__main__':unittest.main()
