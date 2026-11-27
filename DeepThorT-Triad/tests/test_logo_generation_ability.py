import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from deepthort_local.logo_generation import checked,generate,review,execute,SVG

def spec():
    return {'title':'Example & Co','width':320,'height':160,'background':None,'elements':[
        {'kind':'circle','cx':40,'cy':80,'radius':24,'fill':'#005577'},
        {'kind':'polygon','points':[[30,80],[40,65],[50,80]],'fill':'#ffffff'},
        {'kind':'rect','x':80,'y':115,'width':200,'height':4,'radius':2,'fill':'#005577'},
        {'kind':'text','x':80,'y':90,'text':'Example & Co','size':24,'family':'sans','weight':'bold','anchor':'start','fill':'#101010'}]}
class LogoTests(unittest.TestCase):
    def test_editable_elements(self):
        out,r=generate(spec());root=ET.fromstring(out)
        self.assertEqual([n.tag for n in root],[SVG+x for x in ('title','circle','polygon','rect','text')])
        self.assertEqual(root[-1].text,'Example & Co');self.assertEqual(root[-1].get('font-size'),'24')
        self.assertTrue(r['transparent_background']);self.assertFalse(r['visual_render_verified'])
    def test_literal_text_and_background(self):
        s=spec();s['background']='#ffffff';s['elements'][-1]['text']='<script>alert(1)</script>'
        out,r=generate(s);root=ET.fromstring(out)
        self.assertEqual(root[1].tag,SVG+'rect');self.assertEqual(root[-1].text,s['elements'][-1]['text'])
        self.assertEqual(list(root[-1]),[]);self.assertFalse(r['trademark_clearance_verified'])
    def test_reject_unsafe_geometry_and_fields(self):
        s=spec();s['elements'][0]['fill']='url(https://example.com)'
        with self.assertRaises(ValueError):checked(s)
        s=spec();s['elements'][0]['radius']=100
        with self.assertRaises(ValueError):checked(s)
        s=spec();s['elements'][1]['points']=[[1,1],[2,2],[3,3]]
        with self.assertRaises(ValueError):checked(s)
        s=spec();s['elements'][3]['onclick']='alert(1)'
        with self.assertRaises(ValueError):checked(s)
    def test_publish_and_stale_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'spec.json';p.write_text(json.dumps(spec()))
            plan,r=review(root,'spec.json','brand.svg');result=execute(root,plan)
            self.assertEqual(r['verification']['elements'],4);self.assertTrue(result['geometry_verified'])
            with self.assertRaises(ValueError):execute(root,plan)
            (root/'brand.svg').unlink();s=spec();s['title']='Changed';p.write_text(json.dumps(s))
            with self.assertRaises(ValueError):execute(root,plan)
