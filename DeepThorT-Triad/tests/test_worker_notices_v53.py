"""Scripted model replies; real role adapters and durable scoped ledgers."""
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.worker_notices import PREFIX,split_notice,observe_notices
from deepthort_local.worker_reports import observe_worker_reports,counsel_fields,still_current
from deepthort_local.project_assignments import ProjectRoleClient
from deepthort_local.creative_core import create_midi,generate_score_reply,inspect_midi
from deepthort_local.delegation import DelegationStore
from deepthort_local.project_midi import ProjectMidi
import test_worker_reports_v48 as previous
import test_creative_coordination_v49 as creative

NOTICE={'kind':'integration_hint','need':'Owner field or tempo interface','reason':'Useful to upcoming integration.'}
def reply(body):return PREFIX+json.dumps(NOTICE)+'\n'+body

class NoticeTests(unittest.TestCase):
    def test_strict_notice_with_output(self):
        self.assertEqual(split_notice(reply('print(42)')),(NOTICE,'print(42)'))
        self.assertEqual(split_notice('print(42)'),(None,'print(42)'))
        for bad in (PREFIX+json.dumps(NOTICE),reply('DEEPTHORT_WORKER_REPORT:{}'),
                    PREFIX+json.dumps(dict(NOTICE,authority=True))+'\nprint(42)'):
            with self.assertRaises(ValueError):split_notice(bad)
    def test_granite_notice_does_not_block_or_authorize_source(self):
        fixture=previous.WorkerReportTests()
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        class Client:
            def chat_as(self,role,session,prompt,max_tokens):
                self.prompt=prompt
                return reply('print(42)')
        client=Client()
        scoped=ProjectRoleClient(client,fixture.contract,notice=lambda n,o:
            fixture.store.record_notice(fixture.attempt,fixture.request,n,o))
        self.assertEqual(scoped.chat('source','Produce source'),'print(42)')
        self.assertIn(PREFIX,client.prompt)
        self.assertEqual(scoped.chat('source','Produce source'),'print(42)')
        observed=observe_worker_reports(fixture.jobs.path)
        self.assertEqual(observed['reports'],[])
        self.assertEqual(len(observed['notices']),1)
        item=observed['notices'][0]
        self.assertFalse(item['authority']);self.assertFalse(item['verified'])
        self.assertEqual(item['sender'],'implementation')
        self.assertTrue(still_current(fixture.jobs.path,item['receipt_sha']))
        self.assertIn('NONBLOCKING',counsel_fields(item,fixture.jobs.path)[1])
        self.assertEqual(fixture.jobs.get(fixture.jobid)['state'],'running')
        with self.assertRaises(ValueError):fixture.store.seal(fixture.attempt,'print(42)')
        self.assertFalse((fixture.project/'ship.py').exists())
        fixture.jobs.cancel(fixture.jobid)
        self.assertEqual(observe_notices(fixture.jobs.path),[])
    def test_gemma_notice_and_real_midi_validation(self):
        fixture=creative.CreativeCoordination()
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        # Use the same actual private staging root as the production adapter.
        store=ProjectMidi(fixture.runs,DelegationStore(fixture.chats.path,fixture.root/'state'/'creative-tasks'))
        score={'bpm':100,'notes':[[60,480],[62,480],[64,480],[65,480]]}
        answer=reply(json.dumps(score))
        self.assertEqual(generate_score_reply(lambda p:answer,'brief',allow_report=True),answer)
        with self.assertRaises(ValueError):generate_score_reply(lambda p:answer,'brief')
        folder,receipt=create_midi(requester='janus',scope=fixture.contract['scope'],
            brief=fixture.contract['brief'],root=fixture.root,generate=lambda *args:(answer,42))
        self.assertEqual(inspect_midi((folder/'score.mid').read_bytes()),score)
        self.assertEqual(receipt['notice'],NOTICE)
        # Scripted fixture for the native receipt gate, not native-model evidence.
        receipt['native_inference_verified']=True
        (folder/'receipt.json').write_text(json.dumps(receipt),encoding='utf-8')
        self.assertTrue(store.record_notice(fixture.lease,fixture.contract,folder,receipt))
        self.assertFalse(store.record_notice(fixture.lease,fixture.contract,folder,receipt))
        snap=observe_worker_reports(fixture.root/'jobs.sqlite3')
        self.assertEqual(snap['reports'],[])
        self.assertEqual(snap['notices'][0]['sender'],'multimedia')
        self.assertEqual(store.status(fixture.task['id']),'assigned')
        self.assertFalse((fixture.project/fixture.task['output']).exists())
        fixture.runs.change(fixture.req['id'],'paused','User paused')
        self.assertEqual(observe_notices(fixture.root/'jobs.sqlite3'),[])
    def test_tampering_or_supersession_hides_notice(self):
        fixture=previous.WorkerReportTests()
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        fixture.store.record_notice(fixture.attempt,fixture.request,NOTICE,'print(42)')
        self.assertEqual(len(observe_notices(fixture.jobs.path)),1)
        with fixture.graph._db() as db:
            db.execute("UPDATE worker_notices_v53 SET output_sha=?",('a'*64,))
        self.assertEqual(observe_notices(fixture.jobs.path),[])
if __name__=='__main__':unittest.main()
