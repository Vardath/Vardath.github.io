"""Proactive dependency handoffs use real graph, grant and creative ledgers."""
import json
import unittest
from deepthort_local.project_assignments import ProjectAssignments,ProjectRoleClient
from deepthort_local.task_graph import TaskGraphStore,GraphError
from deepthort_local.project_authority import issue_grant,record_file
from deepthort_local.project_assignment_probe import fixture_receipt
from deepthort_local.creative_core import midi
import test_project_assignments_v43 as software
import test_project_midi_v45 as media

class HandoffTests(unittest.TestCase):
    def test_proactive_exact_dependency_does_not_spend_recovery(self):
        f=software.ProjectRoleTests();f.setUp();self.addCleanup(f.doCleanups)
        first=f.steps[0]
        proof=record_file(f.grants,f.job,f.steps,first,enabled=True)
        f.graph.record_artifact(f.job,f.steps,first,proof['sha256'])
        first['state']='saved'
        attempt,contract=f.begin(1)
        args=(attempt,f.job,f.steps,f.steps[1],f.original,[],f.grants,1200)
        text=f.store.proactive_source_context(*args,enabled=True)
        self.assertIn(f.old,text);self.assertIn(proof['sha256'],text)
        self.assertEqual(f.store.proactive_source_context(*args,enabled=True,exclude={'main.py'}),'')
        result=f.store.supply_dependency(attempt,f.job,f.steps,f.steps[1],f.original,[],f.grants,
            {'kind':'missing_dependency','need':'main.py','reason':'Need exact interface'},1200,enabled=True)
        self.assertIn(f.old,result)
        class Client:
            def chat_as(self,role,session,prompt,max_tokens):
                self.prompt=prompt;self.session=session;return 'answer'
        client=Client()
        scoped=ProjectRoleClient(client,contract,handoff=text)
        self.assertEqual(scoped.chat('same','Original approved task'),'answer')
        self.assertIn(f.old,client.prompt)
        self.assertNotEqual(scoped._session('same'),ProjectRoleClient(client,contract)._session('same'))
        (f.project/'main.py').write_bytes(b'changed')
        with self.assertRaises(GraphError):f.store.proactive_source_context(*args,enabled=True)

    def creative_fixture(self):
        f=media.ProjectMidiTests();f.setUp();self.addCleanup(f.doCleanups)
        key='milestone:1:1:'+ 'a'*16
        job={'id':13,'mode':'build','state':'queued','project':str(f.project),'chat_id':'a',
             'approval_key':key,'prompt':f.request['prompt']}
        steps=[{'id':101,'sequence':0,'path':'play.py','description':'Integrate the approved melody','state':'planned'}]
        graphs=TaskGraphStore(f.root/'task-graph.sqlite3');assignments=ProjectAssignments(graphs)
        grants=f.root/'grants';issue_grant(grants,job,steps);graphs.create(job,steps)
        job['state']='running'
        self.assertTrue(f.runs.reserve(1,1,key,f.plan['code_sha']))
        self.assertTrue(f.runs.finish(key,job['id'],True))
        return f,job,steps,graphs,assignments,grants

    def test_checked_media_handoff_and_changed_bytes_block_commit(self):
        f,job,steps,graphs,assignments,grants=self.creative_fixture()
        lease,_,_=f.ready()
        with self.assertRaises(ValueError):f.store.integration_records(job,f.request,f.plan)
        f.publish(lease)
        records=f.store.integration_records(job,f.request,f.plan)
        self.assertEqual(len(records),1)
        self.assertEqual(records[0]['path'],f.task['output'])
        self.assertEqual(records[0]['bpm'],100)
        self.assertEqual(f.store.integration_records(job,f.request,f.plan,exclude={f.task['output']}),[])
        attempt,contract=assignments.begin(job,steps,steps[0],f.request['prompt'],[],grants,enabled=True)
        handoff=assignments.bind_media_inputs(attempt,records,800)
        self.assertIn(f.task['output'],handoff);self.assertIn(records[0]['sha256'],handoff)
        self.assertIn('not playback or runtime proof',handoff)
        source='THEME = "audio/theme.mid"'
        for kind,proposal in [('plan',json.dumps({'path':steps[0]['path'],'description':steps[0]['description']},ensure_ascii=False)),('code',source)]:
            assignments.review(attempt,kind,proposal,fixture_receipt(f.request['prompt'],proposal))
        assignments.seal(attempt,source)
        args=(attempt,job,steps,steps[0],f.request['prompt'],[],grants,source)
        assignments.validate(*args,enabled=True)
        action=graphs.begin_action(job,steps,'write','file:101')
        (f.project/f.task['output']).write_bytes(midi(dict(f.score,bpm=120)))
        with self.assertRaises(ValueError):assignments.validate(*args,enabled=True)
        with self.assertRaises(ValueError):assignments.commit(*args,action,enabled=True)
        with self.assertRaises(ValueError):f.store.integration_records(job,f.request,f.plan)
        self.assertFalse((f.project/'play.py').exists())

    def test_unrelated_or_changed_roadmap_does_not_supply_receipts(self):
        f,job,steps,graphs,assignments,grants=self.creative_fixture()
        lease,_,_=f.ready();f.publish(lease)
        self.assertEqual(f.store.integration_records(dict(job,approval_key='draft:4'),f.request,f.plan),[])
        with self.assertRaises(ValueError):f.store.integration_records(dict(job,id=14),f.request,f.plan)
        with self.assertRaises(ValueError):f.store.integration_records(job,f.request,dict(f.plan,sha='bad'))
        f.runs.change(1,'paused','User paused')
        with self.assertRaises(ValueError):f.store.integration_records(job,f.request,f.plan)

if __name__=='__main__':unittest.main()
