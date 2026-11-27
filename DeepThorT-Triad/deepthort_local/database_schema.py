"""Generate and validate a typed SQLite schema without touching a live database."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sqlite3
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard

SCHEMA='janus-database-schema-v1'
TYPES={'INTEGER','REAL','TEXT','BLOB','NUMERIC'}
def name(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,62}',value) or value.casefold().startswith('sqlite_'):
        raise ValueError('Invalid or reserved SQLite identifier')
    return value

def names(values,columns,*,empty=False):
    if not isinstance(values,list) or (not empty and not values) or len(values)>16:
        raise ValueError('Invalid key column list')
    result=[name(x) for x in values]
    if len(set(result))!=len(result) or any(x not in columns for x in result):
        raise ValueError('Duplicate or unknown key column')
    return result

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'tables'} or not isinstance(spec['tables'],list) or not 1<=len(spec['tables'])<=32:
        raise ValueError('Expected 1 to 32 table definitions')
    tables=[];seen=set()
    for t in spec['tables']:
        if not isinstance(t,dict) or set(t)!={'name','columns','primary_key','foreign_keys','unique'}:
            raise ValueError('Expected name, columns, primary_key, foreign_keys and unique')
        title=name(t['name'])
        if title.casefold() in seen:raise ValueError('Duplicate table name')
        seen.add(title.casefold())
        if not isinstance(t['columns'],list) or not 1<=len(t['columns'])<=64:
            raise ValueError('Invalid column count')
        cols=[];keys=set()
        for c in t['columns']:
            if not isinstance(c,dict) or set(c)!={'name','type','nullable'} or c['type'] not in TYPES or type(c['nullable']) is not bool:
                raise ValueError('Invalid typed column')
            n=name(c['name'])
            if n.casefold() in keys:raise ValueError('Duplicate column name')
            keys.add(n.casefold());cols.append(dict(c))
        colnames={c['name'] for c in cols}
        primary=names(t['primary_key'],colnames,empty=True)
        if any(c['nullable'] for c in cols if c['name'] in primary):raise ValueError('Primary key columns must be nonnullable')
        if not isinstance(t['unique'],list) or len(t['unique'])>16 or not isinstance(t['foreign_keys'],list) or len(t['foreign_keys'])>16:
            raise ValueError('Invalid constraint count')
        unique=[names(v,colnames) for v in t['unique']]
        if len({tuple(v) for v in unique})!=len(unique):raise ValueError('Duplicate unique key')
        fk=[]
        for f in t['foreign_keys']:
            if not isinstance(f,dict) or set(f)!={'columns','table','references'}:
                raise ValueError('Invalid foreign key')
            own=names(f['columns'],colnames);remote=f['references']
            if not isinstance(remote,list) or len(remote)!=len(own):raise ValueError('Foreign key arity mismatch')
            fk.append({'columns':own,'table':name(f['table']),'references':[name(x) for x in remote]})
        tables.append({'name':title,'columns':cols,'primary_key':primary,'unique':unique,'foreign_keys':fk})
    by={t['name']:t for t in tables}
    for t in tables:
        for f in t['foreign_keys']:
            remote=by.get(f['table'])
            if not remote or f['references'] not in [remote['primary_key'],*remote['unique']]:
                raise ValueError('Foreign key must reference a declared primary or unique key')
            own_types={c['name']:c['type'] for c in t['columns']}
            remote_types={c['name']:c['type'] for c in remote['columns']}
            if any(own_types[a]!=remote_types[b] for a,b in zip(f['columns'],f['references'])):
                raise ValueError('Foreign key types differ')
    return {'tables':tables}

def quote(s):return '"'+s+'"'
def keys(v):return '('+', '.join(map(quote,v))+')'
def sql_for(spec):
    statements=[]
    for t in spec['tables']:
        parts=[quote(c['name'])+' '+c['type']+('' if c['nullable'] else ' NOT NULL') for c in t['columns']]
        if t['primary_key']:parts.append('PRIMARY KEY '+keys(t['primary_key']))
        parts.extend('UNIQUE '+keys(v) for v in t['unique'])
        parts.extend('FOREIGN KEY '+keys(f['columns'])+' REFERENCES '+quote(f['table'])+' '+keys(f['references']) for f in t['foreign_keys'])
        statements.append('CREATE TABLE '+quote(t['name'])+' (\n    '+',\n    '.join(parts)+'\n);')
    return 'PRAGMA foreign_keys = ON;\nBEGIN;\n\n'+'\n\n'.join(statements)+'\n\nCOMMIT;\n'

def verify(spec,sql):
    db=sqlite3.connect(':memory:')
    try:
        db.executescript(sql)
        if db.execute('PRAGMA foreign_keys').fetchone()[0]!=1:raise ValueError('Foreign key enforcement disabled')
        observed={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        if observed!={t['name'] for t in spec['tables']}:raise ValueError('Schema table mismatch')
        for t in spec['tables']:
            actual=db.execute('PRAGMA table_info('+quote(t['name'])+')').fetchall()
            expected=[(c['name'],c['type'],int(not c['nullable']),t['primary_key'].index(c['name'])+1 if c['name'] in t['primary_key'] else 0) for c in t['columns']]
            if [(r[1],r[2],r[3],r[5]) for r in actual]!=expected:raise ValueError('Schema column mismatch')
            fk=db.execute('PRAGMA foreign_key_list('+quote(t['name'])+')').fetchall()
            grouped={}
            for r in fk:grouped.setdefault(r[0],[]).append(r)
            seen=sorted((v[0][2],tuple(r[3] for r in sorted(v,key=lambda r:r[1])),tuple(r[4] for r in sorted(v,key=lambda r:r[1]))) for v in grouped.values())
            want=sorted((f['table'],tuple(f['columns']),tuple(f['references'])) for f in t['foreign_keys'])
            if seen!=want:raise ValueError('Schema foreign-key mismatch')
            uniques=[]
            for index in db.execute('PRAGMA index_list('+quote(t['name'])+')'):
                if index[2] and index[3]=='u':
                    # SQLite-generated names only; escape even trusted metadata.
                    literal='"'+index[1].replace('"','""')+'"'
                    uniques.append(tuple(r[2] for r in db.execute('PRAGMA index_info('+literal+')')))
            if sorted(uniques)!=sorted(map(tuple,t['unique'])):raise ValueError('Schema unique-key mismatch')
        if db.execute('PRAGMA integrity_check').fetchone()!=('ok',) or db.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ValueError('Disposable schema integrity check failed')
    finally:db.close()

def review(root,source,output,exclude=()):
    return guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.sql')
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.sql')
def execute(root,plan):
    spec,dst,_=validate(root,plan);sql=sql_for(spec);verify(spec,sql)
    sha=guard.publish(sql.encode('utf-8'),dst,lambda:validate(root,plan))
    return {'schema':'janus-database-schema-result-v1','status':'sqlite_schema_verified','output':plan['output'],
            'sha256':sha,'tables':len(spec['tables']),'columns':sum(len(t['columns']) for t in spec['tables']),
            'live_database_modified':False,'application_semantics_verified':False}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--plan',required=True);args=parser.parse_args()
    try:
        print(json.dumps(execute(args.root,json.loads(args.plan)),sort_keys=True),flush=True);return 0
    except Exception as exc:
        print(json.dumps({'status':'blocked','error_type':type(exc).__name__,'reason':'Schema generation unavailable; inspect typed schema and constraints'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
