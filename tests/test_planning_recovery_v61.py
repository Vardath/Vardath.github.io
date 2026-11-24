import sqlite3
import tempfile
import unittest
from pathlib import Path
from deepthort_local.planning_recovery import observe_planning, resume_stalled_draft

FAIL='Local model request failed: Indexed X4 roadmap paused for lack of verified progress'

class Index:
    def __init__(self):self.closed=0
    def status(self,ident,original):return {'sha256':'source-'+original,'reviewed':3}
    def roadmap_stall_status(self,ident,original):return {'checks_closed_total':self.closed}

class PlanningRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'conversations.sqlite3'
        self.db=sqlite3.connect(self.path)
        self.addCleanup(self.db.close)
        self.db.execute('''CREATE TABLE conversation_requests (
            id INTEGER PRIMARY KEY,project TEXT,chat_id TEXT,mode TEXT,prompt TEXT,
            state TEXT,detail TEXT,updated_at TEXT)''')
        self.index=Index()

    def add(self,ident,state='failed',detail=FAIL,chat='chat'):
        with self.db:
            self.db.execute("INSERT INTO conversation_requests VALUES (?,?,?,'draft_plan','exact source',?,?,CURRENT_TIMESTAMP)",
                (ident,'project',chat,state,detail))

    def fail(self,ident,detail=FAIL):
        with self.db:self.db.execute("UPDATE conversation_requests SET state='failed',detail=? WHERE id=?",(detail,ident))

    def test_bounded_retries_survive_restart_and_require_progress(self):
        self.add(1)
        for attempt in (1,2):
            result=resume_stalled_draft(self.path,self.index,cooldown_seconds=0)
            self.assertEqual(result['attempt'],attempt)
            self.assertEqual(observe_planning(self.path.parent/'jobs.sqlite3')[0]['state'],'pending')
            self.fail(1,FAIL+' '+str(attempt))
        self.assertIsNone(resume_stalled_draft(self.path,self.index,cooldown_seconds=0))
        self.index.closed=1
        self.assertEqual(resume_stalled_draft(self.path,self.index,cooldown_seconds=0)['attempt'],1)

    def test_never_revive_cancelled_superseded_or_source_blocked(self):
        self.add(1)
        self.add(2,state='cancelled')
        self.add(3,detail='Local model request failed: X4 source missing',chat='other')
        self.assertIsNone(resume_stalled_draft(self.path,self.index,cooldown_seconds=0))
        plans=observe_planning(self.path.parent/'jobs.sqlite3')
        self.assertEqual([p['id'] for p in plans],[3])
        self.assertNotIn('prompt',plans[0])

    def test_cooldown_prevents_immediate_retry(self):
        self.add(1)
        self.assertIsNone(resume_stalled_draft(self.path,self.index,cooldown_seconds=90))

if __name__=='__main__':
    unittest.main()
