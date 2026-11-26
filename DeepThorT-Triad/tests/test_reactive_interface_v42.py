"""V42: real recursive peer flow, quiescence and unsolicited local Interface messages."""
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.janus_cognition import CORE_NAMES,SPECIALISTS,SenseFrame,process_society
from deepthort_local.janus_engine import JanusStore
from deepthort_local.watchdog import SentinelStore
from deepthort_local.job_queue import JobStore
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local import interface_outbox

class ReactiveInterfaceTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.jobs=JobStore(self.root/'jobs.sqlite3')
        self.chats=ConversationStore(self.root/'conversations.sqlite3')
        self.j=JanusStore(self.root/'janus.sqlite3')
        self.s=SentinelStore(self.root/'sentinel.sqlite3')

    def test_peer_routes_and_quiescence(self):
        req=self.chats.submit('chat','project','chat','Assess the system constraints.')
        a=self.j.tick(self.jobs.path)
        self.assertEqual(a['peer_exchange']['links'],59)
        for name in SPECIALISTS:
            self.assertEqual(set(a['cores'][name]['peer_sources']),set(SPECIALISTS)-{name})
        for name in ('Left','Right'):
            self.assertEqual(a['cores'][name]['peer_sources'],list(SPECIALISTS))
        self.assertEqual(a['cores']['Front']['peer_sources'],['Left','Right'])
        self.assertEqual(a['cores']['Interface']['peer_sources'],['Front'])
        for c in a['cores'].values():
            self.assertEqual(c['registered_stimuli'][0]['id'],req)
            self.assertEqual(set(c['projection_1_3_4']),{'origin','line','off_line'})
        b=self.j.tick(self.jobs.path)
        self.assertEqual(b['peer_exchange']['links'],0)
        for name in CORE_NAMES:
            self.assertEqual(a['cores'][name]['weights'],b['cores'][name]['weights'])
            self.assertEqual(a['cores'][name]['peer_turn_count'],b['cores'][name]['peer_turn_count'])
        self.assertEqual(b['cores']['Memory']['previous_front'],a['cores']['Front'])
        new=self.chats.submit('chat','project','chat','New requirement: include tests.')
        c=self.j.tick(self.jobs.path)
        self.assertEqual(c['peer_exchange']['links'],59)
        self.assertEqual(c['cores']['Interface']['registered_stimuli'][0]['id'],new)

    def test_janus_unsolicited_message_requires_full_cycle_and_survives_restart(self):
        self.j.recommend(evidence_key='new-idea',problem='Observed failed verification',proposal='Inspect input receipts',origin='local_model')
        self.assertEqual(self.j.interface_unread(),0)
        self.j.tick(self.jobs.path,gaming=True)
        self.assertEqual(self.j.interface_unread(),0)
        a=self.j.tick(self.jobs.path)
        self.assertEqual(a['cores']['Interface']['message']['source_key'],'new-idea')
        self.assertEqual(self.j.interface_unread(),1)
        m=self.j.interface_messages()[0]
        self.assertIn('Inspect input receipts',m['body'])
        self.assertIn('advisory',m['body'])
        reopened=JanusStore(self.j.path)
        reopened.tick(self.jobs.path)
        self.assertEqual(len(reopened.interface_messages()),1)
        self.assertEqual(reopened.acknowledge_interface([m['id']]),1)
        self.assertEqual(JanusStore(self.j.path).interface_unread(),0)
        self.assertEqual(reopened.actions(),[])

    def test_sentinel_independent_message_not_shared_state(self):
        self.s.recommend('s-one','Mismatch observed','Inspect current lease')
        before=self.j.status()['cycle']
        obs={'worker_state':'running','counts':{},'warning':'Mismatch observed'}
        a=self.s.reflect(observation=obs,focus='verify',decision='review',goal='Existing goal',alternatives=['Inspect'])
        self.assertEqual(a['cores']['Interface']['message']['source_key'],'s-one')
        self.assertEqual(self.s.interface_unread(),1)
        self.s.reflect(observation=obs,focus='verify',decision='review',goal='Existing goal',alternatives=['Inspect'])
        self.assertEqual(len(self.s.interface_messages()),1)
        self.assertEqual(self.j.interface_unread(),0)
        self.assertEqual(self.j.status()['cycle'],before)

    def test_reject_bypass_and_changed_source(self):
        self.j.recommend(evidence_key='r',problem='Observed issue',proposal='Inspect evidence')
        with self.j.connect() as db:findings=interface_outbox.pending(db,'janus')
        society=process_society(society='janus',observation={},frames=[SenseFrame('runtime','test','New issue',salience=.8)],
            focus='test',decision='review',findings=findings)
        with self.j.connect() as db:
            society['cores']['Evidence']['finding_refs']=[]
            with self.assertRaises(ValueError):interface_outbox.publish(db,'janus',society,1,'test')
        society=process_society(society='janus',observation={},frames=[SenseFrame('runtime','test','New issue',salience=.8)],
            focus='test',decision='review',findings=findings)
        with self.j.connect() as db:
            db.execute("UPDATE janus_recommendations SET proposal='changed' WHERE evidence_key='r'")
            self.assertFalse(interface_outbox.publish(db,'janus',society,1,'test'))
        self.assertEqual(self.j.interface_unread(),0)

    def test_upgrade_baseline_and_pause(self):
        self.j.recommend(evidence_key='old',problem='Historic issue',proposal='Historic advice')
        with self.j.connect() as db:
            db.execute('DROP TABLE interface_settings')
            db.execute('DROP TABLE interface_messages')
        j=JanusStore(self.j.path)
        j.tick(self.jobs.path)
        self.assertEqual(j.interface_unread(),0)
        j.recommend(evidence_key='new',problem='New issue',proposal='New advice')
        j.set_paused(True)
        j.tick(self.jobs.path)
        self.assertEqual(j.interface_unread(),0)
        j.set_paused(False)
        j.tick(self.jobs.path)
        self.assertEqual(j.interface_unread(),1)
        self.assertNotIn('Historic',j.interface_messages()[0]['body'])

if __name__=='__main__':unittest.main()
