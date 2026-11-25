"""Structured verification intents. An intent is never a grant or command.

The ordinary scheduler remains the only dispatcher. Requests are advisory and
may be coalesced; existing automatic verification is not made dependent on AI.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from .project_authority import _plan_digest,authorize_test
from .reasoning_council import sha

def encode(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def binding(job,steps,original):
    if job.get('mode')!='build' or type(job.get('id')) is not int or job['id']<1:
        raise ValueError('Only a bound build can request verification')
    return {'job_id':job['id'],'project':str(Path(job['project']).resolve(strict=True)),
            'plan_sha256':_plan_digest(job,steps),'spec_sha256':sha(original)}

class ExecutionIntents:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with closing(sqlite3.connect(self.path,timeout=5)) as db,db:
            db.execute('''CREATE TABLE IF NOT EXISTS verification_intents(
                id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL,project TEXT NOT NULL,
                binding TEXT NOT NULL,origin TEXT NOT NULL,phase TEXT NOT NULL,
                attempt INTEGER,argv_sha256 TEXT,result TEXT,
                created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
            db.execute('CREATE INDEX IF NOT EXISTS verification_intents_job ON verification_intents(job_id,project,id)')
            # An interrupted dispatch must not be replayed from this store.
            db.execute("UPDATE verification_intents SET phase='interrupted' WHERE phase='claimed'")
    def request(self,job,steps,original,*,enabled):
        if not enabled or job.get('state')!='running':raise ValueError('No active approved development operation')
        identity=binding(job,steps,original)
        payload=encode(identity)
        with closing(sqlite3.connect(self.path,timeout=5)) as db,db:
            db.execute('BEGIN IMMEDIATE')
            old=db.execute("SELECT id,binding FROM verification_intents WHERE job_id=? AND project=? AND phase='pending' ORDER BY id DESC LIMIT 1",
                           (job['id'],identity['project'])).fetchone()
            if old:
                if old[1]!=payload:raise ValueError('An obsolete verification intent requires reconciliation')
                return old[0]
            return db.execute("INSERT INTO verification_intents(job_id,project,binding,origin,phase) VALUES(?,?,?,'JANUS','pending')",
                (job['id'],identity['project'],payload)).lastrowid
    def claim(self,job,steps,original,argv,*,grant_folder,enabled,attempt):
        """Called only at the existing authorized scheduler dispatch boundary."""
        if type(attempt) is not int or attempt<1:raise ValueError('Invalid test attempt')
        identity=binding(job,steps,original)
        with closing(sqlite3.connect(self.path,timeout=5)) as db,db:
            db.execute('BEGIN IMMEDIATE')
            rows=db.execute("SELECT id,binding FROM verification_intents WHERE job_id=? AND project=? AND phase='pending' ORDER BY id",
                            (job['id'],identity['project'])).fetchall()
            if not rows:return None
            valid=[]
            for ident,payload in rows:
                if payload!=encode(identity):
                    db.execute("UPDATE verification_intents SET phase='stale' WHERE id=?",(ident,))
                else:valid.append(ident)
            if not valid:return None
            authorize_test(grant_folder,job,steps,list(argv),enabled=enabled)
            chosen=valid[0]
            for ident in valid[1:]:
                db.execute("UPDATE verification_intents SET phase='coalesced' WHERE id=?",(ident,))
            db.execute("UPDATE verification_intents SET phase='claimed',attempt=?,argv_sha256=? WHERE id=?",
                       (attempt,sha(encode(list(argv))),chosen))
            return chosen
    def finish(self,ident,*,job_id,phase,exit_code=None,assurance='',evidence_sha=None):
        if phase not in ('passed','failed','interrupted','blocked'):raise ValueError('Invalid verification result')
        if phase=='passed' and (exit_code!=0 or not isinstance(evidence_sha,str) or len(evidence_sha)!=64):
            raise ValueError('A passing intent requires observed verification evidence')
        result=encode({'exit_code':exit_code,'assurance':assurance,'evidence_sha256':evidence_sha})
        with closing(sqlite3.connect(self.path,timeout=5)) as db,db:
            if db.execute("UPDATE verification_intents SET phase=?,result=? WHERE id=? AND job_id=? AND phase='claimed'",
                          (phase,result,ident,job_id)).rowcount!=1:raise ValueError('No matching claimed intent')
    def recent(self,job_id,project):
        with closing(sqlite3.connect(self.path,timeout=5)) as db:
            db.row_factory=sqlite3.Row
            return [dict(r) for r in db.execute("SELECT id,phase,attempt,argv_sha256,result FROM verification_intents WHERE job_id=? AND project=? ORDER BY id DESC LIMIT 20",
                        (job_id,str(Path(project).resolve())))]
    def describe(self,job_id,project):
        rows=self.recent(job_id,project)
        return '\n'.join(f"#{r['id']} verify_project: {r['phase']}"+(f" (attempt {r['attempt']})" if r['attempt'] else '') for r in rows)
