"""Reviewed bounded SQLite SELECT queries against a disposable immutable byte snapshot."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard

SCHEMA='janus-sql-query-v1'
EXTRA=('database',{'.sqlite','.sqlite3','.db'})
MAX_ROWS=5000
MAX_RESULT=4*1024*1024
MAX_STEPS=2_000_000
FUNCTIONS={'abs','avg','coalesce','count','glob','hex','ifnull','instr','length','like','lower','ltrim','max','min',
           'nullif','replace','round','rtrim','substr','substring','sum','total','trim','typeof','upper'}

def scalar(value):
    if value is None or type(value) is bool:return value
    if type(value) is int and -(2**63)<=value<2**63:return value
    if type(value) is float and math.isfinite(value):return value
    if isinstance(value,str) and len(value)<=32768 and '\0' not in value:return value
    raise ValueError('Unsupported SQL parameter')

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'database','query','parameters','max_rows'} or not isinstance(spec['database'],str):
        raise ValueError('Expected database, query, parameters and max_rows')
    q=spec['query']
    if not isinstance(q,str) or not 1<=len(q)<=8000 or '\0' in q or not re.match(r'^\s*(SELECT|WITH)\b',q,re.I):
        raise ValueError('Only reviewed SELECT or WITH queries supported')
    if not isinstance(spec['parameters'],list) or len(spec['parameters'])>64 or type(spec['max_rows']) is not int or not 1<=spec['max_rows']<=MAX_ROWS:
        raise ValueError('Invalid parameters or result row bound')
    return {'database':spec['database'],'query':q,'parameters':[scalar(x) for x in spec['parameters']],'max_rows':spec['max_rows']}

def no_sidecars(path):
    for suffix in ('-wal','-shm','-journal'):
        side=Path(str(path)+suffix)
        if side.exists() or side.is_symlink():raise ValueError('Use a standalone SQLite backup without WAL or journal files')

def snapshot_bytes(path,record):
    no_sidecars(path);raw=guard.exact(path,record,guard.MAX_INPUT);no_sidecars(path)
    if len(raw)<100 or not raw.startswith(b'SQLite format 3\0') or raw[18:20]!=b'\x01\x01':
        raise ValueError('Use a complete non-WAL SQLite database snapshot')
    return raw

def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    _,_,db=guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    snapshot_bytes(db,plan['guards'][1])
    return plan,spec
def validate(root,plan):
    spec,dst,db=guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    no_sidecars(db)
    return spec,dst,db

def result_value(v):
    if v is None or type(v) in (int,str):return v
    if type(v) is float and math.isfinite(v):return v
    if isinstance(v,bytes) and len(v)<=32768:return {'encoding':'base64','value':base64.b64encode(v).decode('ascii')}
    raise ValueError('Unsupported or oversized SQL result value')

def query(raw,spec):
    db=sqlite3.connect(':memory:')
    try:
        if not hasattr(db,'deserialize'):raise ValueError('SQLite deserialize unavailable in installed Python')
        db.deserialize(raw)
        return query_connection(db,spec)
    finally:db.close()

def query_connection(db,spec):
        db.execute('PRAGMA trusted_schema=OFF')
        db.execute('PRAGMA query_only=ON')
        if db.execute('PRAGMA query_only').fetchone()!=(1,) or db.execute('PRAGMA trusted_schema').fetchone()!=(0,):
            raise ValueError('Required SQLite restrictions unavailable')
        if hasattr(db,'enable_load_extension'):db.enable_load_extension(False)
        # Reject views, virtual/shadow tables and internal metadata as query
        # sources; read only ordinary tables in the disposable main database.
        allowed={row[1] for row in db.execute('PRAGMA main.table_list') if row[0]=='main' and row[2]=='table' and not row[1].startswith('sqlite_')}
        for code,val in ((sqlite3.SQLITE_LIMIT_LENGTH,1_000_000),(sqlite3.SQLITE_LIMIT_SQL_LENGTH,8000),
                         (sqlite3.SQLITE_LIMIT_COLUMN,128),(sqlite3.SQLITE_LIMIT_EXPR_DEPTH,50),
                         (sqlite3.SQLITE_LIMIT_COMPOUND_SELECT,16),(sqlite3.SQLITE_LIMIT_ATTACHED,0),
                         (sqlite3.SQLITE_LIMIT_VDBE_OP,100000)):
            db.setlimit(code,val)
        start=time.monotonic();steps=[0]
        def progress():
            steps[0]+=1000
            return int(steps[0]>MAX_STEPS or time.monotonic()-start>15)
        db.set_progress_handler(progress,1000)
        def authorize(action,a,b,database,origin):
            if origin:return sqlite3.SQLITE_DENY
            if action==sqlite3.SQLITE_SELECT:return sqlite3.SQLITE_OK
            if action==sqlite3.SQLITE_READ and a in allowed and database=='main':return sqlite3.SQLITE_OK
            if action==sqlite3.SQLITE_FUNCTION and isinstance(b,str) and b.casefold() in FUNCTIONS:return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY
        db.set_authorizer(authorize)
        cursor=db.execute(spec['query'],spec['parameters'])
        columns=[entry[0] for entry in cursor.description or ()]
        if not 1<=len(columns)<=128 or any(not c or len(c)>256 for c in columns) or len({c.casefold() for c in columns})!=len(columns):
            raise ValueError('Use distinct bounded result column aliases')
        rows=[];used=0;truncated=False
        for row in cursor:
            if len(rows)>=spec['max_rows']:truncated=True;break
            clean=[result_value(v) for v in row]
            size=len(json.dumps(clean,ensure_ascii=True,allow_nan=False))
            used+=size
            if used>MAX_RESULT:raise ValueError('SQL result exceeds output budget')
            rows.append(clean)
        return {'columns':columns,'rows':rows,'row_count':len(rows),'truncated':truncated,
                'scope':'Single read-only query on exact standalone SQLite byte snapshot; no source writes, extensions, external databases, views or virtual tables.',
                'live_database_modified':False}
    

def execute(root,plan):
    spec,dst,source=validate(root,plan)
    raw=snapshot_bytes(source,plan['guards'][1])
    result=query(raw,spec)
    result.update(schema='janus-sql-query-data-v1',source_sha256=plan['guards'][1]['expected'],
                  query_sha256=hashlib.sha256(spec['query'].encode('utf-8')).hexdigest())
    payload=(json.dumps(result,ensure_ascii=True,indent=2,allow_nan=False)+'\n').encode('utf-8')
    if len(payload)>MAX_RESULT or json.loads(payload)!=result:raise ValueError('SQL output exceeds bound')
    def recheck():
        _,_,path=validate(root,plan);snapshot_bytes(path,plan['guards'][1])
    sha=guard.publish(payload,dst,recheck)
    return {'schema':'janus-sql-query-result-v1','status':'query_executed','output':plan['output'],'sha256':sha,
            'rows':result['row_count'],'truncated':result['truncated'],'source_unchanged':True,'live_database_modified':False}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--plan',required=True);args=parser.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2)
            resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(args.root,json.loads(args.plan)),sort_keys=True),flush=True);return 0
    except Exception as exc:
        print(json.dumps({'status':'blocked','error_type':type(exc).__name__,'reason':'Query unavailable; inspect reviewed query, standalone snapshot and restrictions'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
