"""Reviewed immutable local release deployment; never install or execute an artifact."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.installer_project import component

SCHEMA='janus-local-release-deploy-v1'
EXTRA=('artifact','.zip')
MAX_TOTAL=64*1024*1024
MAX_MEMBERS=256

def checked(s):
    if not isinstance(s,dict) or set(s)!={'artifact','name','version','sha256'}:
        raise ValueError('Expected artifact, release name, version and exact SHA-256')
    if not isinstance(s['artifact'],str) or not s['artifact'].casefold().endswith('.zip'):raise ValueError('Choose existing release ZIP')
    component(s['name'])
    if not isinstance(s['version'],str) or not re.fullmatch(r'[0-9]{1,4}(?:\.[0-9]{1,4}){1,3}',s['version']):
        raise ValueError('Choose numeric version')
    if not isinstance(s['sha256'],str) or not re.fullmatch(r'[0-9a-f]{64}',s['sha256']):
        raise ValueError('Exact artifact SHA-256 required')
    return s

def inspect(raw,s):
    checked(s)
    if hashlib.sha256(raw).hexdigest()!=s['sha256']:raise ValueError('Artifact hash differs from approved release identity')
    seen=set();total=0
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            infos=z.infolist()
            if not 1<=len(infos)<=MAX_MEMBERS:raise ValueError('Release member count outside bound')
            for i in infos:
                name=i.filename.rstrip('/')
                if not name or len(name)>220 or i.flag_bits&1 or stat.S_IFMT(i.external_attr>>16) not in (0,stat.S_IFREG,stat.S_IFDIR):
                    raise ValueError('Unsafe or encrypted archive member')
                for p in name.split('/'):component(p)
                folded=name.casefold()
                if folded in seen:raise ValueError('Duplicate or case-colliding release member')
                seen.add(folded);total+=i.file_size
                if total>MAX_TOTAL:raise ValueError('Expanded release exceeds bound')
            if not any(not i.is_dir() for i in infos):raise ValueError('Empty release')
            files={i.filename.casefold() for i in infos if not i.is_dir()}
            if any('/'.join(n.split('/')[:k]) in files for n in seen for k in range(1,len(n.split('/')))):
                raise ValueError('Archive file/directory collision')
            if z.testzip() is not None:raise ValueError('Release CRC check failed')
    except (zipfile.BadZipFile,RuntimeError,NotImplementedError) as exc:raise ValueError('Invalid release archive') from exc
    return {'schema':SCHEMA,'name':s['name'],'version':s['version'],'artifact_sha256':s['sha256'],
            'bytes':len(raw),'members':len(infos),'expanded_bytes':total,'archive_verified':True,
            'installed':False,'executed':False,'remote_deployed':False,'ci_verified':False}

def validate(root,plan):
    s,dst,src=guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
    if dst.name!=s['name']+'-'+s['version']+'.zip':
        raise ValueError('Output must be the exact new versioned release filename')
    if plan['guards'][1]['expected']!=s['sha256']:raise ValueError('Reviewed artifact digest mismatch')
    return s,dst,src

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
    _,_,src=validate(root,plan);receipt=inspect(guard.exact(src,plan['guards'][1],guard.MAX_INPUT),s)
    return plan,dict(s,observations=receipt,scope='Atomically publish the exact existing reviewed ZIP into a new versioned file in an existing project-local release directory. No replacement, extraction, execution, installation, remote transfer, or CI claim.')

def execute(root,plan):
    s,dst,src=validate(root,plan);raw=guard.exact(src,plan['guards'][1],guard.MAX_INPUT)
    receipt=inspect(raw,s)
    digest=guard.publish(raw,dst,lambda:validate(root,plan))
    if digest!=s['sha256']:raise ValueError('Publication hash mismatch')
    return {'status':'local_versioned_release_deployed','output':plan['output'],'sha256':digest,
            'source_unchanged':True,'previous_releases_untouched':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Exact local release deployment unavailable; inspect source hash, versioned destination and archive'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
