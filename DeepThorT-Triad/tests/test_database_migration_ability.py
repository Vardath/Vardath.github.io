import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from deepthort_local.database_migration import migrate,review,execute
S={'database':'old.db','from_version':0,'to_version':1,'steps':[
    {'operation':'add_nullable_column','table':'items','column':'notes','type':'TEXT'},
    {'operation':'create_index','table':'items','name':'items_notes','columns':['notes']}]}
def fixture():
    db=sqlite3.connect(':memory:')
    try:
        db.executescript('CREATE TABLE items(id INTEGER PRIMARY KEY, value TEXT); INSERT INTO items VALUES(1, "original");')
        return db.serialize()
    finally:db.close()
class MigrationTests(unittest.TestCase):
    def test_migration_and_original_values(self):
        raw=fixture();output,info=migrate(raw,S)
        db=sqlite3.connect(':memory:')
        try:
            db.deserialize(output)
            self.assertEqual(db.execute('SELECT * FROM items').fetchall(),[(1,'original',None)])
            self.assertEqual(db.execute('PRAGMA user_version').fetchone(),(1,))
            self.assertEqual(db.execute('PRAGMA index_info(items_notes)').fetchone()[2],'notes')
            self.assertEqual(info['row_counts'],{'items':1})
        finally:db.close()
    def test_version_and_destructive_step_refusal(self):
        with self.assertRaises(ValueError):migrate(fixture(),dict(S,from_version=1,to_version=2))
        with self.assertRaises(ValueError):migrate(fixture(),dict(S,steps=[{'operation':'drop_table','table':'items'}]))
        s=copy.deepcopy(S);s['steps'][0]['column']='value'
        with self.assertRaises(ValueError):migrate(fixture(),s)
    def test_exact_source_and_new_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw=fixture();source=root/'old.db';source.write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(S),encoding='utf-8')
            plan,_=review(root,'spec.json','new.db')
            self.assertTrue(execute(root,plan)['source_unchanged'])
            self.assertEqual(source.read_bytes(),raw)
            plan,_=review(root,'spec.json','later.db')
            source.write_bytes(raw+b'changed')
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'later.db').exists())
