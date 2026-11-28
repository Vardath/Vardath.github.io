"""Owner-reviewed rollback of an exact V71 installed diagnostic update.

Only the previously installed diagnostic source is restored; models, state,
projects, runtime, other source and cap settings are never overwritten.
"""
from contextlib import closing
import json
import os
import re
import sqlite3
import time
from . import self_installation as install
from .self_development import CAP_SOURCE,TARGET,_load,_candidate
from .self_update_preparation import _verify_zip
from .agent_contract import canonical_sha
from .source_security import linked
from .typed_project_tool import read_bound
from .disk_gate import require_storage

SCHEMA='deepthortriad-diagnostic-rollback-v1'

def snapshot(root,state,scope):
    root,state=install.roots(root,state)
    if not isinstance(scope,str) or not re.fullmatch(r'[0-9a-f]{64}',scope):
        raise ValueError('Invalid installed update scope')
    folder=state/'self-development'/scope
    if linked(folder) or not folder.is_dir():raise ValueError('Unsafe update folder')
    def read(name,limit=32000):
        path=folder/name
        if linked(path):raise ValueError('Linked rollback artifact')
        return read_bound(path,limit)
    with closing(sqlite3.connect(state/'self-development.sqlite3',timeout=2)) as db:
        body=_load(db,scope)
    if not body or body['state']!='update_prepared' or body['authority'] is not False:
        raise ValueError('No independently reviewed installed update')
    raw=read('install-receipt.json');receipt=json.loads(raw)
    plan=receipt['plan']
    if (receipt['schema']!=install.SCHEMA or receipt['state'] not in ('installed','prepared')
            or receipt['backup']!='installed-baseline.py.txt' or plan['schema']!=install.SCHEMA
            or plan['root']!=str(root) or plan['target']!=TARGET or plan['scope_sha']!=scope):
        raise ValueError('Installation receipt mismatch')
    baseline=read('installed-baseline.py.txt');candidate=read('candidate.py.txt')
    if baseline!=read('baseline.py.txt'):raise ValueError('Backup differs from reviewed baseline')
    evidence=body['evidence']
    if (canonical_sha(evidence)!=scope or evidence['target']!=TARGET
            or evidence['base_sha']!=install.digest(baseline)
            or evidence['cap_source_sha']!=install.digest(read_bound(root/CAP_SOURCE,32000))):
        raise ValueError('Baseline or resource configuration changed')
    expected=_candidate({'source':baseline.decode('utf8'),'evidence':evidence},
                        json.dumps({'replacement':body['candidate']['replacement']}))
    if (candidate!=expected['source'].encode('utf8') or body['candidate']['candidate_sha']!=expected['candidate_sha']
            or body['review']['accepted'] is not True or body['review']['candidate_sha']!=expected['candidate_sha']
            or plan['review_sha']!=canonical_sha(body['review'])
            or plan['baseline_sha']!=install.digest(baseline) or plan['candidate_sha']!=install.digest(candidate)):
        raise ValueError('Reviewed diagnostic identities differ')
    update=body['update'];manifest=update['manifest']
    expected_manifest={'schema':'deepthort-self-update-preparation-v1',
        'version':'diagnostic-'+expected['candidate_sha'][:16],'target':TARGET,'scope_sha':scope,
        'review_sha':plan['review_sha'],'baseline_sha':plan['baseline_sha'],'candidate_sha':plan['candidate_sha'],
        'runtime_probe':{'schema':'diagnostic-probe-v1','baseline_sha':plan['baseline_sha'],
                         'candidate_sha':plan['candidate_sha'],'cases_passed':8,
                         'assurance':'isolated_formatter_runtime_only'},
        'rollback_bytes_verified':True,'full_application_verified':False,
        'installation_authorized':False,'installer':False}
    archive=folder/(expected_manifest['version']+'.zip')
    if (manifest!=expected_manifest or update['version']!=expected_manifest['version']
            or update['package']!=archive.name or linked(archive)
            or _verify_zip(archive,manifest,baseline,candidate)!=update['package_sha']
            or plan['package_sha']!=update['package_sha']):
        raise ValueError('Update package changed')
    if receipt['state']=='installed' and receipt.get('installed_sha')!=plan['candidate_sha']:
        raise ValueError('Installed receipt hash mismatch')
    if read_bound(root/TARGET,32000)!=candidate:raise ValueError('Live source is not the exact installed candidate')
    return root,folder,baseline,candidate,install.digest(raw)

def review(root,state,scope=None):
    root,state=install.roots(root,state)
    if scope is None:
        with closing(sqlite3.connect(state/'self-development.sqlite3',timeout=2)) as db:
            keys=db.execute("SELECT key FROM self_development_v70 WHERE state='update_prepared' LIMIT 129").fetchall()
        if len(keys)>128:raise ValueError('Too many update records for automatic selection')
        eligible=[]
        for (key,) in keys:
            if not re.fullmatch(r'[0-9a-f]{64}',key):raise ValueError('Invalid ledger key')
            if os.path.lexists(state/'self-development'/key/'install-receipt.json'):
                try:
                    snapshot(root,state,key)
                except (ValueError,OSError,KeyError,TypeError):continue
                eligible.append(key)
        if len(eligible)!=1:raise ValueError('No unique exact installed diagnostic update available for rollback')
        scope=eligible[0]
    root,folder,baseline,candidate,receipt_sha=snapshot(root,state,scope)
    if os.path.lexists(folder/'rollback-receipt.json'):
        raise ValueError('Prior rollback transaction exists; inspect before retry')
    return {'schema':SCHEMA,'root':str(root),'target':TARGET,'scope_sha':scope,
            'baseline_sha':install.digest(baseline),'installed_sha':install.digest(candidate),
            'install_receipt_sha':receipt_sha,'expires_at':int(time.time())+300}

def restore(root,state,plan,*,approval=False,idle=lambda:False):
    if approval is not True or not idle():raise PermissionError('Fresh explicit owner consent and idle app required')
    def checked():
        if not isinstance(plan,dict) or type(plan.get('expires_at')) is not int or not time.time()<plan['expires_at']<=time.time()+300:
            raise ValueError('Invalid or expired rollback approval')
        result=snapshot(root,state,plan.get('scope_sha'))
        r,folder,baseline,candidate,receipt_sha=result
        expected={'schema':SCHEMA,'root':str(r),'target':TARGET,'scope_sha':plan['scope_sha'],
                  'baseline_sha':install.digest(baseline),'installed_sha':install.digest(candidate),
                  'install_receipt_sha':receipt_sha,'expires_at':plan['expires_at']}
        if expected!=plan:raise ValueError('Reviewed rollback scope changed')
        return result
    root,folder,baseline,candidate,_=checked()
    require_storage(root)
    receipt=folder/'rollback-receipt.json'
    if os.path.lexists(receipt):raise ValueError('Prior rollback transaction exists')
    record={'schema':SCHEMA,'plan':plan,'state':'prepared','restart_required':True,
            'full_application_restored':False,'retained_candidate':'candidate.py.txt'}
    with receipt.open('x',encoding='utf8') as out:
        json.dump(record,out,sort_keys=True);out.flush();os.fsync(out.fileno())
    def recheck():
        if not idle():raise ValueError('Application no longer idle')
        checked()
    install.atomic_bytes(root/TARGET,baseline,recheck)
    if read_bound(root/TARGET,32000)!=baseline:raise ValueError('Restored bytes differ; inspect receipt')
    record['state']='restored';record['restored_sha']=install.digest(baseline)
    install.atomic_bytes(receipt,json.dumps(record,sort_keys=True).encode('utf8'),lambda:None)
    return record
