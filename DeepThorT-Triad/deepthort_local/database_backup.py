"""Reviewed exact standalone SQLite database backup into a verified archive."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import time
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.sql_query import EXTRA,snapshot_bytes
from deepthort_local.structured_source import strict_json

SCHEMA='janus-database-backup-v1'
MAX_DB=guard.MAX_INPUT-65536

def checked(s):
    if not isinstance(s,dict) or set(s)!={'database'} or not isinstance(s['database'],str):
        raise ValueError('Expected one standalone SQLite database')
    return s

def integrity(raw):
    if not 100<=len(raw)<=MAX_DB or raw[:16]!=b'SQLite format 3\x00' or raw[18:20]!=b'\x01\x01':
        raise ValueError('Expected bounded standalone non-WAL SQLite database')
    db=sqlite3.connect(':memory:')
    try:
        db.deserialize(raw)
        db.execute('PRAGMA trusted_schema=OFF')
        db.execute('PRAGMA query_only=ON')
        db.enable_load_extension(False)
        deadline=time.monotonic()+5
        db.set_progress_handler(lambda:int(time.monotonic()>=deadline),1000)
        if db.execute('PRAGMA quick_check(1)').fetchall()!=[('ok',)]:
            raise ValueError('SQLite integrity check failed')
        return {'user_version':db.execute('PRAGMA user_version').fetchone()[0],
                'page_count':db.execute('PRAGMA page_count').fetchone()[0]}
    finally:db.close()

def sha(raw):return hashlib.sha256(raw).hexdigest()

def unpack(raw):
    if not 1<=len(raw)<=guard.MAX_INPUT:raise ValueError('Archive exceeds bound')
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            entries=z.infolist()
            if len(entries)!=2 or {i.filename for i in entries}!={'database.sqlite3','manifest.json'} or any(i.flag_bits&1 for i in entries):
                raise ValueError('Invalid backup member set')
            if not 100<=z.getinfo('database.sqlite3').file_size<=MAX_DB or not 1<=z.getinfo('manifest.json').file_size<=4096:
                raise ValueError('Backup member exceeds bound')
            db=z.read('database.sqlite3');manifest=strict_json(z.read('manifest.json').decode('utf-8'))
    except (zipfile.BadZipFile,RuntimeError,NotImplementedError) as exc:raise ValueError('Invalid backup archive') from exc
    expected={'schema':SCHEMA,'database_sha256':sha(db),'database_bytes':len(db),**integrity(db)}
    if manifest!=expected:raise ValueError('Backup integrity manifest mismatch')
    return db,expected

def pack(raw):
    metadata={'schema':SCHEMA,'database_sha256':sha(raw),'database_bytes':len(raw),**integrity(raw)}
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for name,payload in [('database.sqlite3',raw),('manifest.json',json.dumps(metadata,sort_keys=True).encode())]:
            entry=zipfile.ZipInfo(name,(1980,1,1,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(entry,payload)
    payload=out.getvalue()
    if unpack(payload)!=(raw,metadata):raise ValueError('Backup roundtrip failed')
    return payload,metadata

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
    _,_,p=validate(root,plan);raw=snapshot_bytes(p,plan['guards'][1]);meta=integrity(raw)
    return plan,dict(s,observations=meta,scope='Backup one closed standalone SQLite project database to a new local ZIP, preserving exact bytes and verifying restoration. Contains private database contents; not encrypted. No live database, scheduling or app-wide backup.')
def execute(root,plan):
    s,dst,src=validate(root,plan);raw=snapshot_bytes(src,plan['guards'][1]);payload,meta=pack(raw)
    def recheck():
        _,_,p=validate(root,plan);snapshot_bytes(p,plan['guards'][1])
    digest=guard.publish(payload,dst,recheck)
    return {'status':'database_backup_verified','output':plan['output'],'sha256':digest,
            'source_unchanged':True,'encrypted':False,'restore_roundtrip_verified':True,**meta}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Backup refused; use a closed standalone database and sufficient storage'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
