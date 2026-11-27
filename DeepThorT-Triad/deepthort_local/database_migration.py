"""Reviewed additive SQLite migrations on disposable standalone snapshots."""
from __future__ import annotations
import argparse
import json
import sqlite3
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.database_schema import name,quote,TYPES
from deepthort_local.sql_query import EXTRA,snapshot_bytes
from deepthort_local.pdf_diagrams import limits
SCHEMA='janus-database-migration-v1'
MAX_STEPS=16
def checked(s):
    if not isinstance(s,dict) or set(s)!={'database','from_version','to_version','steps'} or not isinstance(s['database'],str):
        raise ValueError('Expected database, versions and typed steps')
    old,new=s['from_version'],s['to_version']
    if type(old) is not int or type(new) is not int or not 0<=old<new<=2147483647 or new!=old+1:
        raise ValueError('Migration version must increment by exactly one')
    if not isinstance(s['steps'],list) or not 1<=len(s['steps'])<=MAX_STEPS:raise ValueError('Choose 1–16 additive steps')
    for step in s['steps']:
        if not isinstance(step,dict):raise ValueError('Invalid migration step')
        if step.get('operation')=='add_nullable_column':
            if set(step)!={'operation','table','column','type'} or step['type'] not in TYPES:
                raise ValueError('Expected typed nullable column')
            name(step['table']);name(step['column'])
        elif step.get('operation')=='create_index':
            if set(step)!={'operation','table','name','columns'} or not isinstance(step['columns'],list) or not 1<=len(step['columns'])<=8:
                raise ValueError('Expected nonunique index definition')
            name(step['table']);name(step['name'])
            cols=[name(x) for x in step['columns']]
            if len({x.casefold() for x in cols})!=len(cols):raise ValueError('Duplicate index column')
        else:raise ValueError('Only additive nullable column and nonunique index steps supported')
    return s
def tables(db):
    items=list(db.execute('PRAGMA main.table_list'))
    if any(r[2]!='table' for r in items if r[0]=='main' and not r[1].startswith('sqlite_')):
        raise ValueError('Views, virtual and shadow tables unsupported')
    if db.execute("SELECT 1 FROM sqlite_schema WHERE type='trigger' LIMIT 1").fetchone():
        raise ValueError('Triggers unsupported in migration snapshots')
    result={}
    for r in items:
        if r[0]!='main' or r[1].startswith('sqlite_'):continue
        table=name(r[1])
        cols=list(db.execute('PRAGMA table_xinfo('+quote(table)+')'))
        if any(c[6]!=0 for c in cols):raise ValueError('Generated or hidden columns unsupported')
        for c in cols:name(c[1])
        result[table]=cols
    if not 1<=len(result)<=64:raise ValueError('Unsupported table count')
    return result
def integrity(db):
    if db.execute('PRAGMA integrity_check').fetchall()!=[('ok',)] or db.execute('PRAGMA foreign_key_check').fetchone() is not None:
        raise ValueError('Database integrity or foreign-key check failed')
def migrate(raw,s):
    checked(s)
    db=sqlite3.connect(':memory:')
    try:
        db.deserialize(raw);db.execute('PRAGMA trusted_schema=OFF');db.execute('PRAGMA foreign_keys=ON')
        if db.execute('PRAGMA user_version').fetchone()!=(s['from_version'],):raise ValueError('Source version mismatch')
        before=tables(db);integrity(db)
        counts={t:db.execute('SELECT COUNT(*) FROM '+quote(t)).fetchone()[0] for t in before}
        expected={k:list(v) for k,v in before.items()}
        db.execute('BEGIN')
        for step in s['steps']:
            table=step['table'];cols=expected.get(table)
            if cols is None:raise ValueError('Unknown exact table')
            existing={c[1].casefold() for c in cols}
            if step['operation']=='add_nullable_column':
                column=step['column']
                if column.casefold() in existing:raise ValueError('Column already exists')
                db.execute('ALTER TABLE '+quote(table)+' ADD COLUMN '+quote(column)+' '+step['type'])
                cols.append((len(cols),column,step['type'],0,None,0,0))
            else:
                if any(c not in {v[1] for v in cols} for c in step['columns']):raise ValueError('Unknown exact index column')
                db.execute('CREATE INDEX '+quote(step['name'])+' ON '+quote(table)+' ('+', '.join(map(quote,step['columns']))+')')
                found=list(db.execute('PRAGMA index_info('+quote(step['name'])+')'))
                if [v[2] for v in found]!=step['columns']:raise ValueError('Index verification failed')
        db.execute('PRAGMA user_version='+str(s['to_version']))
        if tables(db)!=expected or any(db.execute('SELECT COUNT(*) FROM '+quote(t)).fetchone()[0]!=n for t,n in counts.items()):
            raise ValueError('Schema or row count preservation failed')
        for step in s['steps']:
            if step['operation']=='add_nullable_column' and db.execute('SELECT 1 FROM '+quote(step['table'])+' WHERE '+quote(step['column'])+' IS NOT NULL LIMIT 1').fetchone():
                raise ValueError('New nullable column unexpectedly contains values')
        integrity(db);db.commit()
        payload=db.serialize()
    finally:db.close()
    if not payload or len(payload)>guard.MAX_OUTPUT:raise ValueError('Migrated snapshot exceeds bound')
    verify=sqlite3.connect(':memory:')
    try:
        verify.deserialize(payload);verify.execute('PRAGMA trusted_schema=OFF')
        integrity(verify)
        if verify.execute('PRAGMA user_version').fetchone()!=(s['to_version'],) or tables(verify)!=expected:
            raise ValueError('Serialized migration verification failed')
    finally:verify.close()
    return payload,{'row_counts':counts,'from_version':s['from_version'],'to_version':s['to_version'],'steps':len(s['steps'])}
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.db',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.db',extra=EXTRA)
    _,_,path=validate(root,plan);snapshot_bytes(path,plan['guards'][1])
    return plan,dict(s,scope='Migrate a disposable snapshot to a new DB file; preserve original for rollback.')
def execute(root,plan):
    s,dst,src=validate(root,plan);raw=snapshot_bytes(src,plan['guards'][1]);payload,receipt=migrate(raw,s)
    def recheck():
        _,_,path=validate(root,plan);snapshot_bytes(path,plan['guards'][1])
    digest=guard.publish(payload,dst,recheck)
    return {'status':'additive_migration_snapshot_verified','output':plan['output'],'sha256':digest,
            'source_unchanged':True,'live_database_modified':False,'application_semantics_verified':False,**receipt}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        limits();print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Migration unavailable; inspect snapshot, version and additive steps'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
