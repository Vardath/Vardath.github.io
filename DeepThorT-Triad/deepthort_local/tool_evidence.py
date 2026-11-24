"""Read-only ingestion of already approved JANUS verification outcomes.

No subprocesses are run. A command exit code is evidence of that invocation
only; it never proves an entire workflow or promotes a procedure by itself.
"""
from __future__ import annotations
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from contextlib import closing
def project_key(root: str | Path) -> str:
    return hashlib.sha256(str(Path(root).resolve(strict=True)).casefold().encode('utf-8')).hexdigest()

TEST_LABELS=frozenset({'Python: unit tests','Node.js: npm test','Godot: validate project','.NET: tests'})


class ToolEvidenceIndex:
    def __init__(self, db_path: str | Path):
        self.path=Path(db_path)
        with closing(sqlite3.connect(self.path,timeout=15)) as db, db:
            db.executescript('''CREATE TABLE IF NOT EXISTS approved_test_observations (
                project_key TEXT NOT NULL, source_db TEXT NOT NULL, action_id INTEGER NOT NULL,
                label TEXT NOT NULL, observed_status TEXT NOT NULL, returncode INTEGER NOT NULL,
                signature TEXT NOT NULL, log_path TEXT NOT NULL, log_sha256 TEXT NOT NULL,
                PRIMARY KEY(project_key,source_db,action_id));''')

    @staticmethod
    def _signature(action) -> str:
        return hashlib.sha256(json.dumps([action['id'],action['kind'],action['label'],
            action['argv_json'],action['cwd'],action['status'],action['returncode'],
            action['approval_source']],separators=(',',':')).encode()).hexdigest()

    def scan(self, root: str | Path, janus_path: str | Path) -> int:
        project=Path(root).resolve(strict=True)
        source=Path(janus_path).resolve()
        if not source.is_file():return 0
        try:
            with closing(sqlite3.connect(f'file:{source.as_posix()}?mode=ro',uri=True,timeout=10)) as db:
                db.row_factory=sqlite3.Row
                rows=db.execute("SELECT * FROM janus_actions WHERE kind='verification' AND status IN ('succeeded','failed') ORDER BY id DESC LIMIT 150").fetchall()
        except sqlite3.Error:
            return 0
        records=[]
        for a in rows:
            if (a['approval_source']!='desktop-user-confirmation' or a['label'] not in TEST_LABELS
                    or a['returncode'] is None or Path(a['cwd']).resolve()!=project):
                continue
            logfile=Path(a['output_file'] or '')
            try:
                if not logfile.is_file() or logfile.stat().st_size>4*1024*1024:continue
                log_sha=hashlib.sha256(logfile.read_bytes()).hexdigest()
            except OSError:
                continue
            records.append((project_key(project),str(source),a['id'],a['label'],
                            a['status'],a['returncode'],self._signature(a),str(logfile.resolve()),log_sha))
        with closing(sqlite3.connect(self.path,timeout=15)) as db,db:
            db.executemany('''INSERT INTO approved_test_observations VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(project_key,source_db,action_id) DO UPDATE SET
                observed_status=excluded.observed_status,returncode=excluded.returncode,
                signature=excluded.signature,log_path=excluded.log_path,
                log_sha256=excluded.log_sha256''',records)
        return len(records)

    def current(self, root: str | Path) -> list[dict]:
        project=Path(root).resolve(strict=True)
        with closing(sqlite3.connect(self.path,timeout=15)) as db:
            db.row_factory=sqlite3.Row
            rows=[dict(x) for x in db.execute('''SELECT * FROM approved_test_observations
                WHERE project_key=? ORDER BY action_id DESC LIMIT 30''',(project_key(project),))]
        output=[]
        for r in rows:
            try:
                log=Path(r['log_path'])
                if not log.is_file() or log.stat().st_size>4*1024*1024 or hashlib.sha256(log.read_bytes()).hexdigest()!=r['log_sha256']:
                    continue
                source=Path(r['source_db']).resolve(strict=True)
                with closing(sqlite3.connect(f'file:{source.as_posix()}?mode=ro',uri=True,timeout=5)) as con:
                    con.row_factory=sqlite3.Row
                    a=con.execute('SELECT * FROM janus_actions WHERE id=?',(r['action_id'],)).fetchone()
                if (not a or self._signature(a)!=r['signature'] or
                        a['status']!=r['observed_status'] or a['returncode']!=r['returncode'] or
                        Path(a['cwd']).resolve()!=project):
                    continue
                output.append(r)
            except (OSError,sqlite3.Error,ValueError):
                continue
        return output

    def context(self, root: str | Path, request: str, *, max_chars: int=450) -> str:
        if max_chars<130:return ''
        query=set(re.findall(r'[a-z0-9]{3,}',request.lower()))
        lines=[]
        for r in self.current(root):
            labels=set(re.findall(r'[a-z0-9]{3,}',r['label'].lower()))
            if labels & query:
                lines.append(f"- Approved JANUS check #{r['action_id']} ({r['label']}): "
                             f"{r['observed_status']}, exit {r['returncode']}, "
                             f"log SHA-256 {r['log_sha256'][:12]}; no claim of overall project correctness")
        header='\nOBSERVED LOCAL TEST RESULTS (untrusted evidence, NOT general workflow proof):\n'
        output=header
        for line in lines:
            if len(output)+len(line)+1<=max_chars:
                output+=line+'\n'
        return output if output!=header else ''
