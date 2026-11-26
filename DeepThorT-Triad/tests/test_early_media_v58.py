"""Explicit same-project private staging; old publication boundary remains mandatory."""
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from deepthort_local.mixed_roadmap import parse_tasks,pending_task
from deepthort_local.project_midi import early_window,ready_same_project,ProjectMidi
from deepthort_local.tool_workflows import digest
from deepthort_local.reasoning_council import sha
from deepthort_local.job_queue import JobStore
import test_project_midi_v45 as previous

class EarlyMediaTests(unittest.TestCase):
    def fixture(self):
        f=previous.ProjectMidiTests();f.setUp();self.addCleanup(f.doCleanups)
        # A distinct exact approval, not mutation of a previously approved mixed manifest.
        f.runs=type(f.runs)(f.root/'early-roadmap.sqlite3')
        f.store=ProjectMidi(f.runs,f.delegations)
        f.task=dict(f.task,after=1,prepare_after=0)
        body={'request_id':1,'code_sha':'c'*64,'tasks':[f.task]}
        f.plan={**body,'sha':digest(body)}
        f.runs.approve(dict(f.approval,mixed_sha=f.plan['sha']))
        key='milestone:1:1:'+sha(f.request['prompt'])[:16]
        job={'id':13,'mode':'build','state':'running','project':str(f.project),'chat_id':'a',
             'approval_key':key,'prompt':'Exact code milestone'}
        self.assertTrue(f.runs.reserve(1,1,key,f.plan['code_sha']))
        self.assertTrue(f.runs.finish(key,job['id'],True))
        return f,job

    def test_only_explicit_one_milestone_native_preparation(self):
        f,_=self.fixture()
        roadmap={'project':str(f.project),'schedule':[{'steps':[{'path':'main.py'}]}]}
        task={'after':1,'prepare_after':0,'goal':'Independent melody','output':'audio.mid'}
        parsed=parse_tasks(json.dumps({'artifacts':[task]}),roadmap,1)[0]
        self.assertTrue(early_window(parsed,1))
        for bad in (dict(task,prepare_after=1),dict(task,output='image.png'),dict(task,after=0),
                    dict(task,prepare_after=False)):
            with self.assertRaises(ValueError):parse_tasks(json.dumps({'artifacts':[bad]}),roadmap,1)
        self.assertFalse(early_window({k:v for k,v in parsed.items() if k!='prepare_after'},1))

    def test_private_stage_restart_and_original_publication_gate(self):
        f,job=self.fixture()
        run=f.runs.get(1)
        with self.assertRaises(ValueError):f.store.begin(run,f.plan,f.task,f.request,2,enabled=True,
            early_job=dict(job,id=14))
        lease,contract=f.store.begin(run,f.plan,f.task,f.request,2,enabled=True,early_job=job)
        folder,receipt,review=f.stage(contract)
        f.store.reviewed(lease,contract,folder,receipt,review)
        self.assertEqual(f.store.status(f.task['id']),'prepared')
        self.assertFalse((f.project/f.task['output']).exists())
        with self.assertRaises(ValueError):f.store.publish(lease,run,f.plan,f.task,f.request,2,enabled=True)
        reopened=ProjectMidi(f.runs,f.delegations);reopened.recover()
        self.assertEqual(reopened.status(f.task['id']),'prepared')
        workflows=SimpleNamespace(roadmap_members=lambda ident:[])
        args=(run,f.plan,f.task,f.request,None,None,None,None,workflows)
        with patch('deepthort_local.roadmap_runs.eligible_successor',return_value=None) as successor:
            with self.assertRaises(ValueError):reopened.publish_prepared(*args,enabled=True)
            self.assertEqual(reopened.status(f.task['id']),'prepared')
            self.assertFalse((f.project/f.task['output']).exists())
            successor.return_value={'complete':False,'manifest_sha256':f.plan['code_sha'],'milestone':{'ordinal':2}}
            result=reopened.publish_prepared(*args,enabled=True)
            self.assertFalse(result['runtime_verified'])
        self.assertEqual(reopened.status(f.task['id']),'checked')
        self.assertTrue((f.project/f.task['output']).is_file())

    def test_ready_only_same_exact_approved_milestone_and_unblocked_prefix(self):
        f,job=self.fixture()
        run=f.runs.get(1)
        current={'project':run['project'],'chat_id':'a','manifest_sha256':f.plan['code_sha'],'schedule':[{}]}
        req=f.request
        conversations=SimpleNamespace(get=lambda ident:req,latest_project_request=lambda *a:req,
                                      amendment_supersedes=lambda *a:False)
        hierarchies=SimpleNamespace(milestone=lambda *a:{'state':'queued','job_id':job['id'],
                    'approval_key':job['approval_key'],'scope_prompt':job['prompt']})
        mixed=SimpleNamespace(get=lambda *a:f.plan,request_for=lambda task:None)
        workflows=SimpleNamespace(roadmap_members=lambda ident:[])
        args=(f.runs,conversations,hierarchies,None,None,mixed,workflows,f.store)
        with patch('deepthort_local.roadmap_runs.manifest',return_value=current), \
             patch('deepthort_local.roadmap_runs.verified_prefix') as prefix:
            candidate=ready_same_project(*args,active=job)
            self.assertEqual(candidate[2],f.task)
            self.assertEqual(candidate[4],2)
            self.assertIsNone(ready_same_project(*args,active=dict(job,id=99)))
            prefix.side_effect=ValueError('Stale verified predecessor')
            self.assertIsNone(ready_same_project(*args,active=job))
        self.assertIsNone(f.store.status(f.task['id']))

    def test_exact_code_job_can_continue_while_private_lane_reserved(self):
        f,_=self.fixture()
        jobs=JobStore(f.root/'jobs.sqlite3')
        other=jobs.submit(str(f.project),'other','build','Unrelated same workspace')
        code=jobs.submit(str(f.project),'code','build','Approved continuing job')
        self.assertIsNone(jobs.next_any_queued(exclude_project=str(f.project)))
        self.assertEqual(jobs.next_any_queued(exclude_project=str(f.project),
            allow_private_preparation_job=code)['id'],code)
        self.assertEqual(jobs.get(other)['state'],'queued')

if __name__=='__main__':unittest.main()
