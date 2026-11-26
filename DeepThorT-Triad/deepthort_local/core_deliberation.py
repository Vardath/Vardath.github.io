"""Resumable neural phase of each existing eleven-core society.

Each role has its own exact scoped cycle. One admitted turn per background
opportunity: seven independent specialist readings, six-peer reconsideration
for each specialist, two separate hemisphere integrations, Front, Interface.
The same resident role model performs isolated inference calls; no new model
process, execution authority, or foreground dependency is introduced.
"""
from contextlib import closing
import json
import sqlite3
import time
from pathlib import Path
from .agent_contract import canonical_sha
from .janus_cognition import SPECIALISTS, FACULTIES
from .memory_duty import reader,DUTY_STATES
from . import workflow_attention as attention
from .structured_source import strict_json
from .agent_doctrine import fingerprint

ORDER=tuple((n,'initial') for n in SPECIALISTS)+tuple((n,'revise') for n in SPECIALISTS)+(
    ('Left','integrate'),('Right','integrate'),('Front','integrate'),('Interface','express'))
TTL=3600
MAX_ROUNDS=32
ROLES=('janus','sentinel')
CORE_TASKS={
 'Evidence':'Identify what the observed evidence actually supports, and what is missing.',
 'Safety':'Assess user authority, risks, resource constraints and potential harm.',
 'Counterpoint':'Challenge assumptions; identify a specific counterexample or conflicting requirement.',
 'Context':'Relate the current work to the original goal, surrounding interfaces and circumstances.',
 'Logic':'Derive dependencies, causal explanations and testable implications.',
 'Novelty':'Identify a useful alternative or previously unconsidered opportunity.',
 'Memory':'Distinguish relevant recalled knowledge, continuity and unverified historical claims.',
 'Left':'Integrate all seven revised specialist findings into a constrained, evidence-based interpretation.',
 'Right':'Integrate all seven revised specialist findings into an alternative-oriented interpretation.',
 'Front':'Integrate the two hemisphere interpretations, preserving uncertainty and resolving disagreements.',
 'Interface':'Decide whether the exact Front finding is worth expressing; do not add new content.'}

def _path(job_db):return Path(job_db).parent/'janus-counsel.sqlite3'

def _parse(answer,core):
    if not isinstance(answer,str) or len(answer)>1800:raise ValueError('Invalid neural core response')
    if core in ('Front','Interface'):return attention.parse(answer)
    value=strict_json(answer.strip())
    if not isinstance(value,dict) or set(value)!= {'faculties','conclusion','check'}:
        raise ValueError('Invalid core response schema')
    faculties=value['faculties']
    if not isinstance(faculties,dict) or set(faculties)!=set(map(str,FACULTIES)):
        raise ValueError('Expected all seven Fano faculty interpretations')
    for field,limit in [(s,45) for s in faculties]:
        x=faculties[field]
        if not isinstance(x,str) or not x.strip() or len(x)>limit or any(ord(c)<32 for c in x):raise ValueError('Invalid faculty')
    for field,limit in (('conclusion',180),('check',120)):
        x=value[field]
        if not isinstance(x,str) or not x.strip() or len(x)>limit or any(ord(c)<32 for c in x):raise ValueError('Invalid conclusion')
    return value

def _ensure(db):
    db.execute("""CREATE TABLE IF NOT EXISTS core_deliberation_v64(
       role TEXT NOT NULL,work_key TEXT NOT NULL,job_id INTEGER NOT NULL,
       identity TEXT NOT NULL,turns TEXT NOT NULL,receipt_sha TEXT NOT NULL,
       updated REAL NOT NULL,PRIMARY KEY(role,work_key))""")

def _identity(role,packet):
    return {'role':role,'key':packet['key'],'scope':packet['identity'],
            'doctrine':fingerprint(role),'schema':'reactive-core-v64'}

