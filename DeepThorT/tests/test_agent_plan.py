import tempfile,unittest
from pathlib import Path
from deepthort_local.agent_plan import parse_build_plan,PlanError
from deepthort_local.job_queue import JobStore

class AgentPlanTests(unittest.TestCase):
 def test_parse_valid_and_no_escape(self):
  with tempfile.TemporaryDirectory() as td:
   result=parse_build_plan('{"files":[{"path":"src/main.py","description":"Main program"},{"path":"test_main.py","description":"Unit tests"}]}',td)
   self.assertEqual(result[0]['path'],'src/main.py')
   with self.assertRaises(PlanError):
    parse_build_plan('{"files":[{"path":"../outside.py","description":"Escape path"}]}',td)
   with self.assertRaises(PlanError):
    parse_build_plan('A nice plan',td)
 def test_persist_plan_steps_and_large_prompts(self):
  with tempfile.TemporaryDirectory() as td:
   store=JobStore(Path(td)/'queue.sqlite3')
   job=store.submit(td,'abc','build','Build a game '*1000)
   self.assertEqual(len(store.get(job)['prompt']),13000)
   store.add_plan(job,[{'path':'game.py','description':'Game loop'}])
   step=store.next_step(job)
   self.assertEqual(step['path'],'game.py')
   store.set_step(step['id'],'saved','User approved code')
   self.assertIsNone(store.next_step(job))
   self.assertEqual(JobStore(Path(td)/'queue.sqlite3').steps(job)[0]['state'],'saved')
 def test_migrate_v6(self):
  import sqlite3
  with tempfile.TemporaryDirectory() as td:
   db=Path(td)/'q.sqlite3'
   with sqlite3.connect(db) as c:
    c.execute('''CREATE TABLE jobs (id INTEGER PRIMARY KEY AUTOINCREMENT,project TEXT NOT NULL,chat_id TEXT NOT NULL,
       mode TEXT NOT NULL CHECK(mode IN ('chat','edit','plan')),target TEXT,prompt TEXT NOT NULL,
       state TEXT NOT NULL DEFAULT 'queued',detail TEXT NOT NULL DEFAULT 'Waiting for model',
       result TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
       updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
    c.execute("INSERT INTO jobs(project,chat_id,mode,prompt) VALUES('p','c','chat','preserved')")
   store=JobStore(db)
   self.assertEqual(store.get(1)['prompt'],'preserved')
   self.assertEqual(store.submit('p','c','build','new task'),2)

if __name__=='__main__':unittest.main()
