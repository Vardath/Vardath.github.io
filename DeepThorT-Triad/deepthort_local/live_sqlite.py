"""Explicit read-only query against a live local SQLite database, no credentials/network."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.sql_query import checked,query_connection,MAX_RESULT,EXTRA
from deepthort_local.source_security import linked
from deepthort_local.pdf_diagrams import limits
SCHEMA='janus-live-sqlite-v1'
MAX_DB=16*1024*1024

def identity(path):
    st=path.stat()
    if not 100<=st.st_size<=MAX_DB or not st.st_ino:
        raise ValueError('Database exceeds bound or lacks stable file identity')
    with path.open('rb') as f:header=f.read(100)
    if not header.startswith(b'SQLite format 3\0'):raise ValueError('Not a SQLite database')
    for suffix in ('-wal','-shm','-journal'):
        side=Path(str(path)+suffix)
        if side.is_symlink() or side.exists() and (linked(side) or not side.is_file() or side.stat().st_size>MAX_DB):
            raise ValueError('Unsafe SQLite sidecar')
    # Do not initiate WAL shared-memory creation. Require an already active
    # WAL with ordinary existing sidecars or a rollback-journal database.
    if header[18:20]==b'\x02\x02' and not all(Path(str(path)+x).is_file() for x in ('-wal','-shm')):
        raise ValueError('Active WAL requires existing WAL and SHM files')
    if header[18:20] not in (b'\x01\x01',b'\x02\x02'):raise ValueError('Unknown SQLite journal format')
    return {'device':st.st_dev,'inode':st.st_ino}

def review(root,source,output,exclude=()):
    # The SQL specification stays hash-bound. The database content is
    # deliberately not hashed because the user approves a live read.
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    root=Path(root).resolve(strict=True)
    db=guard.path_for(root,s['database'],plan['exclude'],EXTRA[1],exists=True)
    plan['database_identity']=identity(db)
    return plan,dict(s,scope='Read current committed local SQLite data, not the reviewed historical bytes. No database write or remote connection.')

def validate(root,plan):
    if not isinstance(plan,dict) or 'database_identity' not in plan:raise ValueError('Missing live database identity')
    core=dict(plan);expected=core.pop('database_identity')
    s,dst,_=guard.validate(root,core,schema=SCHEMA,checked=checked,output_suffix='.json')
    db=guard.path_for(Path(root).resolve(strict=True),s['database'],core['exclude'],EXTRA[1],exists=True)
    if identity(db)!=expected:raise ValueError('Reviewed database file replaced')
    return s,dst,db

def execute(root,plan):
    s,dst,path=validate(root,plan)
    db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=1)
    try:
        db.execute('PRAGMA query_only=ON')
        db.execute('PRAGMA trusted_schema=OFF')
        db.execute('BEGIN')
        if identity(path)!=plan['database_identity']:raise ValueError('Database identity changed')
        result=query_connection(db,s)
        result.update(schema='janus-live-sqlite-result-v1',scope='Single read-only query in one SQLite transaction on current committed local data. Database contents may change between approval and execution; not an immutable source snapshot.',
                      source_snapshot_sha256=None,database_identity=plan['database_identity'],
                      query_sha256=hashlib.sha256(s['query'].encode()).hexdigest())
    finally:db.close()
    payload=json.dumps(result,ensure_ascii=True,allow_nan=False,sort_keys=True,indent=2).encode()
    if len(payload)>MAX_RESULT:raise ValueError('Result exceeds byte bound')
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'live_read_only_query_completed','output':plan['output'],'sha256':digest,
            'rows':result['row_count'],'truncated':result['truncated'],'live_database_modified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        limits();print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Live SQLite query unavailable; inspect file identity, query and journal state'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
