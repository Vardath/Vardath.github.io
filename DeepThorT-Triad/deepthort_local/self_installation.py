"""Explicitly owner-approved installation of the fixed V71 diagnostic-only update.

Not a general updater. No arbitrary generated code, network, launch or elevation.
The running process continues using its imported formatter until a normal restart.
"""
from __future__ import annotations
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
from .agent_contract import canonical_sha
from .source_security import linked
from .self_development import TARGET,observe,_load
from .self_update_preparation import _snapshot,_verify_zip
from .typed_project_tool import read_bound
from .disk_gate import require_storage

SCHEMA='deepthortriad-diagnostic-install-v1'

def digest(raw):return hashlib.sha256(raw).hexdigest()

def roots(root,state):
    root=Path(root).resolve(strict=True);state=Path(state).resolve(strict=True)
    if state!=root/'state' or not state.is_dir():raise ValueError('Expected installed application state')
    for path in (root,state,root/'deepthort_local',root/TARGET,state/'self-development',state/'self-development.sqlite3'):
        if linked(path):raise ValueError('Linked application or state path')
    return root,state

def prepared(root,state):
    root,state=roots(root,state)
    seen=observe(root)
    if not seen:raise ValueError('No current diagnostic-only update')
    with closing(sqlite3.connect(state/'self-development.sqlite3',timeout=2)) as db:
        body=_load(db,seen['key'])
    if not body or body['state']!='update_prepared' or body['authority'] is not False:raise ValueError('No prepared independent review')
    staged={k:v for k,v in body.items() if k!='update'};staged['state']='staged'
    observed,candidate,folder,baseline,new=_snapshot(root,state,staged)
    update=body['update'];manifest=update['manifest']
    expected={'schema':'deepthort-self-update-preparation-v1','version':'diagnostic-'+candidate['candidate_sha'][:16],
              'target':TARGET,'scope_sha':observed['key'],'review_sha':canonical_sha(body['review']),
              'baseline_sha':digest(baseline),'candidate_sha':digest(new),
              'runtime_probe':{'schema':'diagnostic-probe-v1','baseline_sha':digest(baseline),'candidate_sha':digest(new),
                               'cases_passed':8,'assurance':'isolated_formatter_runtime_only'},
              'rollback_bytes_verified':True,'full_application_verified':False,'installation_authorized':False,'installer':False}
    if manifest!=expected or update['version']!=expected['version'] or update['package']!=expected['version']+'.zip':
        raise ValueError('Prepared update manifest mismatch')
    archive=folder/update['package']
    if any(linked(x) for x in (folder,archive,folder/'manifest.json',folder/'baseline.py.txt',folder/'candidate.py.txt')):
        raise ValueError('Linked staged source')
    if _verify_zip(archive,expected,baseline,new)!=update['package_sha']:raise ValueError('Prepared package changed')
    return root,folder,baseline,new,body

def review(root,state):
    root,folder,baseline,new,body=prepared(root,state)
    plan={'schema':SCHEMA,'root':str(root),'target':TARGET,'scope_sha':body['key'],
          'baseline_sha':digest(baseline),'candidate_sha':digest(new),'package_sha':body['update']['package_sha'],
          'review_sha':canonical_sha(body['review']),'expires_at':int(time.time())+300}
    return plan,{'old':body['evidence']['observed'],'new':body['candidate']['replacement'],
                 'target':TARGET,'candidate_sha':plan['candidate_sha'],'scope':'Diagnostic wording only; normal restart needed. No general application acceptance.'}

def validated(root,state,plan):
    fresh,_=review(root,state)
    if not isinstance(plan,dict) or set(plan)!=set(fresh) or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+300:
        raise ValueError('Invalid or expired owner review')
    if any(plan[k]!=fresh[k] for k in fresh if k!='expires_at'):raise ValueError('Reviewed update changed')
    return prepared(root,state)

def atomic_bytes(target,raw,recheck):
    fd,name=tempfile.mkstemp(prefix='.deepthortriad-update-',suffix='.tmp',dir=target.parent)
    try:
        with os.fdopen(fd,'wb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
        recheck();os.replace(name,target)
    finally:
        if os.path.exists(name):os.unlink(name)

def install(root,state,plan,*,approval=False,idle=lambda:False):
    if approval is not True or not idle():raise PermissionError('Fresh explicit owner consent and idle app required')
    root,folder,baseline,new,body=validated(root,state,plan);target=root/TARGET
    require_storage(root)
    backup=folder/'installed-baseline.py.txt';receipt=folder/'install-receipt.json'
    if os.path.lexists(backup) or os.path.lexists(receipt):raise ValueError('Prior installation transaction exists; inspect before retry')
    with backup.open('xb') as f:f.write(baseline);f.flush();os.fsync(f.fileno())
    if read_bound(backup,32000)!=baseline:raise ValueError('Backup verification failed')
    record={'schema':SCHEMA,'plan':plan,'backup':backup.name,'restart_required':True,
            'full_application_verified':False,'state':'prepared'}
    # Retain a durable pre-write receipt even if power is lost after replacement.
    with receipt.open('x',encoding='utf8') as f:json.dump(record,f,sort_keys=True);f.flush();os.fsync(f.fileno())
    def recheck():
        if not idle():raise ValueError('Application no longer idle')
        validated(root,state,plan)
        if read_bound(backup,32000)!=baseline:raise ValueError('Backup changed')
    atomic_bytes(target,new,recheck)
    if read_bound(target,32000)!=new:raise ValueError('Installed bytes differ; retain recovery artifacts')
    record['state']='installed';record['installed_sha']=digest(new)
    atomic_bytes(receipt,json.dumps(record,sort_keys=True).encode('utf8'),lambda:None)
    return record
