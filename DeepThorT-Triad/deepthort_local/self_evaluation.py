"""Bounded autonomous self-evaluation of local acceptance evidence; advisory only."""
from collections import Counter
from datetime import datetime,timezone
import hashlib
import os
from pathlib import Path
import re
from .latest_acceptance import ALLOWED,SCHEMA,STATUSES
from .structured_source import strict_json
from .source_security import linked

MAX_REPORTS=8
MAX_BYTES=65536
FILE=re.compile(r'LatestTest-\d{8}-\d{6}-\d{6}\.json')
ORDER={'failed':0,'blocked':1,'inconclusive':2,'cancelled':3,'passed':4}

def read_report(path):
    if linked(path) or not path.is_file() or path.stat().st_size>MAX_BYTES:
        raise ValueError('Invalid acceptance report')
    with path.open('rb') as stream:raw=stream.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:raise ValueError('Acceptance report exceeds bound')
    data=strict_json(raw.decode('utf-8'))
    if not isinstance(data,dict) or data.get('schema')!=SCHEMA or not isinstance(data.get('results'),list) or not 1<=len(data['results'])<=len(ALLOWED):
        raise ValueError('Invalid acceptance report schema')
    timestamp=datetime.fromisoformat(data['completed_utc'])
    if timestamp.tzinfo is None:raise ValueError('Missing report timezone')
    timestamp=timestamp.astimezone(timezone.utc)
    if not isinstance(data.get('test_id'),str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}',data['test_id']):
        raise ValueError('Invalid acceptance test identity')
    checks={}
    for row in data['results']:
        if not isinstance(row,dict) or row.get('check') not in ALLOWED or row.get('status') not in STATUSES or row['check'] in checks:
            raise ValueError('Invalid or duplicate probe result')
        checks[row['check']]=row['status']
    outcome=next(s for s in ('cancelled','failed','blocked','inconclusive','passed') if s in checks.values())
    if data.get('outcome')!=outcome:raise ValueError('Report outcome contradicts checks')
    return {'sha256':hashlib.sha256(raw).hexdigest(),'test_id':data['test_id'],
            'completed_utc':timestamp.isoformat(),'outcome':outcome,'checks':checks}

def assess(state):
    folder=Path(state)/'latest-tests';latest=folder/'latest.json'
    if not folder.is_dir() or linked(folder) or not latest.is_file():return None
    current=read_report(latest)
    candidates=[]
    with os.scandir(folder) as entries:
        for i,entry in enumerate(entries):
            if i>=4096:raise ValueError('Acceptance history exceeds bounded directory scan')
            if FILE.fullmatch(entry.name) and entry.is_file(follow_symlinks=False):candidates.append(entry.name)
    prior=[];seen={current['sha256']}
    for name in sorted(candidates,reverse=True)[:MAX_REPORTS]:
        try:row=read_report(folder/name)
        except (OSError,ValueError,TypeError,KeyError):continue
        if row['sha256'] in seen or row['test_id']!=current['test_id'] or row['completed_utc']>=current['completed_utc']:continue
        seen.add(row['sha256']);prior.append(row)
    prior.sort(key=lambda r:r['completed_utc'],reverse=True)
    findings=[]
    for check,status in current['checks'].items():
        if status=='passed':continue
        history=[r['checks'][check] for r in prior if check in r['checks']]
        regression=bool(history and history[0]=='passed' and status=='failed')
        recurring=0
        for earlier in history:
            if earlier!=status:break
            recurring+=1
        findings.append({'check':check,'status':status,'regression':regression,'consecutive_observations':1+recurring})
    findings.sort(key=lambda r:(ORDER[r['status']],not r['regression'],-r['consecutive_observations'],r['check']))
    return {'schema':'janus-self-evaluation-v1','latest_sha':current['sha256'],'test_id':current['test_id'],
            'completed_utc':current['completed_utc'],'counts':dict(Counter(current['checks'].values())),
            'findings':findings,'comparable_history':len(prior),'missing_checks':sorted(ALLOWED-set(current['checks'])),
            'general_competence_verified':False,'execution_authorized':False}

def recommend_once(state,store):
    assessment=assess(state)
    if not assessment:return 0
    count=0
    for row in assessment['findings']:
        if row['status']=='cancelled':continue
        check=row['check'];status=row['status']
        kind='regression' if row['regression'] else 'repeated observation' if row['consecutive_observations']>1 else 'observation'
        proposal={'failed':'Investigate the exact failed acceptance probe; reproduce the failure and obtain independent review before any repair.',
                  'blocked':'Identify the missing prerequisite or resource condition; do not classify as a model defect.',
                  'inconclusive':'Collect missing acceptance evidence without treating uncertainty as success.'}[status]
        key='self-eval-'+hashlib.sha256((assessment['latest_sha']+':'+check).encode()).hexdigest()
        count+=bool(store.recommend(evidence_key=key,problem=f'Self-evaluation: {check} {status} ({kind}; {row["consecutive_observations"]} comparable observation(s))',
            proposal=proposal+' Advisory only; no execution or source changes authorized.'))
    return count
