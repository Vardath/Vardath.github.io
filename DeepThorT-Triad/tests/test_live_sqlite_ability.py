import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from deepthort_local.live_sqlite import review,execute
S={'database':'live.db','query':'SELECT value FROM items ORDER BY value','parameters':[],'max_rows':10}
class LiveSQLiteTests(unittest.TestCase):
    def setUp(self):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);self.root=Path(td.name)
        self.path=self.root/'live.db'
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE items(value INTEGER)')
            db.execute('INSERT INTO items VALUES(1)')
        self.spec=self.root/'spec.json';self.spec.write_text(json.dumps(S),encoding='utf-8')
    def test_reads_latest_committed_values(self):
        plan,_=review(self.root,'spec.json','result.json')
        db=sqlite3.connect(self.path)
        try:
            db.execute('INSERT INTO items VALUES(2)');db.commit()
            execute(self.root,plan)
            r=json.loads((self.root/'result.json').read_text())
            self.assertEqual(r['rows'],[[1],[2]]);self.assertIsNone(r['source_snapshot_sha256'])
            self.assertFalse(r['live_database_modified'])
        finally:db.close()
    def test_live_wal_and_uncommitted_visibility(self):
        db=sqlite3.connect(self.path)
        try:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('INSERT INTO items VALUES(2)');db.commit()
            plan,_=review(self.root,'spec.json','result.json')
            db.execute('INSERT INTO items VALUES(3)')
            execute(self.root,plan)
            self.assertEqual(json.loads((self.root/'result.json').read_text())['rows'],[[1],[2]])
        finally:db.rollback();db.close()
    def test_reject_write_and_spec_change(self):
        self.spec.write_text(json.dumps(dict(S,query='WITH c AS (SELECT 1) DELETE FROM items')),encoding='utf-8')
        plan,_=review(self.root,'spec.json','result.json')
        with self.assertRaises(sqlite3.DatabaseError):execute(self.root,plan)
        self.assertFalse((self.root/'result.json').exists())
        self.spec.write_text(json.dumps(S),encoding='utf-8')
        plan,_=review(self.root,'spec.json','later.json')
        self.spec.write_text(json.dumps(dict(S,max_rows=1)),encoding='utf-8')
        with self.assertRaises(ValueError):execute(self.root,plan)