def _validate_turns(identity,turns):
    if not isinstance(turns,list) or len(turns)>len(ORDER):raise ValueError('Invalid persisted turns')
    previous=canonical_sha(identity)
    for i,turn in enumerate(turns):
        core,phase=ORDER[i]
        if not isinstance(turn,dict) or set(turn)!= {'core','phase','input_sha','result','previous','sha'}:
            raise ValueError('Invalid persisted core turn')
        if (turn['core'],turn['phase'])!=(core,phase) or turn['previous']!=previous:
            raise ValueError('Core sequence changed')
        if canonical_sha({k:v for k,v in turn.items() if k!='sha'})!=turn['sha']:
            raise ValueError('Core receipt changed')
        _parse(json.dumps(turn['result']),core)
        previous=turn['sha']
    return turns

def _load(job_db,role,packet):
    identity=_identity(role,packet)
    try:
        with closing(reader(_path(job_db),timeout=.05)) as db:
            row=db.execute("SELECT identity,turns,receipt_sha,updated FROM core_deliberation_v64 WHERE role=? AND work_key=?",
                (role,packet['key'])).fetchone()
        if not row:return []
        if not time.time()-TTL<=row['updated']<=time.time():return []
        actual=json.loads(row['identity']);turns=json.loads(row['turns'])
        if actual!=identity or canonical_sha([actual,turns])!=row['receipt_sha']:return None
        return _validate_turns(identity,turns)
    except sqlite3.OperationalError as exc:
        if 'no such table' in str(exc) or 'unable to open database file' in str(exc):return []
        return None
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return None

def choose(job_db,role):
    if role not in ROLES:raise ValueError('Unknown society')
    try:
        with closing(reader(job_db,timeout=.05)) as db:
            marks=','.join('?' for _ in DUTY_STATES)
            ids=[r[0] for r in db.execute(f"""SELECT id FROM jobs WHERE mode='build'
                AND approval_key IS NOT NULL AND state IN ({marks}) ORDER BY id LIMIT 32""",DUTY_STATES)]
        for job_id in ids:
            packet=attention._safe_scope(job_db,job_id)
            if not packet:continue
            turns=_load(job_db,role,packet)
            if turns is not None and len(turns)<len(ORDER):return packet
    except (OSError,ValueError,TypeError,sqlite3.Error):pass
    return None

def _inputs(job_db,packet,turns):
    core,phase=ORDER[len(turns)]
    if phase=='initial':
        return {'observed':attention.evidence(job_db,packet)}
    if phase=='revise':
        first={t['core']:t['result'] for t in turns[:7]}
        return {'observed':attention.evidence(job_db,packet)[:1900],
                'own_prior':first[core],
                'peers':{n:first[n] for n in SPECIALISTS if n!=core}}
    if core in ('Left','Right'):
        return {'peers':{t['core']:t['result'] for t in turns[7:14]}}
    if core=='Front':
        return {'peers':{t['core']:t['result'] for t in turns[14:16]}}
    return {'Front':turns[16]['result']}

def _bounded_input(inputs):
    # Preserve all peer conclusions and checks; never silently cut the last
    # core from a JSON stream. Faculty readings remain stored in full.
    compact={}
    for k,v in inputs.items():
        if k=='peers':compact[k]={n:({'conclusion':a['conclusion'],'check':a['check']} if 'conclusion' in a else a) for n,a in v.items()}
        elif k=='own_prior':compact[k]=v
        else:compact[k]=v
    text=json.dumps(compact,ensure_ascii=False)
    # Truncate only the raw observed excerpt (which is already labelled
    # partial); every prior conclusion and all six/seven peer identities
    # must remain complete. Escaped JSON length, not raw length, is bounded.
    if len(text)>4200 and 'observed' in compact:
        observed=compact['observed']
        lo,hi=0,len(observed)
        while lo<hi:
            mid=(lo+hi+1)//2
            compact['observed']=observed[:mid]
            if len(json.dumps(compact,ensure_ascii=False))<=4200:lo=mid
            else:hi=mid-1
        compact['observed']=observed[:lo]
        text=json.dumps(compact,ensure_ascii=False)
    if len(text)>4200:raise ValueError('Core input exceeds bounded context')
    return text

