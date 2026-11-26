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
from .triad_profiles import PROFILES,RUNTIME_VERSION

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
    db.execute("""CREATE TABLE IF NOT EXISTS core_deliberation_v65(
       role TEXT NOT NULL,work_key TEXT NOT NULL,job_id INTEGER NOT NULL,
       identity TEXT NOT NULL,turns TEXT NOT NULL,receipt_sha TEXT NOT NULL,
       updated REAL NOT NULL,PRIMARY KEY(role,work_key))""")

def _scope_identity(role,packet):
    return {'role':role,'scope':packet['identity']['scope'],'plan_sha':packet['identity']['plan_sha'],
            'doctrine':fingerprint(role),'model':PROFILES[role][2],'runtime':RUNTIME_VERSION,
            'schema':'reactive-core-v65'}

def _fresh(job_db,packet):
    fresh=attention._safe_scope(job_db,packet['bound']['job_id'])
    if not fresh or any(fresh['identity'][k]!=packet['identity'][k] for k in ('scope','plan_sha')):return None
    return fresh

def _validate_turns(identity,turns):
    if not isinstance(turns,list) or len(turns)>len(ORDER):raise ValueError('Invalid persisted turns')
    previous=canonical_sha(identity)
    for i,turn in enumerate(turns):
        core,phase=ORDER[i]
        if not isinstance(turn,dict) or set(turn)!= {'core','phase','input_sha','result','previous','progress_key','sha'}:
            raise ValueError('Invalid persisted core turn')
        if (turn['core'],turn['phase'])!=(core,phase) or turn['previous']!=previous:
            raise ValueError('Core sequence changed')
        if canonical_sha({k:v for k,v in turn.items() if k!='sha'})!=turn['sha']:
            raise ValueError('Core receipt changed')
        for field in ('input_sha','progress_key'):
            if not isinstance(turn[field],str) or len(turn[field])!=64 or any(c not in '0123456789abcdef' for c in turn[field]):
                raise ValueError('Invalid core observation identity')
        _parse(json.dumps(turn['result']),core)
        if core=='Interface' and turn['result']['kind']=='advice' and turn['result']!=turns[16]['result']:
            raise ValueError('Interface changed the Front conclusion')
        previous=turn['sha']
    return turns

def _current_complete(turns,key):
    # Initial observations can be historical: all seven revisions explicitly
    # reconsider their own and peer readings against newer observations.
    # Outward advice requires a complete revision/integration pass on the
    # current progress state. Mixed-progress thoughts remain internal.
    return len(turns)==len(ORDER) and all(t['progress_key']==key for t in turns[7:])

def _rounds(job_db,role,packet):
    scope=_scope_identity(role,packet);result=[]
    try:
        with closing(reader(_path(job_db),timeout=.05)) as db:
            rows=[dict(r) for r in db.execute("""SELECT * FROM core_deliberation_v65
                WHERE role=? AND job_id=? AND updated>=? ORDER BY updated DESC,rowid DESC LIMIT 12""",
                (role,packet['bound']['job_id'],time.time()-TTL))]
        for row in rows:
            try:
                identity=json.loads(row['identity']);turns=json.loads(row['turns'])
                if any(identity.get(k)!=v for k,v in scope.items()):continue
                if identity.get('key')!=row['work_key'] or row['updated']>time.time():continue
                if canonical_sha([identity,turns])!=row['receipt_sha']:continue
                _validate_turns(identity,turns)
                result.append({'identity':identity,'turns':turns,'receipt_sha':row['receipt_sha']})
            except (ValueError,TypeError,KeyError):continue
        return result
    except FileNotFoundError:return []
    except sqlite3.OperationalError as exc:
        if 'no such table' in str(exc) or 'unable to open database file' in str(exc):return []
        return None
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return None

def _round(job_db,role,packet):
    rounds=_rounds(job_db,role,packet)
    if rounds is None:return None
    recent=rounds[0] if rounds else None
    if recent and (len(recent['turns'])<len(ORDER) or _current_complete(recent['turns'],packet['key'])):
        return recent
    # A new observation reopens the same approved objective, but its
    # predecessor's reasoning remains available as historical hypotheses.
    identity={**_scope_identity(role,packet),'origin_progress':packet['key'],
              'key':canonical_sha([role,packet['key'],recent['receipt_sha'] if recent else None])}
    return {'identity':identity,'turns':[],'receipt_sha':None}

def _historical(job_db,role,packet,round_identity,core):
    rounds=_rounds(job_db,role,packet) or []
    for item in rounds:
        if item['identity']==round_identity:continue
        for turn in reversed(item['turns']):
            if turn['core']==core:
                return {'progress_key':turn['progress_key'],'reading':turn['result'],
                        'receipt_sha':turn['sha'],'status':'historical_hypothesis_not_current_evidence'}
    return None

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
            cycle=_round(job_db,role,packet)
            if cycle is not None and len(cycle['turns'])<len(ORDER):return packet
    except (OSError,ValueError,TypeError,sqlite3.Error):pass
    return None

def select_lane(ordinary,core,last_lane):
    """Fairly alternate independent opportunities when both lanes are ready."""
    if core and (not ordinary or last_lane=='ordinary'):return 'core'
    if ordinary:return 'ordinary'
    return ''

def _reading(turn):
    return {**turn['result'],'progress_key':turn['progress_key']}

