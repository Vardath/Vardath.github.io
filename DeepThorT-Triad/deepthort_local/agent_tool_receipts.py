"""Durable local observations, not execution authority or proof of correctness."""
from __future__ import annotations
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

class ToolReceipts:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with closing(sqlite3.connect(self.path,timeout=5)) as db,db:
            db.execute('''CREATE TABLE IF NOT EXISTS agent_tool_receipts(
                id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL,project TEXT NOT NULL,
                spec_sha TEXT NOT NULL,session TEXT NOT NULL,turn INTEGER NOT NULL,
                payload TEXT NOT NULL,sha TEXT NOT NULL,delivered INTEGER NOT NULL DEFAULT 0,
                created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
            db.execute('CREATE INDEX IF NOT EXISTS agent_receipts_job ON agent_tool_receipts(job_id,project,id)')
    def record(self,*,job_id,project,spec_sha,session,turn,request,result):
        if type(job_id) is not int or job_id<1 or type(turn) is not int or not 0<=turn<3:
            raise ValueError('Invalid tool observation binding')
        row={'job_id':job_id,'project':str(Path(project).resolve()),'spec_sha':spec_sha,
             'session':session,'turn':turn,'request':request,'result':result}
        payload=canonical(row);seal=digest(row)
        if len(payload.encode())>12000:raise ValueError('Tool receipt exceeds bound')
        with closing(sqlite3.connect(self.path,timeout=5)) as db,db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT count(*) FROM agent_tool_receipts WHERE job_id=? AND project=?',(job_id,row['project'])).fetchone()[0]>=2000:
                raise ValueError('Tool receipt quota reached; inspect existing evidence')
            return db.execute('''INSERT INTO agent_tool_receipts
                (job_id,project,spec_sha,session,turn,payload,sha) VALUES(?,?,?,?,?,?,?)''',
                (job_id,row['project'],spec_sha,session,turn,payload,seal)).lastrowid
    def delivered(self,ident):
        with closing(sqlite3.connect(self.path,timeout=5)) as db,db:
            if db.execute('UPDATE agent_tool_receipts SET delivered=1 WHERE id=?',(ident,)).rowcount!=1:
                raise ValueError('Missing tool receipt')
    def recent(self,job_id,project,limit=20):
        return self.read_recent(self.path,job_id,project,limit)
    @staticmethod
    def read_recent(path,job_id,project,limit=20,*,read_only=False):
        """Read existing sealed receipts without schema writes when requested."""
        key=str(Path(project).resolve())
        conn=(sqlite3.connect(Path(path).resolve(strict=True).as_uri()+'?mode=ro',uri=True,timeout=.05)
              if read_only else sqlite3.connect(path,timeout=5))
        with closing(conn) as db:
            rows=db.execute('''SELECT id,spec_sha,session,turn,payload,sha,delivered,created
                FROM agent_tool_receipts WHERE job_id=? AND project=? ORDER BY id DESC LIMIT ?''',
                (job_id,key,max(1,min(limit,60)))).fetchall()
        result=[]
        for ident,spec,session,turn,payload,seal,used,created in rows:
            if len(payload.encode())>12000:raise ValueError('Oversized stored tool receipt')
            row=json.loads(payload)
            if digest(row)!=seal or any(row.get(k)!=v for k,v in
                {'job_id':job_id,'project':key,'spec_sha':spec,'session':session,'turn':turn}.items()):
                raise ValueError('Tool receipt integrity check failed')
            result.append({**row,'id':ident,'sha256':seal,'delivered':bool(used),'created':created})
        return result
    def describe(self,job_id,project):
        rows=self.recent(job_id,project)
        if not rows:return ''
        lines=['Historical agent tool receipts (not current verification):']
        for row in rows:
            request=row['request'];result=row['result']
            lines.append(f"#{row['id']} {request['tool']}: {len(result['items'])} observations; "
                         +('selected for model context' if row['delivered'] else 'observed, not selected')
                         +f"; SHA256 {row['sha256'][:16]}")
        return '\n'.join(lines)
