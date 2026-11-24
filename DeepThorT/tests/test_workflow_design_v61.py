import tempfile
import unittest
import json
from pathlib import Path
from deepthort_local.workflow_design import parse_draft,source_binding,current_source,WorkflowDrafts
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
            c.amend_project('chat',t,'Use a different mesh')
            self.assertFalse(current_source(binding,c))
if __name__=='__main__':unittest.main()