def step(job_db,role,counsel,stopped,packet=None):
    if stopped():return None
    packet=packet or choose(job_db,role)
    if not packet or not attention.current(job_db,packet):return None
    turns=_load(job_db,role,packet)
    if turns is None or len(turns)>=len(ORDER):return None
    core,phase=ORDER[len(turns)]
    inputs=_inputs(job_db,packet,turns)
    try:payload=_bounded_input(inputs)
    except ValueError:return None
    answer=counsel.request(society=role,goal='Independent '+core+' core',
        problem=CORE_TASKS[core],evidence=payload,core_phase=phase,core_name=core)
    if not answer or stopped() or not attention.current(job_db,packet):return None
    try:
        result=_parse(answer,core)
        if core=='Interface' and result['kind']=='advice' and result!=turns[16]['result']:
            raise ValueError('Interface cannot introduce or change a Front finding')
        identity=_identity(role,packet)
        turn={'core':core,'phase':phase,'input_sha':canonical_sha(json.loads(payload)),'result':result,
              'previous':turns[-1]['sha'] if turns else canonical_sha(identity)}
        turn['sha']=canonical_sha(turn)
        with closing(sqlite3.connect(_path(job_db),timeout=2)) as db,db:
            _ensure(db);db.execute('BEGIN IMMEDIATE')
            prior=db.execute("SELECT receipt_sha,updated FROM core_deliberation_v64 WHERE role=? AND work_key=?",
                (role,packet['key'])).fetchone()
            if prior and prior[1]>=time.time()-TTL and prior[0]!=canonical_sha([identity,turns]):return None
            if not prior and turns:return None
            updated=turns+[turn]
            db.execute("""INSERT OR REPLACE INTO core_deliberation_v64 VALUES(?,?,?,?,?,?,?)""",
                (role,packet['key'],packet['bound']['job_id'],json.dumps(identity,sort_keys=True),
                 json.dumps(updated,sort_keys=True),canonical_sha([identity,updated]),time.time()))
            db.execute("DELETE FROM core_deliberation_v64 WHERE updated<?",(time.time()-TTL,))
            db.execute("""DELETE FROM core_deliberation_v64 WHERE rowid IN
                (SELECT rowid FROM core_deliberation_v64 ORDER BY updated DESC,rowid DESC LIMIT -1 OFFSET ?)""",(MAX_ROUNDS,))
        if not attention.current(job_db,packet):return None
        if core=='Interface' and result['kind']=='advice':
            # Reuse the existing attention ledger/outbox publication route.
            # No model is allowed to publish or change the goal by itself.
            return {'key':packet['key'],'job_id':packet['bound']['job_id'],
                    'result':result,'round_sha':turn['sha']}
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return None
    return None

def snapshot(job_db,role):
    """Existing society's public per-core neural readings; not new facts."""
    try:
        with closing(reader(_path(job_db),timeout=.05)) as db:
            rows=db.execute("""SELECT work_key,job_id FROM core_deliberation_v64
              WHERE role=? AND updated>=? ORDER BY updated DESC LIMIT 8""",(role,time.time()-TTL)).fetchall()
        for key,job_id in rows:
            packet=attention._safe_scope(job_db,job_id)
            if not packet or packet['key']!=key:continue
            turns=_load(job_db,role,packet)
            if not turns:continue
            return {'key':key,'turn_count':len(turns),'complete':len(turns)==len(ORDER),
                    'cores':{t['core']:{'phase':t['phase'],'reading':t['result'],'receipt_sha':t['sha']}
                             for t in turns},'epistemic_status':'advisory_not_verified'}
    except (OSError,ValueError,TypeError,sqlite3.Error):pass
    return {}
