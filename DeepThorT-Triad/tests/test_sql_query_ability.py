import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from deepthort_local.sql_query import review,execute

class SQLQueryTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.db=self.root/'sample.db';self.spec=self.root/'query.json'
        conn=sqlite3.connect(self.db)
        try:
            conn.executescript("CREATE TABLE items(id INTEGER, name TEXT, qty INTEGER); INSERT INTO items VALUES(1,'A',3),(2,'B',4),(3,'A',5); CREATE VIEW hidden AS SELECT * FROM items;")
        finally:conn.close()
        self.data={'database':'sample.db','query':'SELECT name, SUM(qty) AS total FROM items WHERE qty >= ? GROUP BY name ORDER BY name','parameters':[3],'max_rows':10}
        self.save()
    def save(self):self.spec.write_text(json.dumps(self.data),encoding='utf-8')
    def run_query(self):
        plan,_=review(self.root,'query.json','out.json');return execute(self.root,plan)
    def test_actual_aggregate_and_source_preservation(self):
        raw=self.db.read_bytes();r=self.run_query()
        data=json.loads((self.root/'out.json').read_text('utf-8'))
        self.assertEqual(data['columns'],['name','total']);self.assertEqual(data['rows'],[['A',8],['B',4]])
        self.assertFalse(r['truncated']);self.assertEqual(self.db.read_bytes(),raw)
    def test_truncation_and_parameters(self):
        self.data.update(query='SELECT id FROM items ORDER BY id',parameters=[],max_rows=2);self.save()
        r=self.run_query();self.assertTrue(r['truncated']);self.assertEqual(r['rows'],2)
    def test_write_extension_view_and_multiple_statements_refused(self):
        for sql in ("WITH x AS (SELECT 1) DELETE FROM items","SELECT load_extension('x')","SELECT * FROM hidden","SELECT 1; SELECT 2"):
            self.data.update(query=sql,parameters=[]);self.save()
            with self.assertRaises((ValueError,sqlite3.Error)):self.run_query()
        self.assertFalse((self.root/'out.json').exists())
    def test_stale_output_and_sidecar(self):
        plan,_=review(self.root,'query.json','out.json')
        side=Path(str(self.db)+'-wal');side.write_bytes(b'pending')
        with self.assertRaises(ValueError):execute(self.root,plan)
        side.unlink();out=self.root/'out.json';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink()
        self.db.write_bytes(b'changed')
        with self.assertRaises(ValueError):execute(self.root,plan)
