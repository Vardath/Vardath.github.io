"""The approved dependency graph, not list order, selects real software work."""
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.requirements_intelligence import complete_dependencies,dependency_order
from deepthort_local.task_graph import TaskGraphStore,GraphError
from deepthort_local.project_authority import issue_grant,record_file
from deepthort_local.project_assignments import ProjectAssignments
from deepthort_local.project_assignment_probe import fixture_receipt

class ReadyTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.project=self.root/'project';self.project.mkdir()
        self.job={'id':1,'mode':'build','state':'queued','project':str(self.project),
                  'chat_id':'chat','approval_key':'draft:1','prompt':'Create a coherent working program'}
        self.steps=[{'id':i+1,'sequence':i,'path':p,'description':d,'state':'planned'} for i,(p,d) in enumerate([
            ('docs.md','Write standalone guide; depends-on: none'),
            ('engine.py','Implement shared engine; depends-on: none'),
            ('ui.py','Connect interface; depends-on: engine.py'),
            ('tests.py','Test engine behavior; depends-on: engine.py')])]
        self.graph=TaskGraphStore(self.root/'task-graph.sqlite3');self.store=ProjectAssignments(self.graph)
        self.grants=self.root/'grants'
    def start(self):
        issue_grant(self.grants,self.job,self.steps);self.graph.create(self.job,self.steps)
        self.job['state']='running'
    def save(self,step,text):
        (self.project/step['path']).write_text(text,encoding='utf-8')
        receipt=record_file(self.grants,self.job,self.steps,step,enabled=True)
        self.graph.record_artifact(self.job,self.steps,step,receipt['sha256'])
        step['state']='saved'
    def test_real_ready_work_not_original_list_order(self):
        self.start()
        self.assertTrue(self.graph.explicit(1))
        self.assertEqual(self.graph.ready_step(self.job,self.steps)['path'],'engine.py')
        self.assertIsNone(self.graph.ready_step(self.job,self.steps,preferred=3))
        self.assertEqual(self.graph.ready_step(self.job,self.steps,preferred=1)['path'],'docs.md')
        step=self.steps[1]
        attempt,contract=self.store.begin(self.job,self.steps,step,self.job['prompt'],[],self.grants,enabled=True)
        source='def tick(): return 1'
        for kind,proposal in [('plan',json.dumps({'path':step['path'],'description':step['description']},ensure_ascii=False)),('code',source)]:
            self.store.review(attempt,kind,proposal,fixture_receipt(self.job['prompt'],proposal))
        self.store.seal(attempt,source)
        self.assertEqual(self.store.target_step(attempt,1,self.steps),step)
        with self.assertRaises(GraphError):self.store.target_step(attempt,2,self.steps)
        self.save(step,source)
        self.assertEqual(self.graph.ready_step(self.job,self.steps,preferred=3)['path'],'ui.py')
        (self.project/'engine.py').write_text('changed',encoding='utf-8')
        self.assertIsNone(self.graph.ready_step(self.job,self.steps,preferred=3))
        self.assertEqual(self.graph.ready_step(self.job,self.steps)['path'],'docs.md')
    def test_legacy_incomplete_declarations_remain_ordered(self):
        self.steps[0]['description']='Write standalone guide'
        self.start()
        self.assertFalse(self.graph.explicit(1))
        self.assertEqual(self.graph.ready_step(self.job,self.steps)['path'],'docs.md')
        self.assertIsNone(self.graph.ready_step(self.job,self.steps,preferred=2))
    def test_tampered_dependency_graph_rejected(self):
        self.start()
        with self.graph._db() as db:
            db.execute("DELETE FROM edges WHERE job_id=1 AND node='file:3' AND depends_on='file:2'")
        with self.assertRaises(GraphError):self.graph.ready_step(self.job,self.steps)
    def test_explicit_none_is_not_a_phantom_file(self):
        mapping=complete_dependencies(self.steps)
        self.assertEqual(mapping['engine.py'],())
        self.assertEqual(mapping['ui.py'],('engine.py',))
        self.steps[0]['description']='Write guide; depends-on: none; depends-on: engine.py'
        with self.assertRaises(ValueError):dependency_order(self.steps)
    def test_cycle_does_not_create_graph(self):
        self.steps[1]['description']='Engine; depends-on: ui.py'
        with self.assertRaises(ValueError):self.start()
        self.assertFalse(self.graph.exists(1))
if __name__=='__main__':unittest.main()
