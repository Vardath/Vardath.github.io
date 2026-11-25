import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.portable_skills_probe import exercise,Fixture
from deepthort_local.workflow_skills import PortableSkills,rebind,validate_portable
from deepthort_local.janus_engine import JanusStore

class PortableSkillTests(unittest.TestCase):
    def test_probe(self):
        result=exercise()
        self.assertEqual(result['status'],'passed',result)
    def test_invalid_and_ambiguous_bindings(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            lib=PortableSkills(JanusStore(root/'janus.db'))
            fixture=Fixture(root)
            skill=lib.publish(fixture,fixture.run,root,user_approved=True)
            bad=json.loads(json.dumps(skill));bad['stages'][0]['argv']=['not permitted']
            with self.assertRaises(ValueError):validate_portable(bad)
            bad=json.loads(json.dumps(skill));bad['stages'][1]['from_stage']=2
            with self.assertRaises(ValueError):validate_portable(bad)
            recipes=[{'recipe_id':1,'tool':'Blender','input_required':True,'output':'a.glb'},
                {'recipe_id':2,'tool':'Blender','input_required':True,'output':'b.glb'},
                {'recipe_id':3,'tool':'Godot','input_required':True,'output':'out.zip'}]
            self.assertIsNone(rebind(skill,recipes,['input.obj']))
            self.assertIsNone(rebind(skill,recipes[1:],['input.txt']))
            self.assertIsNone(rebind(skill,recipes[1:],['input.obj','b.glb']))
            with self.assertRaises(PermissionError):lib.remove(skill['version'])
            with self.assertRaises(ValueError):lib.publish(fixture,dict(fixture.run,state='blocked'),root,user_approved=True)
