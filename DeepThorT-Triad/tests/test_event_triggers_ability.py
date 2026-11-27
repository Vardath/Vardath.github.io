import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.website_monitor import WebsiteMonitors
from deepthort_local.condition_monitor import ConditionWatches,observe
from deepthort_local.event_triggers import EventTriggers

class EventTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.base=Path(tmp.name).resolve();self.root=self.base/'project';self.root.mkdir();self.project=str(self.root)
        self.c=ConversationStore(self.base/'c.db');self.web=WebsiteMonitors(self.c);self.cond=ConditionWatches(self.c);self.rules=EventTriggers(self.c)
        self.s={'path':'result.txt','kind':'exists'}
    def condition_check(self,now):
        return self.cond.finish(self.cond.due(self.project,['c'],now=now),observe(self.root,self.s),now=now)
    def web_check(self,now,digest):
        return self.web.finish(self.web.due(self.project,['c'],now=now),{'sha256':digest*64,'bytes':12,'mime':'text/html'},now=now)
    def release(self,now,enabled=True):
        return self.rules.release(self.project,['c'],now=now,enabled=enabled)
    def test_actual_condition_followup(self):
        n=self.cond.create(self.project,'c',self.s,60,4,approved=True,now=100)
        t=self.rules.create(self.project,'c','condition',n,'became_true','Inspect completed result.',1,approved=True,now=100)
        self.condition_check(100);self.assertIsNone(self.release(100))
        (self.root/'result.txt').write_text('complete')
        self.condition_check(160);self.assertIsNone(self.release(160,False))
        r=self.release(160);req=self.c.get(r['request_id'])
        self.assertEqual(r['trigger_id'],t);self.assertEqual(req['mode'],'chat');self.assertEqual(req['attachments'],'[]')
        self.assertTrue(req['prompt'].startswith('Inspect completed result.'))
        self.assertIn('became_true',req['prompt']);self.assertNotIn('complete\n',req['prompt'])
        self.assertIsNone(self.release(200));self.assertEqual(self.rules.rows(self.project,'c')[0]['state'],'finished')
    def test_no_historical_replay_and_coalesce(self):
        n=self.web.create(self.project,'c','https://example.org/',900,6,approved=True,now=100)
        self.web_check(100,'a');self.web_check(1000,'b')
        t=self.rules.create(self.project,'c','website',n,'changed','Review the change.',3,approved=True,now=1000)
        self.assertIsNone(self.release(1000))
        self.web_check(1900,'c');self.web_check(2800,'d')
        r=self.release(2800);self.assertEqual(r['observed_utc'],2800)
        self.assertIsNone(self.release(2800));self.assertEqual(len(self.rules.history(t,self.project,'c')),1)
        self.c.change(r['request_id'],'responded','done','OK');self.assertIsNone(self.release(2801))
    def test_restart_concurrent_exactly_once_and_failed_stop(self):
        n=self.web.create(self.project,'c','https://example.org/',900,4,approved=True,now=100)
        t=self.rules.create(self.project,'c','website',n,'changed','Review.',3,approved=True,now=100)
        self.web_check(100,'a');self.web_check(1000,'b')
        self.rules=EventTriggers(ConversationStore(self.c.path))
        with ThreadPoolExecutor(max_workers=4) as pool:rs=list(pool.map(lambda _:self.release(1000),range(4)))
        admitted=[r for r in rs if r is not None];self.assertEqual(len(admitted),1)
        self.c.change(admitted[0]['request_id'],'failed','fixture failure')
        self.web_check(1900,'c');self.assertIsNone(self.release(1900))
        self.assertEqual(self.rules.rows(self.project,'c')[0]['state'],'cancelled')
        self.assertEqual(len(self.rules.history(t,self.project,'c')),1)
    def test_consent_scope_cancel_and_source_cancel(self):
        n=self.web.create(self.project,'c','https://example.org/',900,4,approved=True,now=100)
        for kwargs in ({'approved':False},{'approved':True,'event':'baseline'},{'approved':True,'chat':'other'}):
            values=dict(project=self.project,chat='c',kind='website',source_id=n,event='changed',prompt='Check.',occurrences=1,now=100)
            values.update(kwargs)
            with self.assertRaises(ValueError):self.rules.create(**values)
        t=self.rules.create(self.project,'c','website',n,'changed','Check.',2,approved=True,now=100)
        self.assertFalse(self.rules.cancel(t,self.project,'other'))
        self.assertTrue(self.web.cancel(n,self.project,'c'));self.assertIsNone(self.release(200))
        self.assertEqual(self.rules.rows(self.project,'c')[0]['state'],'cancelled')
