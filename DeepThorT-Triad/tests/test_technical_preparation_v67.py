"""Actual approved stores and source bytes; scripted Granite reply."""
import json
import unittest
from pathlib import Path
from deepthort_local.project_authority import issue_grant
from deepthort_local.technical_preparation import run_once, advice
from deepthort_local.workflow_attention import choose, evidence
import test_memory_duty_v47 as previous

class TechnicalPreparationTests(unittest.TestCase):
    def setUp(self):
        self.f=previous.MemoryDutyTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.path=Path(self.f.project)/'ship.py'
        self.path.write_text('def load_ship(owner): return owner',encoding='utf-8')
        issue_grant(self.f.root/'project-grants',self.f.jobs.get(self.f.job),self.f.jobs.steps(self.f.job))
        self.f.jobs.change(self.f.job,'running','Approved work')
        self.calls=[]
        test=self
        class Client:
            def chat_as(self,role,session,prompt,max_tokens):
                test.calls.append((role,prompt))
                return json.dumps({'kind':'advice','finding':'Check owner on load','guidance':'Add a regression test for the owner field.'})
        self.client=Client()
    def test_independent_preparation_and_delivery(self):
        f=self.f
        item=run_once(f.jobs.path,self.client,lambda:False)
        self.assertEqual(self.calls[0][0],'implementation')
        self.assertIn('def load_ship(owner)',self.calls[0][1])
        self.assertFalse(item['authority'])
        self.assertFalse(item['verified'])
        packet=choose(f.jobs.path,'janus')
        self.assertIn('Check owner on load',advice(f.jobs.path,f.job,f.original,packet['focus']))
        self.assertIn('Check owner on load',evidence(f.jobs.path,packet))
        self.assertIsNone(run_once(f.jobs.path,self.client,lambda:False))
        self.assertEqual(len(self.calls),1)
        self.assertEqual(self.path.read_text(encoding='utf-8'),'def load_ship(owner): return owner')
        self.path.write_text('changed after approval',encoding='utf-8')
        self.assertEqual(advice(f.jobs.path,f.job,f.original,packet['focus']),'')
        self.assertIsNone(run_once(f.jobs.path,self.client,lambda:False))
    def test_cancel_and_pause(self):
        f=self.f
        self.assertIsNone(run_once(f.jobs.path,self.client,lambda:True))
        self.assertFalse(self.calls)
        packet=choose(f.jobs.path,'janus')
        run_once(f.jobs.path,self.client,lambda:False)
        f.jobs.cancel(f.job)
        self.assertEqual(advice(f.jobs.path,f.job,f.original,packet['focus']),'')
        self.assertIsNone(run_once(f.jobs.path,self.client,lambda:False))
if __name__=='__main__':unittest.main()
