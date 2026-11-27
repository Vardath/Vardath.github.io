import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from deepthort_local.database_schema import review,execute,checked

class DatabaseSchemaTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.source=self.root/'schema.json'
        def col(n,t='INTEGER',nullable=False):return {'name':n,'type':t,'nullable':nullable}
        self.spec={'tables':[{'name':'parent','columns':[col('id'),col('code','TEXT')],'primary_key':['id'],'unique':[['code']],'foreign_keys':[]},
                            {'name':'child','columns':[col('id'),col('parent_id')],'primary_key':['id'],'unique':[],
                             'foreign_keys':[{'columns':['parent_id'],'table':'parent','references':['id']}]}]}
        self.save()
    def save(self):self.source.write_text(json.dumps(self.spec),encoding='utf-8')
    def test_actual_constraints(self):
        plan,_=review(self.root,'schema.json','schema.sql');receipt=execute(self.root,plan)
        self.assertEqual(receipt['tables'],2);self.assertFalse(receipt['live_database_modified'])
        db=sqlite3.connect(':memory:');self.addCleanup(db.close)
        db.executescript((self.root/'schema.sql').read_text('utf-8'))
        with self.assertRaises(sqlite3.IntegrityError):db.execute('INSERT INTO child VALUES(1,99)')
        db.execute("INSERT INTO parent VALUES(1,'A')")
        db.execute('INSERT INTO child VALUES(1,1)')
        with self.assertRaises(sqlite3.IntegrityError):db.execute("INSERT INTO parent VALUES(2,'A')")
    def test_invalid_reference_and_identifier(self):
        self.spec['tables'][1]['foreign_keys'][0]['references']=['missing']
        with self.assertRaises(ValueError):checked(self.spec)
        self.spec['tables'][1]['foreign_keys'][0]['references']=['id']
        self.spec['tables'][0]['name']='x; DROP TABLE child'
        with self.assertRaises(ValueError):checked(self.spec)
    def test_stale_and_existing_output(self):
        plan,_=review(self.root,'schema.json','schema.sql')
        out=self.root/'schema.sql';out.write_text('keep',encoding='utf-8')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_text('utf-8'),'keep')
        out.unlink();self.source.write_text('{}',encoding='utf-8')
        with self.assertRaises(ValueError):execute(self.root,plan)
    def test_nullable_primary_and_exclusion(self):
        with self.assertRaises(ValueError):review(self.root,'schema.json','schema.sql',['schema.json'])
        self.spec['tables'][0]['columns'][0]['nullable']=True
        with self.assertRaises(ValueError):checked(self.spec)
