import tempfile
import unittest
import json
from pathlib import Path
from deepthort_local.workflow_design import parse_draft,source_binding,current_source,current_source_file,WorkflowDrafts
from deepthort_local.conversation_workflow import ConversationStore

class WorkflowDesignTests(unittest.TestCase):
    def test_exact_inventory_and_dependencies(self):
        recipes=[dict(recipe_id=1,input_required=False,output='a.obj'),
                 dict(recipe_id=2,input_required=True,output='b.png')]
        stages=[dict(recipe_id=1,input=''),dict(recipe_id=2,input='a.obj')]
        self.assertEqual(parse_draft(json.dumps(dict(stages=stages,missing=[])),recipes,[])['stages'],stages)
        with self.assertRaises(ValueError):parse_draft(json.dumps(dict(stages=stages[::-1],missing=[])),recipes,[])
        with self.assertRaises(ValueError):parse_draft(json.dumps(dict(stages=[dict(recipe_id=999,input='')],missing=[])),recipes,[])
    def test_missing_is_not_a_complete_workflow(self):
        proposal={'stages':[],'missing':[{'capability':'mesh converter','goal':'Convert mesh','output':'mesh.obj'}]}
        self.assertEqual(parse_draft(json.dumps(proposal),[],[]),proposal)
        with self.assertRaises(ValueError):parse_draft('{"stages":[],"missing":[]}',[],[])
    def test_amendment_invalidates_binding_and_draft_persists(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);c=ConversationStore(p/'conversations.sqlite3')
            ident=c.submit('chat',t,'draft_plan','Build space game')
            binding=source_binding(c.get(ident))
            store=WorkflowDrafts(p/'workflows.sqlite3')
            store.queue(20,binding,'Generate mesh')
            self.assertEqual(WorkflowDrafts(store.path).latest(binding)['goal'],'Generate mesh')
            self.assertTrue(current_source(binding,c))
            c.change(ident,'running','testing')
            self.assertTrue(current_source_file(binding,c.path))
            self.assertEqual(c.get(ident)['state'],'running')
            c.amend_project('chat',t,'Use a different mesh')
            self.assertFalse(current_source(binding,c))
            self.assertFalse(current_source_file(binding,c.path))
    def test_visual_graph_exact_dependencies(self):
        from deepthort_local.workflow_graph import project_graph
        stages=[dict(recipe_id=1,tool='Blender',title='Mesh',input='',output='a.obj',predecessor=None),
                dict(recipe_id=2,tool='Image',title='Texture',input='',output='b.png',predecessor=None),
                dict(recipe_id=3,tool='Blender',title='Convert',input='a.obj',output='c.glb',predecessor=1)]
        manifest={'project':'project','stages':stages}
        graph=project_graph(manifest)
        self.assertEqual(graph['execution_order'],[1,2,3])
        self.assertEqual(graph['edges'],[{'from':1,'to':3,'artifact':'a.obj'}])
        self.assertNotIn('argv',graph['nodes'][0])
        old=graph['manifest_sha256'];stages[0]['title']='New title'
        self.assertNotEqual(old,project_graph(manifest)['manifest_sha256'])
        stages[2]['predecessor']=2
        with self.assertRaises(ValueError):project_graph(manifest)
        stages[2]['predecessor']=None
        with self.assertRaises(ValueError):project_graph(manifest)
if __name__=='__main__':unittest.main()
