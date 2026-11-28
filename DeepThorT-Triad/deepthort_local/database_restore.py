"""Restore a verified JANUS SQLite archive into a new project database."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.database_backup import unpack
from deepthort_local.sql_query import no_sidecars

SCHEMA='janus-database-restore-v1'
EXTRA=('archive','.zip')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'archive'} or not isinstance(s['archive'],str):
        raise ValueError('Expected one reviewed database backup archive')
    return s

def validate(root,plan):
    s,dst,src=guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.db',extra=EXTRA)
    no_sidecars(dst)
    return s,dst,src

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.db',extra=EXTRA)
    _,_,src=validate(root,plan)
    _,meta=unpack(guard.exact(src,plan['guards'][1],guard.MAX_INPUT))
    return plan,dict(s,observations=meta,scope='Restore exact verified SQLite bytes to a new .db file only. No replacement of live database or app state. Archive contents are not authenticated against an external signature.')
def execute(root,plan):
    s,dst,src=validate(root,plan)
    raw,meta=unpack(guard.exact(src,plan['guards'][1],guard.MAX_INPUT))
    digest=guard.publish(raw,dst,lambda:validate(root,plan))
    if digest!=meta['database_sha256']:raise ValueError('Restored bytes mismatch')
    return {'schema':SCHEMA,'status':'database_restored_verified','output':plan['output'],
            'sha256':digest,'archive_unchanged':True,'live_database_modified':False,
            'integrity_verified':True,'database_bytes':len(raw)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Database restore refused; inspect backup manifest, integrity and new destination'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
