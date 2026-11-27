import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from deepthort_local.infographic_generation import checked,generate,review,execute,SVG

def spec():
    return {'title':'Project snapshot','subtitle':'Supplied local figures','accent':'#1d697a',
            'source_note':'Source: user-provided figures; not independently verified.',
            'facts':[{'label':'Ships built','value':'120','detail':'Completed hulls in the specified period.'},
                     {'label':'Total deliveries','value':'456','detail':'Recorded deliveries across all sectors.'}]}
class InfographicTests(unittest.TestCase):
    def test_structure_and_values(self):
        out,r=generate(spec());root=ET.fromstring(out)
        self.assertEqual(root.tag,SVG+'svg')
        self.assertEqual([(n.get('data-card'),n.text) for n in root if n.get('data-role')=='value'],[('0','120'),('1','456')])
        self.assertEqual(r['facts'],2);self.assertFalse(r['source_claims_verified'])
    def test_odd_cards_and_literal_content(self):
        s=spec();s['facts'].append({'label':'A & B','value':'<tag>','detail':'Literal text, not SVG markup.'})
        out,r=generate(s);root=ET.fromstring(out)
        self.assertEqual(r['height'],678)
        self.assertEqual([n.text for n in root if n.get('data-role')=='value'][-1],'<tag>')
        self.assertEqual(len(list(root.iter(SVG+'tag'))),0)
    def test_bounds_and_invalid_fields(self):
        s=spec();s['facts'][0]['value']='x'*19
        with self.assertRaises(ValueError):checked(s)
        s=spec();s['facts']=[]
        with self.assertRaises(ValueError):checked(s)
        s=spec();s['accent']='url(https://example.com)'
        with self.assertRaises(ValueError):checked(s)
        s=spec();s['facts'][0]['detail']='x'*131
        with self.assertRaises(ValueError):checked(s)
    def test_review_stale_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'spec.json';p.write_text(json.dumps(spec()))
            plan,r=review(root,'spec.json','snapshot.svg');result=execute(root,plan)
            self.assertTrue(result['exact_layout_text_verified']);self.assertEqual(r['verification']['facts'],2)
            with self.assertRaises(ValueError):execute(root,plan)
            (root/'snapshot.svg').unlink();s=spec();s['title']='Changed';p.write_text(json.dumps(s))
            with self.assertRaises(ValueError):execute(root,plan)
