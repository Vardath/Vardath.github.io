"""v34: approvals cannot silently outlive changed files or runaway child tools."""
from __future__ import annotations

from contextlib import closing
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deepthort_local.action_guards import snapshot_file, verify_guards
from deepthort_local.janus_engine import JanusStore
from deepthort_local.tool_acquisition import ToolAcquisition
from deepthort_local.workspace import apply_approved_file, WorkspaceError, safe_target
from janus_worker import JanusWorker


class SupervisedExecutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.project=self.root/'project';self.project.mkdir()
        self.janus=JanusStore(self.root/'janus.sqlite3')
        self.library=ToolAcquisition(self.root/'library.sqlite3')
        self.library.discover([{'name':'Python','location':str(Path(sys.executable).resolve(strict=True))}])
        action=self.library.authorize_probe('Python',self.project,self.janus,user_approved=True)
        self.assertTrue(json.loads(self.janus.action(action)['input_guards_json']))
        log=self.root/'probe.log';log.write_text('python --help\n')
        self.janus.update_action(action,'succeeded',detail='help',returncode=0,output_file=str(log))
        self.library.start_learning(11,'Python',self.project,'Create an output file using approved Python')

    def recipe(self, *, uses_input=False):
        src=('from pathlib import Path\nimport sys\n'
             'Path(sys.argv[-1]).write_text("generated")\n')
        args=['{{script}}']+(['{{input}}'] if uses_input else [])+['{{output}}']
        obj={'title':'Create output artifact','purpose':'Check output file after supervised command',
             'args':args,'artifact':'output.txt',
             'script':{'path':'automation/make.py','source':src}}
        rid=self.library.propose_recipe(11,json.dumps(obj))
        review=self.library.script_review(rid,self.project)
        self.library.stage_script(rid,self.project,self.root/'backup',user_approved=True,
                                  expected_proposal_sha=review['proposal_sha'],
                                  expected_existing_sha=review['existing_sha'])
        return rid

    def worker(self):
        return JanusWorker(self.janus.path,self.root/'jobs.sqlite3',self.root/'games.txt')

    def test_change_script_after_command_approval_blocks_worker_spawn(self):
        rid=self.recipe()
        ident=self.library.authorize_recipe(rid,self.project,self.janus,user_approved=True)
        (self.project/'automation/make.py').write_text('print("changed")\n')
        with patch('janus_worker.subprocess.Popen',side_effect=AssertionError('should not run')):
            self.assertEqual(self.worker().execute_next_approved(),ident)
        self.assertEqual(self.janus.action(ident)['status'],'needs_attention')
        self.assertFalse((self.project/'output.txt').exists())
        self.assertEqual(self.library.reconcile(rid,self.project,self.janus)['status'],'unverified')

    def test_changed_selected_input_blocks_queued_process(self):
        (self.project/'input.txt').write_text('original')
        rid=self.recipe(uses_input=True)
        ident=self.library.authorize_recipe(rid,self.project,self.janus,user_approved=True,input_file='input.txt')
        (self.project/'input.txt').write_text('modified')
        with patch('janus_worker.subprocess.Popen',side_effect=AssertionError('should not run')):
            self.worker().execute_next_approved()
        self.assertEqual(self.janus.action(ident)['status'],'needs_attention')

    def test_new_output_created_after_approval_blocks(self):
        rid=self.recipe()
        ident=self.library.authorize_recipe(rid,self.project,self.janus,user_approved=True)
        (self.project/'output.txt').write_text('different process output')
        with patch('janus_worker.subprocess.Popen',side_effect=AssertionError('should not run')):
            self.worker().execute_next_approved()
        self.assertEqual(self.janus.action(ident)['status'],'needs_attention')

    def test_approved_command_must_equal_preview(self):
        rid=self.recipe()
        old=self.library.preview_recipe(rid,self.project)
        with self.assertRaisesRegex(ValueError,'Command changed'):
            self.library.authorize_recipe(rid,self.project,self.janus,user_approved=True,
                                          expected_argv=old['argv']+['unexpected'])
        self.assertEqual(len(self.janus.actions()),1)

    def test_script_changed_after_review_cannot_be_staged(self):
        rid=self.library.propose_recipe(11,json.dumps({
            'title':'Another generated script','purpose':'Generate a project output for testing',
            'args':['{{script}}','{{output}}'],'artifact':'output.txt',
            'script':{'path':'task.py','source':'print("old")\n'}}))
        review=self.library.script_review(rid,self.project)
        (self.project/'task.py').write_text('print("someone else")\n')
        with self.assertRaisesRegex(ValueError,'Target changed'):
            self.library.stage_script(rid,self.project,self.root/'backups',user_approved=True,
                                      expected_proposal_sha=review['proposal_sha'],
                                      expected_existing_sha=review['existing_sha'])
        self.assertEqual((self.project/'task.py').read_text(),'print("someone else")\n')

    def test_changed_stored_candidate_cannot_override_earlier_review(self):
        rid=self.library.propose_recipe(11,json.dumps({
            'title':'Changing draft test','purpose':'Generate an approved output to test',
            'args':['{{script}}','{{output}}'],'artifact':'output.txt',
            'script':{'path':'task.py','source':'print("version 1")\n'}}))
        review=self.library.script_review(rid,self.project)
        self.library.propose_recipe(11,json.dumps({
            'title':'Changing draft test','purpose':'Generate an approved output to test',
            'args':['{{script}}','{{output}}'],'artifact':'output.txt',
            'script':{'path':'task.py','source':'print("version 2")\n'}}))
        with self.assertRaisesRegex(ValueError,'changed since approval'):
            self.library.stage_script(rid,self.project,self.root/'backups',user_approved=True,
                                      expected_proposal_sha=review['proposal_sha'],
                                      expected_existing_sha=review['existing_sha'])
        self.assertFalse((self.project/'task.py').exists())

    def test_low_disk_space_blocks_queued_process(self):
        ident=self.janus.add_approved_action(argv=[sys.executable,'--version'],
            cwd=self.project,label='Disk preflight',kind='tool',user_approved=True)
        from collections import namedtuple
        Usage=namedtuple('usage','total used free')
        with patch('janus_worker.shutil.disk_usage',return_value=Usage(100,95,5)), \
             patch('janus_worker.subprocess.Popen',side_effect=AssertionError('must not launch')):
            self.worker().execute_next_approved()
        self.assertEqual(self.janus.action(ident)['status'],'needs_attention')
        self.assertIn('disk',self.janus.action(ident)['detail'].lower())

    def test_execution_timeout_safely_ends_hanging_tool(self):
        ident=self.janus.add_approved_action(argv=[sys.executable,'-c',
            'import time; time.sleep(20)'],cwd=self.project,label='Long test',kind='tool',
            user_approved=True)
        with patch('janus_worker.MAX_TOOL_SECONDS',0.12):
            self.worker().execute_next_approved()
        self.assertEqual(self.janus.action(ident)['status'],'needs_attention')
        self.assertIn('runtime',self.janus.action(ident)['detail'])

    def test_oversized_log_does_not_count_as_success(self):
        ident=self.janus.add_approved_action(argv=[sys.executable,'-c',
            'print("x"*90000)'],cwd=self.project,label='Output budget test',kind='tool',
            user_approved=True)
        with patch('janus_worker.MAX_ACTION_LOG_BYTES',1000):
            self.worker().execute_next_approved()
        self.assertEqual(self.janus.action(ident)['status'],'needs_attention')
        self.assertIn('output',self.janus.action(ident)['detail'].lower())

    def test_legacy_janus_database_upgrades_in_place(self):
        db=self.root/'old-janus.sqlite3'
        with closing(sqlite3.connect(db)) as c, c:
            c.execute('''CREATE TABLE janus_actions (id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,kind TEXT,label TEXT,cwd TEXT,argv_json TEXT,approved_at TEXT,
                approval_source TEXT,status TEXT DEFAULT 'approved',output_file TEXT DEFAULT '',
                pid INTEGER,returncode INTEGER,cancel_requested INTEGER DEFAULT 0,
                started_at TEXT,finished_at TEXT,detail TEXT DEFAULT 'Waiting')''')
            c.execute('''INSERT INTO janus_actions(kind,label,cwd,argv_json,approved_at,
                approval_source) VALUES('tool','Old action','/tmp','["abc"]','old',
                'desktop-user-confirmation')''')
        migrated=JanusStore(db)
        self.assertEqual(migrated.action(1)['input_guards_json'],'[]')
        self.assertEqual(migrated.action(1)['status'],'approved')

    def test_unique_temp_allows_recovery_after_interrupted_write(self):
        stranded=self.project/'script.py.deepthort-tmp'
        stranded.write_text('old partial write')
        output=apply_approved_file(self.project,'script.py','print(1)\n',self.root/'backup')
        self.assertEqual(output.read_text(),'print(1)\n')
        self.assertEqual(stranded.read_text(),'old partial write')

    def test_internal_symlink_edit_rejected(self):
        real=self.project/'real.py';real.write_text('print("original")')
        link=self.project/'alias.py'
        try:link.symlink_to(real)
        except (OSError,NotImplementedError):self.skipTest('symlinks unavailable')
        with self.assertRaises(WorkspaceError):
            safe_target(self.project,'alias.py')
        with self.assertRaises(WorkspaceError):
            apply_approved_file(self.project,'alias.py','print("modified")',self.root/'backup')
        self.assertEqual(real.read_text(),'print("original")')


if __name__=='__main__':unittest.main()
