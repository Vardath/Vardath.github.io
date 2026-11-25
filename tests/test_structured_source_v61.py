import unittest
import json
import tomllib
import xml.etree.ElementTree as ET
from deepthort_local.structured_source import stage_new_document,assemble,_envelope,strict_json
from deepthort_local.staged_source import StageError,sha

class Council:
    def __init__(self,answer):self.answer=answer
    def _run(self,client,**kw):return json.dumps(self.answer)

class Model:
    def __init__(self,answers):self.answers=iter(answers);self.prompts=[]
    def chat(self,session,prompt,max_tokens):
        self.prompts.append(prompt)
        return next(self.answers)

class StructuredSourceTests(unittest.TestCase):
    def generate(self,path,plan,answers):
        model=Model(answers)
        reviews=[]
        result=stage_new_document(model,Council(plan),model,session='build',path=path,
              goal='Implement two required sections',scope='Exact project requirements.',
              master_sha=sha('master'),review=lambda p,k:reviews.append(k))
        self.assertEqual(reviews,['plan','code','code','code'])
        self.assertEqual(result['after_sha256'],sha(result['source']))
        return result['source'],model

    def test_xml_preserves_root_and_namespaces(self):
        source,_=self.generate('ship.xml',
            {'envelope':'<macros xmlns:x="urn:test"><!--DEEPTHORT_UNITS--></macros>',
             'units':['Define first macro','Define second macro']},
            ['<x:macro name="one"/>','<x:macro name="two"/>'])
        root=ET.fromstring(source)
        self.assertEqual(root.tag,'macros')
        self.assertEqual([x.tag for x in root],['{urn:test}macro']*2)

    def test_json_retries_duplicate_and_retains_keys(self):
        source,m=self.generate('game.json',{'root':'object','units':['Define sectors','Define mining']},
                   ['{"sectors":200}','{"sectors":100}','{"mining":true}'])
        self.assertEqual(json.loads(source),{'sectors':200,'mining':True})
        self.assertIn('redefines earlier',m.prompts[-1])

    def test_toml_complete_tables(self):
        source,_=self.generate('game.toml',{'units':['Define project','Define economy']},
                   ['[project]\nname="space"','[economy]\nmining=true'])
        self.assertTrue(tomllib.loads(source)['economy']['mining'])

    def test_toml_key_scope_cannot_change_silently(self):
        with self.assertRaisesRegex(StageError,'key scope'):
            assemble('.toml',None,['[economy]\nmining=true','sectors=200'])
        source,_=assemble('.toml',None,['sectors=200','[economy]\nmining=true'])
        self.assertEqual(tomllib.loads(source),{'sectors':200,'economy':{'mining':True}})

    def test_reject_invalid_envelope_and_duplicate_keys(self):
        with self.assertRaises(StageError):_envelope('<!DOCTYPE root [<!ENTITY x "abc">]><root><!--DEEPTHORT_UNITS--></root>')
        with self.assertRaises(StageError):_envelope('<root><nested><!--DEEPTHORT_UNITS--></nested></root>')
        with self.assertRaises(StageError):strict_json('{"a":{"b":1,"b":2}}')
        with self.assertRaises(StageError):strict_json('{"x":NaN}')
        with self.assertRaises(StageError):
            assemble('.xml',_envelope('<root><!--DEEPTHORT_UNITS--></root>'),['<a/>','<a/>'])

if __name__=='__main__':unittest.main()