def _inputs(job_db,role,packet,cycle):
    turns=cycle['turns'];core,phase=ORDER[len(turns)]
    if phase=='initial':
        observed=attention.evidence(job_db,packet)
        prior=_historical(job_db,role,packet,cycle['identity'],core)
        inputs={'observed':observed}
        if prior:
            inputs['historical_hypothesis']=prior
        return inputs
    if phase=='revise':
        first={t['core']:_reading(t) for t in turns[:7]}
        return {'observed':attention.evidence(job_db,packet)[:1900],
                'own_prior':first[core],
                'peers':{n:first[n] for n in SPECIALISTS if n!=core}}
    if core in ('Left','Right'):
        return {'peers':{t['core']:_reading(t) for t in turns[7:14]}}
    if core=='Front':
        return {'peers':{t['core']:_reading(t) for t in turns[14:16]}}
    return {'Front':turns[16]['result']}

def _bounded_input(inputs):
    # Preserve all peer conclusions and checks; never silently cut the last
    # core from a JSON stream. Faculty readings remain stored in full.
    compact={}
    for k,v in inputs.items():
        if k=='peers':compact[k]={n:({x:a[x] for x in ('conclusion','check','progress_key') if x in a} if 'conclusion' in a else a) for n,a in v.items()}
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
    if not packet:return None
    packet=_fresh(job_db,packet)
    if not packet:return None
    cycle=_round(job_db,role,packet)
    if cycle is None:return None
    turns=cycle['turns']
    if len(turns)>=len(ORDER):return None
    core,phase=ORDER[len(turns)]
    inputs=_inputs(job_db,role,packet,cycle)
    try:payload=_bounded_input(inputs)
    except ValueError:return None
    answer=counsel.request(society=role,goal='Independent '+core+' core',
        problem=CORE_TASKS[core],evidence=payload,core_phase=phase,core_name=core)
    if not answer or stopped() or not _fresh(job_db,packet):return None
    try:
        result=_parse(answer,core)
        if core=='Interface' and result['kind']=='advice' and result!=turns[16]['result']:
            raise ValueError('Interface cannot introduce or change a Front finding')
        identity=cycle['identity']
        turn={'core':core,'phase':phase,'input_sha':canonical_sha(json.loads(payload)),'result':result,
              'progress_key':packet['key'],'previous':turns[-1]['sha'] if turns else canonical_sha(identity)}
        turn['sha']=canonical_sha(turn)
        with closing(sqlite3.connect(_path(job_db),timeout=2)) as db,db:
            _ensure(db);db.execute('BEGIN IMMEDIATE')
            # An expired round may have the same deterministic start key.
            # Remove only expired rows before comparing the exact prior receipt.
            db.execute("DELETE FROM core_deliberation_v65 WHERE updated<?",(time.time()-TTL,))
            prior=db.execute("SELECT receipt_sha,updated FROM core_deliberation_v65 WHERE role=? AND work_key=?",
                (role,identity['key'])).fetchone()
            if (prior[0] if prior else None)!=cycle['receipt_sha']:return None
            updated=turns+[turn]
            db.execute("""INSERT OR REPLACE INTO core_deliberation_v65 VALUES(?,?,?,?,?,?,?)""",
                (role,identity['key'],packet['bound']['job_id'],json.dumps(identity,sort_keys=True),
                 json.dumps(updated,sort_keys=True),canonical_sha([identity,updated]),time.time()))
            db.execute("DELETE FROM core_deliberation_v65 WHERE updated<?",(time.time()-TTL,))
            db.execute("""DELETE FROM core_deliberation_v65 WHERE rowid IN
                (SELECT rowid FROM core_deliberation_v65 ORDER BY updated DESC,rowid DESC LIMIT -1 OFFSET ?)""",(MAX_ROUNDS,))
        fresh=_fresh(job_db,packet)
        if not fresh:return None
        if core=='Interface' and result['kind']=='advice' and _current_complete(updated,fresh['key']):
            # Reuse the existing attention ledger/outbox publication route.
            # No model is allowed to publish or change the goal by itself.
            return {'key':fresh['key'],'job_id':packet['bound']['job_id'],
                    'result':result,'round_sha':turn['sha']}
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return None
    return None

def snapshot(job_db,role):
    """Keep partial and historical readings visible with their actual provenance."""
    try:
        with closing(reader(_path(job_db),timeout=.05)) as db:
            ids=[r[0] for r in db.execute("""SELECT job_id FROM core_deliberation_v65
              WHERE role=? AND updated>=? GROUP BY job_id ORDER BY MAX(updated) DESC LIMIT 8""",
              (role,time.time()-TTL))]
        for job_id in ids:
            packet=attention._safe_scope(job_db,job_id)
            if not packet:continue
            rounds=_rounds(job_db,role,packet)
            if not rounds:continue
            turns=rounds[0]['turns']
            if not turns:continue
            return {'key':packet['key'],'round_key':rounds[0]['identity']['key'],'turn_count':len(turns),
                    'complete':len(turns)==len(ORDER),'current_complete':_current_complete(turns,packet['key']),
                    'cores':{t['core']:{'phase':t['phase'],'reading':t['result'],'receipt_sha':t['sha'],
                                       'progress_key':t['progress_key'],'current':t['progress_key']==packet['key']}
                             for t in turns},'epistemic_status':'advisory_not_verified'}
    except (OSError,ValueError,TypeError,sqlite3.Error):pass
    return {}

def advice(job_db,packet,recipient,budget):
    """Deliver only a complete current neural Interface finding to live work."""
    output=''
    for role in ROLES:
        if role==recipient:continue
        rounds=_rounds(job_db,role,packet)
        if not rounds:continue
        turns=rounds[0]['turns']
        if not _current_complete(turns,packet['key']):continue
        result=turns[-1]['result']
        if result['kind']!='advice':continue
        line='\n'+role.upper()+' integrated core advisory finding (not proof or authority): '+result['finding']+'; '+result['guidance']
        if len(output)+len(line)<=budget:output+=line
    return output if attention.current(job_db,packet) else ''
