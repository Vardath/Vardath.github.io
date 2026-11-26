"""V43 regression: host-owned project role assignments, no new execution authority."""
import difflib
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.task_graph import TaskGraphStore,GraphError
from deepthort_local.project_assignments import ProjectAssignments,ProjectRoleClient,sha
from deepthort_local.project_authority import issue_grant,record_file,revoke_grant,GrantError
from deepthort_local.project_assignment_probe import fixture_receipt,exercise
from deepthort_local.delegation_senses import observe_project_assignments

class ProjectRoleTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.project=self.root/'fixture';self.project.mkdir()
        self.original='Create a working example'
        self.job={'id':13,'mode':'build','state':'queued','project':str(self.project),
                  'chat_id':'t','approval_key':'draft:44','prompt':self.original}
        self.steps=[{'id':101,'sequence':0,'path':'main.py','description':'Main source','state':'planned'},
                    {'id':102,'sequence':1,'path':'test_main.py','description':'Test code','state':'planned'}]
        self.old='def answer():\n    return 1\n'
        (self.project/'main.py').write_bytes(self.old.encode())
        self.graph=TaskGraphStore(self.root/'task-graph.sqlite3')
        self.store=ProjectAssignments(self.graph);self.grants=self.root/'grants'
        issue_grant(self.grants,self.job,self.steps);self.graph.create(self.job,self.steps)
        self.job['state']='running'
    def begin(self,index=0):
        step=self.steps[index]
        return self.store.begin(self.job,self.steps,step,self.original,[],self.grants,enabled=True)
    def review(self,attempt,kind,proposal):
        self.store.review(attempt,kind,proposal,fixture_receipt(self.original,proposal))
    def plan(self,attempt,index=0):
        step=self.steps[index]
        self.review(attempt,'plan',json.dumps({'path':step['path'],'description':step['description']},ensure_ascii=False))
    def validate(self,attempt,source,amendments=()):
        return self.store.validate(attempt,self.job,self.steps,self.steps[0],self.original,amendments,self.grants,source,enabled=True)
    def test_real_host_probe(self):
        result=exercise();self.assertEqual(result['status'],'passed',result)
    def test_requires_ready_dependencies_and_exact_plan(self):
        with self.assertRaises(GraphError):self.begin(1)
        attempt,contract=self.begin()
        self.review(attempt,'code','print(2)')
        self.review(attempt,'plan','Unrelated plan')
        with self.assertRaises(GraphError):self.store.seal(attempt,'print(2)')
        self.plan(attempt);self.store.seal(attempt,'print(2)')
        self.assertEqual(self.validate(attempt,'print(2)'),contract)
    def test_scope_change_candidate_change_revocation(self):
        attempt,_=self.begin();self.plan(attempt)
        source='print(2)';self.review(attempt,'code',source);self.store.seal(attempt,source)
        with self.assertRaises(GraphError):self.validate(attempt,'print(3)')
        with self.assertRaises(GraphError):self.validate(attempt,source,['Changed requirement'])
        (self.project/'main.py').write_bytes(b'changed')
        with self.assertRaises(GrantError):self.validate(attempt,source)
        (self.project/'main.py').write_bytes(self.old.encode())
        revoke_grant(self.grants,self.job['id'])
        with self.assertRaises(GrantError):self.validate(attempt,source)
    def test_review_cannot_certify_runtime_or_wrong_source(self):
        attempt,_=self.begin();r=fixture_receipt(self.original,'print(2)')
        with self.assertRaises(GraphError):self.store.review(attempt,'code','print(3)',r)
        r['verified']=True
        with self.assertRaises(GraphError):self.store.review(attempt,'code','print(2)',r)
    def test_exact_reviewed_range_assembly(self):
        attempt,_=self.begin();self.plan(attempt)
        replacement='def answer():\n    return 2\n'
        action='Update answer'
        delta=''.join(difflib.unified_diff(self.old.splitlines(keepends=True),replacement.splitlines(keepends=True),fromfile='before',tofile='after',n=2))
        self.review(attempt,'plan','Change only source range 1: '+action)
        self.review(attempt,'code',f'Exact source range 1, action: {action}\n{delta}')
        staged={'before_sha256':sha(self.old),'master_sha256':sha(self.original),'step_id':101,
                'after_sha256':sha(replacement),'changed_ranges':1,'range_receipts':[
                    {'start':0,'end':len(self.old),'length':len(replacement),'action':action}]}
        changed=replacement.replace('2','3')
        with self.assertRaises(GraphError):self.store.seal(attempt,changed,staged=dict(staged,after_sha256=sha(changed)))
        self.store.seal(attempt,replacement,staged=staged)
        self.assertEqual(self.store.summary(13)[0]['review_mode'],'reviewed_deltas')
    def test_abandon_and_uncertain_write_not_replayed(self):
        attempt,_=self.begin();self.plan(attempt)
        source='print(2)';self.review(attempt,'code',source);self.store.seal(attempt,source)
        self.assertEqual(self.store.recover(),[])
        with self.assertRaises(GraphError):self.validate(attempt,source)
        second,_=self.begin();self.plan(second);self.review(second,'code',source);self.store.seal(second,source)
        with self.assertRaises(GraphError):
            self.store.commit(second,self.job,self.steps,self.steps[0],self.original,[],self.grants,source,'absent',enabled=True)
        lease=self.graph.begin_action(self.job,self.steps,'write','file:101')
        self.store.commit(second,self.job,self.steps,self.steps[0],self.original,[],self.grants,source,lease,enabled=True)
        self.assertEqual(ProjectAssignments(self.graph).recover(),[13])
        with self.assertRaises(GraphError):self.begin()
    def test_scoped_explicit_role_cache_and_observation(self):
        attempt,contract=self.begin()
        class Client:
            def __init__(self):self.calls=[]
            def chat_as(self,role,session,prompt,max_tokens):
                self.calls.append((role,session,prompt));return 'answer'
            def completed_exchange(self,session,prompt):
                return 'answer' if any(s==session and p==prompt for _,s,p in self.calls) else None
        client=Client();scoped=ProjectRoleClient(client,contract)
        self.assertEqual(scoped.chat('same','exact'),'answer')
        self.assertEqual(client.calls[0][0],'implementation')
        self.assertEqual(scoped.completed_exchange('same','exact'),'answer')
        self.assertIsNone(ProjectRoleClient(client,dict(contract,original_sha256='changed')).completed_exchange('same','exact'))
        snap=observe_project_assignments(self.root/'jobs.sqlite3')
        self.assertEqual(snap['active'][0]['assignee'],'implementation')
        self.assertNotIn(self.original,json.dumps(snap))
        self.assertNotIn(str(self.project),json.dumps(snap))

if __name__=='__main__':unittest.main()
