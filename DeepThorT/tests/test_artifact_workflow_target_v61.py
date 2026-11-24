import tempfile
import unittest
import json
from pathlib import Path
from deepthort_local.artifact_types import artifact_type
from deepthort_local.workflow_design import inventory,check_required_proposal

class Acquisition:
    def recipes(self,root):
        for i in range(20):
            yield dict(id=i+1,name='tool',title='Generate texture',purpose='Generate texture',
                       args_json=json.dumps(['{{output}}']),artifact=f'other{i}.png',status='candidate')
        yield dict(id=99,name='tool',title='Convert',purpose='Export native model',
                   args_json=json.dumps(['{{output}}']),artifact='target.glb',status='candidate')
    def script_needs_review(self,*args):return False
    def _build_recipe_command(self,*args,**kwargs):return ['tool']

class ArtifactWorkflowTargetTests(unittest.TestCase):
    def test_exact_output_is_visible_despite_inventory_limit(self):
        with tempfile.TemporaryDirectory() as t:
            recipes,_=inventory(Acquisition(),t,'Generate texture',required_output='target.glb')
            self.assertEqual(recipes[0]['recipe_id'],99)
            self.assertLessEqual(len(recipes),12)
            ordinary,_=inventory(Acquisition(),t,'Generate texture')
            self.assertNotIn(99,[r['recipe_id'] for r in ordinary])

    def test_missing_target_cannot_be_silently_replaced(self):
        with tempfile.TemporaryDirectory() as t:
            task={'output':'target.glb','artifact_type':artifact_type('target.glb')}
            gap=lambda output:dict(capability='converter',goal='Export mesh',output=output)
            proposal=lambda *gaps:dict(stages=[],missing=list(gaps))
            self.assertTrue(check_required_proposal(t,task,proposal(gap('target.glb')),[]))
            for gaps in ((gap('wrong.glb'),),(gap('../target.glb'),),(gap('target.glb'),gap('TARGET.GLB'))):
                with self.assertRaises(ValueError):
                    check_required_proposal(t,task,proposal(*gaps),[])
            Path(t,'intermediate.obj').write_text('existing')
            with self.assertRaises(ValueError):
                check_required_proposal(t,task,proposal(gap('target.glb'),gap('intermediate.obj')),[])

    def test_known_recipe_exact_output_and_missing_collision(self):
        with tempfile.TemporaryDirectory() as t:
            task={'output':'target.glb','artifact_type':artifact_type('target.glb')}
            recipes=[dict(recipe_id=99,output='target.glb')]
            proposal=dict(stages=[dict(recipe_id=99,input='')],missing=[])
            self.assertTrue(check_required_proposal(t,task,proposal,recipes))
            proposal['missing']=[dict(capability='tool',goal='Export',output='TARGET.GLB')]
            with self.assertRaises(ValueError):
                check_required_proposal(t,task,proposal,recipes)
            with self.assertRaises(ValueError):
                check_required_proposal(t,dict(task,artifact_type=artifact_type('target.png')),
                                        dict(stages=[],missing=[]),recipes)

if __name__=='__main__':unittest.main()
