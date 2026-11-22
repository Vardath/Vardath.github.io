"""v42 evidence-backed graph, leases, blocked prerequisites and crash recovery."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

from deepthort_local.task_graph import TaskGraphStore, GraphError
from deepthort_local.project_authority import issue_grant,authorize_file,record_file
from deepthort_local.workspace import apply_approved_file

class GraphTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.project=self.root/'game';self.project.mkdir()
        self.job={'id':13,'mode':'build','state':'queued','project':str(self.project),
                  'chat_id':'t','approval_key':'draft:44','prompt':'Create game'}
        self.steps=[{'id':101,'sequence':0,'path':'main.py','description':'Main source','state':'planned'},
                    {'id':102,'sequence':1,'path':'test_main.py','description':'Test code','state':'planned'}]
        self.store=TaskGraphStore(self.root/'state'/'graph.db')
        self.grants=self.root/'grants';self.backups=self.root/'backups'
        issue_grant(self.grants,self.job,self.steps)
        self.store.create(self.job,self.steps)
        self.cmd=[sys.executable,'-m','unittest','discover']

    def save(self,idx,contents):
        step=self.steps[idx]
        self.job['state']='running'
        allowed=authorize_file(self.grants,self.job,self.steps,step,enabled=True)
        apply_approved_file(self.project,step['path'],contents,self.backups,
                            expected_existing_sha=allowed['before_sha256'])
        receipt=record_file(self.grants,self.job,self.steps,step,enabled=True)
        self.store.record_artifact(self.job,self.steps,step,receipt['sha256'])
        step['state']='saved'
        self.job['state']='queued'
        return receipt['sha256']

    def test_nodes_and_edges_from_exact_approved_steps(self):
        snap=self.store.status(13)
        self.assertEqual(snap['state'],'active')
        self.assertEqual(len(snap['nodes']),6)
        self.assertIn({'node':'file:102','depends_on':'file:101'},snap['edges'])
        self.assertIn({'node':'verify','depends_on':'file:102'},snap['edges'])
        self.assertEqual(snap['nodes'][0]['state'],'approved')

    def test_out_of_order_artifact_is_blocked(self):
        target=self.project/'test_main.py';target.write_text('one\n')
        with self.assertRaisesRegex(GraphError,'Waiting for prerequisites'):
            self.store.record_artifact(self.job,self.steps,self.steps[1],
                                       hashlib.sha256(target.read_bytes()).hexdigest())

    def test_test_requires_all_saved_source_and_observed_tool(self):
        self.save(0,'def add(a,b):return a+b\n')
        self.job['state']='waiting_verification'
        with self.assertRaisesRegex(GraphError,'Waiting for prerequisites'):
            self.store.ready_to_test(self.job,self.steps,self.cmd)
        self.job['state']='queued';self.save(1,'def test_add():return True\n')
        self.job['state']='waiting_verification'
        self.assertTrue(self.store.ready_to_test(self.job,self.steps,self.cmd))
        self.assertEqual(next(x for x in self.store.status(13)['nodes'] if x['node']=='tool:verify')['state'],'available')

    def test_success_requires_actual_evidence(self):
        self.save(0,'print(1)\n');self.save(1,'print(2)\n')
        self.job['state']='waiting_verification'
        self.store.ready_to_test(self.job,self.steps,self.cmd)
        lease=self.store.begin_action(self.job,self.steps,'test','verify')
        with self.assertRaises(GraphError):self.store.begin_action(self.job,self.steps,'test','verify')
        self.store.finish_action(lease,13,'passed')
        with self.assertRaises(GraphError):self.store.test_finished(self.job,self.steps,True,None)
        self.store.test_finished(self.job,self.steps,True,{'verified':True,'command':self.cmd})
        assert_states={x['node']:x['state'] for x in self.store.status(13)['nodes']}
        self.assertEqual(assert_states['verify'],'passed')
        self.assertEqual(assert_states['evidence'],'recorded')

    def test_missing_or_edited_tool_blocks(self):
        self.save(0,'print(1)\n');self.save(1,'print(2)\n')
        self.job['state']='waiting_verification'
        with self.assertRaises(GraphError):self.store.ready_to_test(self.job,self.steps,['madeup-tool','-x'])
        self.assertTrue(self.store.ready_to_test(self.job,self.steps,self.cmd))
        (self.project/'main.py').write_text('external modification')
        with self.assertRaisesRegex(GraphError,'changed'):
            self.store.ready_to_test(self.job,self.steps,self.cmd)

    def test_repair_needs_retest_and_updates_accepted_hash(self):
        self.save(0,'print(1)\n');self.save(1,'print(2)\n')
        self.job['state']='waiting_verification';self.store.ready_to_test(self.job,self.steps,self.cmd)
        self.store.test_finished(self.job,self.steps,False)
        (self.project/'main.py').write_text('print(3)\n')
        self.store.record_repaired_artifact(self.job,self.steps,self.steps[0],
            hashlib.sha256((self.project/'main.py').read_bytes()).hexdigest())
        current={x['node']:x['state'] for x in self.store.status(13)['nodes']}
        self.assertEqual(current['verify'],'waiting')
        self.assertEqual(current['evidence'],'waiting')
        self.assertTrue(self.store.ready_to_test(self.job,self.steps,self.cmd))

    def test_restart_interrupts_lease_without_replay(self):
        lease=self.store.begin_action(self.job,self.steps,'write','file:101')
        reloaded=TaskGraphStore(self.root/'state'/'graph.db')
        self.assertEqual(reloaded.interrupted(),[13])
        state=reloaded.status(13)
        self.assertEqual(next(x for x in state['nodes'] if x['node']=='file:101')['state'],'needs_attention')
        with self.assertRaises(GraphError):reloaded.finish_action(lease,13,'saved')

    def test_approval_is_not_derived_from_model_or_changed_plan(self):
        other=dict(self.job, approval_key=None,id=99)
        with self.assertRaises(GraphError):self.store.create(other,self.steps)
        self.job['prompt']='Changed request'
        with self.assertRaises(GraphError):self.store.begin_action(self.job,self.steps,'write','file:101')

    def test_hierarchical_requirements_are_exact_source_links_not_completion(self):
        from deepthort_local.hierarchical_planning import HierarchicalPlanStore
        h=HierarchicalPlanStore(self.root/'state'/'hierarchy.db')
        source='Remember an archive of every faction; test the archive.'
        source_sha=hashlib.sha256(source.encode()).hexdigest()
        with h._db() as db:
            db.execute('INSERT INTO hierarchy_roots(request_id,chat_id,project,source_sha256,'
                'model_steps_sha256,section_count,milestone_count) VALUES(?,?,?,?,?,?,?)',
                (14,'t',str(self.project),source_sha,'0'*64,1,1))
            db.execute('INSERT INTO hierarchy_requirements(request_id,requirement_id,section_ordinal,'
                'start_char,end_char,source_sha256,kind) VALUES(?,?,?,?,?,?,?)',
                (14,'archive-req',0,0,len(source),source_sha,'requirement'))
            db.execute('INSERT INTO hierarchy_trace(request_id,section_ordinal,section_sha256,path,'
                'milestone_ordinal) VALUES(?,?,?,?,?)',(14,0,source_sha,'main.py',1))
            db.execute('INSERT INTO hierarchy_dependencies(request_id,file_path,requires_path) '
                       'VALUES(?,?,?)',(14,'test_main.py','main.py'))
        refs=h.graph_provenance(14,['main.py','test_main.py'])
        self.assertEqual(refs['total_linked_requirements'],1)
        self.assertEqual(refs['root_source_sha256'],source_sha)
        self.store.attach_hierarchy(self.job,self.steps,refs)
        info=self.store.status(13)
        reqs=[x for x in info['nodes'] if x['kind']=='requirement' and x['node'].startswith('req:')]
        self.assertEqual(len(reqs),1)
        self.assertEqual(reqs[0]['state'],'linked')
        self.assertIn('not implementation',reqs[0]['note'])
        self.assertIn({'node':'file:101','depends_on':reqs[0]['node']},info['edges'])
        self.save(0,'print(1)\n')
        self.save(1,'print(2)\n')

    def test_later_declared_dependency_is_not_silently_reordered(self):
        data={'root_project':str(self.project),'requirements':[],
              'declared_file_dependencies':[{'file_path':'main.py','requires_path':'test_main.py'}]}
        with self.assertRaisesRegex(GraphError,'later'):
            self.store.attach_hierarchy(self.job,self.steps,data)

    def test_invalidation_is_persistent(self):
        self.assertTrue(self.store.invalidate(13,'User selected older source checkpoint'))
        self.assertTrue(self.store.invalidate(13,'repeat'))
        with self.assertRaises(GraphError):self.store.begin_action(self.job,self.steps,'write','file:101')
        self.assertEqual(TaskGraphStore(self.root/'state'/'graph.db').status(13)['state'],'invalidated')

if __name__=='__main__':unittest.main()
