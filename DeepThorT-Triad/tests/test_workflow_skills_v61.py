import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from deepthort_local.tool_workflows import digest
from deepthort_local.workflow_skills import checked_skill, skill_hints


class WorkflowSkillTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve()
        self.stages=[
            {'tool':'Blender','input':'private/input.obj','output':'private/mesh.glb','predecessor':None,
             'argv':['never replay this'],'recipe_id':81},
            {'tool':'Godot','input':'private/mesh.glb','output':'private/export.zip','predecessor':1,
             'argv':['never replay this'],'recipe_id':82}]
        manifest={'project':str(self.root),'stages':self.stages}
        self.run={'id':7,'project':str(self.root),'state':'complete',
                  'manifest':json.dumps(manifest),'manifest_sha':digest(manifest)}
        self.workflows=Mock()
        self.workflows.list.return_value=[self.run]
        self.workflows.stages.return_value=[{'workflow_id':7,'ordinal':i,'state':'checked'} for i in (1,2)]
        self.workflows._check_receipt.return_value={'artifact':{'scope':'structure checked','sha256':'a'*64}}
        self.recipes=[{'tool':'Blender','output':'new.glb','input_required':True},
                      {'tool':'Godot','output':'new.zip','input_required':True}]

    def test_shape_contains_types_but_no_old_authority(self):
        skill=checked_skill(self.workflows,self.run,self.root)
        self.assertEqual(skill['stages'][1]['from_stage'],1)
        self.assertEqual(skill['stages'][0]['input_format'],'obj')
        self.assertNotIn('private',str(skill))
        self.assertNotIn('argv',str(skill))
        self.assertNotIn('recipe_id',str(skill))
        self.assertEqual(len(skill['version']),64)

    def test_compatible_current_inventory_only(self):
        hint=skill_hints(self.workflows,self.root,self.recipes,['current.obj'],required_output='new.zip')
        self.assertIn('Blender',hint)
        self.assertIn('not recipes or approval',hint)
        self.assertNotIn('private',hint)
        self.assertFalse(skill_hints(self.workflows,self.root,self.recipes,[]))
        self.assertFalse(skill_hints(self.workflows,self.root,self.recipes[:1],['current.obj']))
        self.assertFalse(skill_hints(self.workflows,self.root,self.recipes,['current.obj'],required_output='new.apk'))

    def test_unchecked_and_changed_evidence_refused(self):
        for state in ('active','blocked'):
            with self.assertRaises(ValueError):
                checked_skill(self.workflows,dict(self.run,state=state),self.root)
        self.workflows._check_receipt.side_effect=ValueError('changed output')
        self.assertFalse(skill_hints(self.workflows,self.root,self.recipes,['current.obj']))

    def test_no_cross_project_or_manifest_mutation(self):
        with self.assertRaises(ValueError):
            checked_skill(self.workflows,dict(self.run,project=str(self.root/'other')),self.root)
        with self.assertRaises(ValueError):
            checked_skill(self.workflows,dict(self.run,manifest='{}'),self.root)

    def test_version_changes_with_receipts(self):
        a=checked_skill(self.workflows,self.run,self.root)['version']
        self.workflows._check_receipt.return_value={'artifact':{'scope':'structure checked','sha256':'b'*64}}
        b=checked_skill(self.workflows,self.run,self.root)['version']
        self.assertNotEqual(a,b)

    def test_existence_only_or_cancelled_not_promoted(self):
        self.workflows._check_receipt.return_value={'artifact':{'scope':'nonempty bytes only'}}
        self.assertFalse(skill_hints(self.workflows,self.root,self.recipes,['current.obj']))
        self.assertFalse(skill_hints(self.workflows,self.root,self.recipes,['current.obj'],cancelled=lambda:True))
