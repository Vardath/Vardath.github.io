"""Verify original recursive societies against real durable delegation state."""
import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from deepthort_local.janus_engine import JanusStore
from deepthort_local.watchdog import JanusSentinel
from deepthort_local.janus_cognition import CORE_NAMES,FACULTIES
from deepthort_local.job_queue import JobStore
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.team_delegation import TeamDelegationStore
from deepthort_local.delegation_senses import observe_delegation
from janus_worker import JanusWorker

class SocietyWorkflowTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.jobs_path=self.root/'jobs.sqlite3'
        self.jobs=JobStore(self.jobs_path)
        self.janus=JanusStore(self.root/'janus.sqlite3')
        self.chats=ConversationStore(self.root/'conversations.sqlite3')
        self.store=TeamDelegationStore(self.chats.path,self.root/'creative-tasks')
        self.req=self.chats.submit('thread','private-project','chat','/delegate design Private brief.')
        self.games=self.root/'games.txt'
        self.games.write_text('game.exe\n')
    def topology(self,society):
        self.assertEqual(set(society['cores']),set(CORE_NAMES))
        for core in society['cores'].values():
            self.assertEqual(set(core['internal_fano_faculties']),{str(d) for d in FACULTIES})
        self.assertEqual(society['cores']['Front']['input_sources'],['Left','Right'])
        self.assertEqual(society['cores']['Interface']['input_sources'],['Front'])
    def sentinel(self):
        worker=JanusSentinel(sentinel_db=self.root/'sentinel.sqlite3',
            janus_db=self.root/'janus.sqlite3',jobs_db=self.jobs_path,
            games_file=self.games,gui_heartbeat=self.root/'heartbeat.json',
            worker_command=[sys.executable,'-c','import time;time.sleep(20)'])
        self.addCleanup(worker.shutdown)
        return worker
    def test_both_original_societies_observe_dependency_progress_independently(self):
        self.janus.set_goal('Preserve original user goal')
        first=self.janus.tick(self.jobs_path)
        self.topology(first)
        self.assertEqual(first['focus'],'delegated_team_work')
        self.assertEqual(observe_delegation(self.jobs_path)['pending'],1)
        self.assertTrue(self.store.start(self.req))
        self.store.plan(self.store.claim(self.req,'janus'),json.dumps({'tasks':[
            {'id':'spec','kind':'design','brief':'Specify interface','depends_on':[]}]}))
        second=self.janus.tick(self.jobs_path)
        self.topology(second)
        self.assertEqual(second['cores']['Memory']['previous_front'],first['cores']['Front'])
        self.assertEqual(self.janus.goal(),'Preserve original user goal')
        snap=observe_delegation(self.jobs_path)
        self.assertEqual(snap['active'][0]['ready_roles']['sentinel'],1)
        self.assertNotIn('Private brief',json.dumps(snap))
        self.assertNotIn('private-project',json.dumps(snap))
        s=self.sentinel()
        before=self.janus.status()['cycle']
        s.step()
        society=json.loads(s.store.snapshot()['society_json'])
        self.topology(society)
        self.assertEqual(society['society'],'sentinel')
        self.assertEqual(society['cores']['Evidence']['observations']['delegation'],snap)
        self.assertEqual(self.janus.status()['cycle'],before)
        self.assertFalse(self.janus.actions())
        self.assertEqual(self.store.summary(self.req)['state'],'running')
    def test_interruption_and_cancel_are_observations_not_authority(self):
        self.assertTrue(self.store.start(self.req))
        self.store.claim(self.req,'janus')
        self.chats.cancel_chat_requests('thread','Cancelled')
        state=self.janus.tick(self.jobs_path)
        self.assertEqual(state['focus'],'delegated_team_review')
        self.assertTrue(state['cores']['Evidence']['observations']['conflict'])
        self.assertFalse(self.janus.actions())
        s=self.sentinel()
        s.step()
        status=s.store.snapshot()
        self.assertEqual(status['focus'],'delegation_review')
        self.assertIn('disagree',json.loads(status['observation_json'])['warning'])
        self.assertEqual(self.store.summary(self.req)['state'],'running')
        self.store.fail(self.req,'Cancelled',interrupted=True)
        self.assertEqual(self.chats.get(self.req)['state'],'cancelled')
        self.assertFalse(observe_delegation(self.jobs_path)['active'])
    def test_legacy_state_without_team_tables_is_not_false_work(self):
        with closing(sqlite3.connect(self.chats.path)) as db,db:
            db.execute('DROP TABLE agent_edges_v39')
        self.assertFalse(observe_delegation(self.jobs_path)['available'])
        self.assertEqual(self.janus.tick(self.jobs_path)['focus'],'idle')
    def test_active_process_observation_allows_scoped_cognition_but_never_dispatches(self):
        worker=JanusWorker(self.root/'janus.sqlite3',self.jobs_path,self.games,game_probe=lambda:False)
        with patch.object(worker,'execute_next_approved') as execute,patch.object(worker,'_consider_local_alternatives') as counsel, \
             patch.object(worker,'_consider_live_work') as live:

            worker._observe_active_process()
            worker._observe_active_process()
            execute.assert_not_called();counsel.assert_not_called()
            self.assertEqual(live.call_count,2)
        self.assertEqual(self.janus.status()['cycle'],2)
        self.janus.set_paused(True)
        worker._observe_active_process()
        self.assertEqual(self.janus.status()['cycle'],2)

if __name__=='__main__':unittest.main()
