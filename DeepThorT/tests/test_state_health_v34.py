"""v34 diagnostics: corrupt state must be reported without leaking database data."""
from __future__ import annotations
from contextlib import closing
import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
from deepthort_local.state_health import inspect_state
from deepthort_local.flight_recorder import export_diagnostics


class HealthTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name);self.state=self.root/'state';self.state.mkdir()
    def test_valid_database_does_not_leak_rows(self):
        database=self.state/'janus.sqlite3'
        with closing(sqlite3.connect(database)) as conn, conn:
            conn.execute('CREATE TABLE private (secret TEXT)')
            conn.execute('INSERT INTO private VALUES (?)',('very_sensitive_chat_content',))
        info=inspect_state(self.state)
        self.assertEqual(info['databases_checked'],1)
        self.assertEqual(info['databases'][0]['quick_check'],'ok')
        dest=self.root/'diag.zip'
        export_diagnostics(self.state,dest)
        with zipfile.ZipFile(dest) as archive:
            payload=archive.read('summary.json').decode()
        self.assertIn('state_health',payload)
        self.assertNotIn('very_sensitive_chat_content',payload)
    def test_corrupt_database_is_reported_not_repaired(self):
        path=self.state/'broken.sqlite3'
        initial=b'not a sqlite database'+b'0'*100
        path.write_bytes(initial)
        info=inspect_state(self.state)
        self.assertEqual(info['databases'][0]['quick_check'],'error_or_locked')
        self.assertEqual(path.read_bytes(),initial)
        self.assertTrue(info['issues'])
    def test_missing_folder(self):
        info=inspect_state(self.root/'missing')
        self.assertIn('Local state folder missing',info['issues'])


if __name__=='__main__':unittest.main()
