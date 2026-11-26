"""Existing roadmap gates, conservative overlap selection and resource admission."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from deepthort_local.task_graph import independent_workspaces
from deepthort_local.job_queue import JobStore
from deepthort_local.adaptive_admission import parallel_media_admitted
from deepthort_local.project_midi import ready_independent
import test_project_midi_v45 as previous

class IndependentProjectTests(unittest.TestCase):
    def test_nested_or_unknown_workspace_cannot_share_write_lanes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a=root/'a';a.mkdir();nested=a/'sub';nested.mkdir();b=root/'b';b.mkdir()
            self.assertTrue(independent_workspaces(str(a),str(b)))
            for left,right in ((a,a),(a,nested),(nested,a),(a,root),(root,a),(a,root/'missing')):
                self.assertFalse(independent_workspaces(str(left),str(right)))
            jobs=JobStore(root/'jobs.sqlite3')
            first=jobs.submit(str(nested),'a','build','Nested job')
            second=jobs.submit(str(b),'b','build','Independent job')
            self.assertEqual(jobs.next_any_queued(exclude_project=str(a))['id'],second)
            self.assertEqual(jobs.get(first)['state'],'queued')

    def test_overlap_requires_live_broker_and_extra_headroom(self):
        health={'pid':42,'ready':True,'serial_memory_mode':False,'admission_waiting':0,
                'admission_slots':2,'models':{r:{'resident':True,'generating':r=='implementation'} for r in ('janus','sentinel','implementation')},
                'memory_model':{'resident':True,'generating':False}}
        self.assertTrue(parallel_media_admitted(health,42,lambda:True))
        self.assertFalse(parallel_media_admitted(health,42,lambda:False))
        for override in ({'pid':43},{'serial_memory_mode':True},{'admission_waiting':1},
                         {'admission_slots':1},{'ready':False},{'models':{}},
                         {'memory_model':{'resident':True,'generating':True}},
                         {'memory_model':{'resident':False,'generating':False}}):
            self.assertFalse(parallel_media_admitted(dict(health,**override),42,
                lambda:self.fail('Resource probe should not run for denied broker')))

    def test_select_only_existing_ready_native_boundary(self):
        f=previous.ProjectMidiTests();f.setUp();self.addCleanup(f.doCleanups)
        separate=f.root/'code';separate.mkdir()
        workflows=SimpleNamespace(roadmap_members=lambda ident:[])
        mixed=SimpleNamespace(get=lambda *a:f.plan,request_for=lambda task:None)
        conversations=SimpleNamespace(get=lambda ident:f.request)
        result={'complete':False,'manifest_sha256':f.plan['code_sha'],'milestone':{'ordinal':1}}
        args=(f.runs,conversations,None,None,None,mixed,workflows,f.store)
        with patch('deepthort_local.roadmap_runs.eligible_successor',return_value=result) as successor, \
             patch('deepthort_local.roadmap_tool_bridge.gate',return_value=[]) as gate:
            candidate=ready_independent(*args,exclude_project=str(separate))
            self.assertIsNotNone(candidate)
            self.assertEqual(candidate[2],f.task)
            self.assertEqual(candidate[4],1)
            self.assertIsNone(f.store.status(f.task['id']))
            self.assertFalse((f.project/f.task['output']).exists())
            gate.assert_called_once_with(workflows,1,f.plan['code_sha'],1)
            successor.reset_mock()
            self.assertIsNone(ready_independent(*args,exclude_project=str(f.project)))
            successor.assert_not_called()
            gate.return_value=['Blocked tool']
            self.assertIsNone(ready_independent(*args,exclude_project=str(separate)))
            gate.return_value=[]
            mixed.request_for=lambda task:10
            self.assertIsNone(ready_independent(*args,exclude_project=str(separate)))
            mixed.request_for=lambda task:None
            f.begin()
            self.assertIsNone(ready_independent(*args,exclude_project=str(separate)))

if __name__=='__main__':unittest.main()
