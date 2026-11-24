"""v33: generated app scripts are never written or executed without two approvals."""
from __future__ import annotations
from contextlib import closing
import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deepthort_local.janus_engine import JanusStore
from deepthort_local.tool_acquisition import ToolAcquisition


class GeneratedScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.project=self.root/'project';self.project.mkdir()
        self.store=ToolAcquisition(self.root/'learn.sqlite3')
        self.janus=JanusStore(self.root/'janus.sqlite3')
        self.store.discover([{'name':'Python','location':str(Path(sys.executable).resolve(strict=True))}])
        act=self.store.authorize_probe('Python',self.project,self.janus,user_approved=True)
        log=self.root/'help.log';log.write_text('usage: python options --help\n')
        self.janus.update_action(act,'succeeded',detail='help',returncode=0,output_file=str(log))
        self.store.start_learning(9,'Python',self.project,'Generate a local output artifact')

    def propose(self, source=None, path='automation/create.py', title='Write a local artifact'):
        if source is None:
            source='from pathlib import Path\nimport sys\nPath(sys.argv[1]).write_text("made by approved script")\n'
        body={'title':title,'purpose':'Create a checked project output file',
              'args':['{{script}}','{{output}}'],'artifact':'output.txt',
              'script':{'path':path,'source':source}}
        return self.store.propose_recipe(9,json.dumps(body))

    def test_candidate_contains_source_but_does_not_write_or_execute(self):
        with patch('subprocess.Popen',side_effect=AssertionError('never execute')):
            r=self.propose()
        self.assertFalse((self.project/'automation/create.py').exists())
        self.assertTrue(self.store.script_needs_review(r,self.project))
        self.assertEqual(self.store.script_review(r,self.project)['source'].splitlines()[0],
                         'from pathlib import Path')
        self.assertEqual([a['kind'] for a in self.janus.actions()],['tool'])
        with self.assertRaises(PermissionError):
            self.store.stage_script(r,self.project,self.root/'backup')
        with self.assertRaises(ValueError):
            self.store.preview_recipe(r,self.project)

    def test_two_explicit_approvals_and_existing_worker_real_execution(self):
        from janus_worker import JanusWorker
        r=self.propose()
        saved=self.store.stage_script(r,self.project,self.root/'backup',user_approved=True)
        self.assertTrue(saved.is_file())
        self.assertEqual(len(self.janus.actions()),1)
        self.assertEqual(self.store.preview_recipe(r,self.project)['argv'][1],str(saved))
        with self.assertRaises(PermissionError):
            self.store.authorize_recipe(r,self.project,self.janus)
        action=self.store.authorize_recipe(r,self.project,self.janus,user_approved=True)
        self.assertEqual(self.janus.action(action)['status'],'approved')
        worker=JanusWorker(self.janus.path,self.root/'jobs.sqlite3',self.root/'games.txt')
        self.assertEqual(worker.execute_next_approved(),action)
        self.assertEqual((self.project/'output.txt').read_text(),'made by approved script')
        self.assertEqual(self.store.reconcile(r,self.project,self.janus)['status'],'artifact_produced')
        self.assertEqual(len(self.store.current_recipes(self.project,self.janus)),1)

    def test_changed_script_blocks_execution_and_revokes_verified_recipe(self):
        r=self.propose()
        saved=self.store.stage_script(r,self.project,self.root/'backup',user_approved=True)
        saved.write_text('print("changed")\n')
        with self.assertRaises(ValueError):
            self.store.authorize_recipe(r,self.project,self.janus,user_approved=True)
        self.assertEqual(len(self.janus.actions()),1)
        self.assertTrue(self.store.script_needs_review(r,self.project))

    def test_reapproved_edit_produces_backup_and_needs_separate_command_approval(self):
        old=self.project/'automation/create.py';old.parent.mkdir();old.write_text('print("old")\n')
        r=self.propose()
        preview=self.store.script_review(r,self.project)
        self.assertIn('print("old")',preview['diff'])
        self.assertIn('from pathlib',preview['diff'])
        self.store.stage_script(r,self.project,self.root/'backups',user_approved=True)
        self.assertNotIn('old',old.read_text())
        self.assertEqual(len(list((self.root/'backups').rglob('create.py'))),1)

    def test_changed_script_invalidates_successful_process_evidence(self):
        from janus_worker import JanusWorker
        r=self.propose(); saved=self.store.stage_script(r,self.project,self.root/'backups',user_approved=True)
        action=self.store.authorize_recipe(r,self.project,self.janus,user_approved=True)
        JanusWorker(self.janus.path,self.root/'jobs.sqlite3',self.root/'games.txt').execute_next_approved()
        self.assertEqual(self.store.reconcile(r,self.project,self.janus)['status'],'artifact_produced')
        saved.write_text('print("tampered")\n')
        self.assertEqual(self.store.reconcile(r,self.project,self.janus)['status'],'unverified')
        self.assertFalse(self.store.current_recipes(self.project,self.janus))

    def test_invalid_script_syntax_and_escape_blocked_before_persistence(self):
        for source,path in [('def broken(:\n','automation/bad.py'),
                            ('print(1)\n','../escape.py'),
                            ('print(1)\n','automation/generate.sh'),
                            ('\0print(1)\n','automation/bad.py')]:
            with self.subTest(source=source,path=path):
                with self.assertRaises(ValueError):self.propose(source,path)
        self.assertEqual(self.store.recipes(self.project),[])

    def test_old_v32_schema_migrates_without_losing_existing_recipe(self):
        # An installed v32 database already has this table; the v33 columns
        # must be added instead of silently replacing user recipes.
        db=self.root/'old.sqlite3'
        with closing(sqlite3.connect(db)) as connection, connection:
            connection.execute('''CREATE TABLE learned_recipes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,
                project_key TEXT NOT NULL,title TEXT NOT NULL,purpose TEXT NOT NULL,
                args_json TEXT NOT NULL,artifact TEXT NOT NULL,
                executable_signature TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'candidate',
                action_id INTEGER,approved_argv TEXT,project_root TEXT,artifact_before TEXT,
                log_file TEXT,log_sha TEXT,artifact_after TEXT,evidence_at TEXT,
                UNIQUE(name,project_key,title))''')
            connection.execute("INSERT INTO learned_recipes(name,project_key,title,purpose,args_json,artifact,executable_signature,project_root) VALUES('Python','a','legacy','legacy','[]','','b','root')")
        new=ToolAcquisition(db)
        with new._db() as connection:
            self.assertEqual(connection.execute('SELECT title,script_path FROM learned_recipes').fetchone()[:],
                             ('legacy',''))

    def test_plain_v32_command_recipes_remain_supported(self):
        r=self.store.propose_recipe(9,json.dumps({'title':'Version of the interpreter',
            'purpose':'Report which Python version is available',
            'args':['--version'],'artifact':''}))
        self.assertFalse(self.store.script_needs_review(r,self.project))
        self.assertIn('--version',self.store.preview_recipe(r,self.project)['argv'])


if __name__=='__main__':unittest.main()
