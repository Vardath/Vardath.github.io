import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.janus_engine import JanusStore
from deepthort_local.portable_skills_probe import Fixture
from deepthort_local.workflow_skills import (PortableSkills, TEMPLATE_SCHEMA, preview_template,
    read_template, export_template, rebind, portable_hints)

class WorkflowTemplateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.lib=PortableSkills(JanusStore(self.root/'janus.db'))
        fixture=Fixture(self.root)
        self.skill=self.lib.publish(fixture,fixture.run,self.root,user_approved=True)
        self.path=self.root/'template.json'
        export_template(self.path,self.skill)
        self.recipes=[{'recipe_id':21,'tool':'Blender','input_required':True,'output':'mesh.glb'},
                      {'recipe_id':22,'tool':'Godot','input_required':True,'output':'out.zip'}]

    def test_roundtrip_and_provenance(self):
        raw=self.path.read_bytes()
        self.assertNotIn(b'old/',raw)
        self.assertNotIn(b'source_version',raw)
        template=read_template(self.path)
        self.assertEqual(template['schema'],TEMPLATE_SCHEMA)
        self.assertNotEqual(template['version'],self.skill['version'])
        with self.assertRaises(PermissionError):
            self.lib.import_template(template,expected_version=template['version'])
        with self.assertRaises(ValueError):
            self.lib.import_template(template,expected_version='0'*64,user_approved=True)
        self.lib.import_template(template,expected_version=template['version'],user_approved=True)
        self.lib.import_template(template,expected_version=template['version'],user_approved=True)
        reopened=PortableSkills(JanusStore(self.root/'janus.db'))
        self.assertEqual(len(reopened.list()),2)
        self.assertIn(template,reopened.list())
        reopened.remove(self.skill['version'],user_approved=True)
        self.assertIn('unverified template',portable_hints(reopened,self.recipes,['input.obj'],max_chars=1800))
        self.assertEqual(rebind(template,self.recipes,['input.obj'])['stages'][1]['input'],'mesh.glb')
        self.assertIsNone(rebind(template,self.recipes,['input.obj','other.obj']))

    def test_refuse_untrusted_fields_and_invalid_graph(self):
        body=json.loads(self.path.read_bytes())
        for field in ('argv','path','source_version','approval'):
            invalid=dict(body,**{field:'unsafe'})
            with self.assertRaises(ValueError):preview_template(json.dumps(invalid).encode())
        body['stages'][0]['from_stage']=2
        with self.assertRaises(ValueError):preview_template(json.dumps(body).encode())
        with self.assertRaises(ValueError):preview_template(b'x'*12001)
        with self.assertRaises(ValueError):preview_template(b'{"schema":"deepthort-workflow-template-v1","schema":"deepthort-workflow-template-v1","stages":[]}')

    def test_never_overwrite_export(self):
        original=self.path.read_bytes()
        with self.assertRaises(FileExistsError):export_template(self.path,self.skill)
        self.assertEqual(self.path.read_bytes(),original)

if __name__=='__main__':
    unittest.main()
