"""Role-owned live project attention, not a serial plan/review pipeline.

Reads the existing approved jobs, steps and independently checked Memory
findings. Each cognitive society independently chooses an unfinished
attention opportunity. A stable scope/progress key and bounded receipts
prevent chatter. No result authorizes work; existing grants remain mandatory.
"""
from contextlib import closing
from pathlib import Path
import json
import sqlite3
import time
from .memory_duty import reader,live_scope,signature,DUTY_STATES,observe_memory_duties
from .agent_contract import canonical_sha
from .structured_source import strict_json

ROLES=('janus','sentinel')
TTL=900
MAX_RESULTS=256

def parse(answer):
    data=strict_json(answer.strip())
    if not isinstance(data,dict) or set(data)!={'kind','finding','guidance'} or data['kind'] not in ('none','advice'):
        raise ValueError('Invalid independent attention response')
    for k,cap in (('finding',220),('guidance',320)):
        if not isinstance(data[k],str) or len(data[k])>cap or any(ord(c)<32 for c in data[k]):
            raise ValueError('Invalid attention finding')
    if data['kind']=='none':
        if data['finding'] or data['guidance']:raise ValueError('No finding must be empty')
    elif not data['finding'].strip() or not data['guidance'].strip():raise ValueError('Missing specific advice')
    return data

def _scope(job_db,job_id):
    with closing(reader(job_db,timeout=.15)) as db:
        row=db.execute("SELECT id,approval_key,state FROM jobs WHERE id=? AND mode='build'",(job_id,)).fetchone()
        if not row or row['state'] not in DUTY_STATES:return None
        key=row['approval_key'] or '';parts=key.split(':')
        if len(parts)==4 and parts[0]=='milestone':
            request_id=int(parts[1])
        elif len(parts)==2 and parts[0]=='draft':
            with closing(reader(Path(job_db).parent/'conversations.sqlite3',timeout=.15)) as conv:
                draft=conv.execute("SELECT request_id FROM project_drafts WHERE id=?",(int(parts[1]),)).fetchone()
            if not draft:return None
            request_id=draft[0]
        else:return None
        rows=[dict(r) for r in db.execute("""SELECT id,path,description,state FROM job_steps
             WHERE job_id=? ORDER BY sequence LIMIT 25""",(job_id,))]
    bound=live_scope(job_db,job_id,request_id,states=DUTY_STATES,timeout=.15)
    if not bound or bound['approval_key']!=key or not rows or len(rows)>24:return None
    planned=[s for s in rows if s['state'] in ('planned','proposed')]
    focus=(planned[0]['path']+': '+planned[0]['description'])[:500] if planned else 'Verification of approved project outputs'
    progress={'phase':'production' if row['state'] in ('queued','running') else row['state'],
              'steps':[{**s,'description':s['description'][:500]} for s in rows]}
    identity={'scope':signature(bound),'plan_sha':canonical_sha([{k:r[k] for k in ('id','path','description')} for r in rows]),
              'progress_sha':canonical_sha(rows),
              'phase':progress['phase'],'focus':focus}
    return {'key':canonical_sha(identity),'identity':identity,'bound':bound,'focus':focus,
            'upcoming':planned[:3],'progress':progress}

def _safe_scope(job_db,job_id):
    try:return _scope(job_db,job_id)
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return None

def _path(job_db):return Path(job_db).parent/'janus-counsel.sqlite3'

def ensure(db):
    db.execute("""CREATE TABLE IF NOT EXISTS workflow_attention_v59(
      role TEXT NOT NULL,work_key TEXT NOT NULL,job_id INTEGER NOT NULL,
      identity TEXT NOT NULL,result TEXT NOT NULL,receipt_sha TEXT NOT NULL,
      stamp REAL NOT NULL,PRIMARY KEY(role,work_key))""")

def _envelope(role,packet,result,stamp):
    return {'role':role,'key':packet['key'],'identity':packet['identity'],
            'result':result,'stamp':stamp,'authority':False,'verified':False}

def _recent(job_db,packet,clock=time.time):
    try:
        with closing(reader(_path(job_db),timeout=.05)) as db:
            rows=[dict(r) for r in db.execute("""SELECT * FROM workflow_attention_v59
              WHERE work_key=? ORDER BY stamp DESC""",(packet['key'],))]
        results=[]
        for row in rows:
            if row['role'] not in ROLES or not clock()-TTL<=row['stamp']<=clock():continue
            result=parse(row['result'])
            item=_envelope(row['role'],packet,result,row['stamp'])
            if row['job_id']!=packet['bound']['job_id'] or json.loads(row['identity'])!=packet['identity'] or canonical_sha(item)!=row['receipt_sha']:continue
            results.append(item)
        return results
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return []

def choose(job_db,role):
    if role not in ROLES:raise ValueError('Unknown cognitive role')
    try:
        with closing(reader(job_db,timeout=.15)) as db:
            marks=','.join('?' for _ in DUTY_STATES)
            ids=[r[0] for r in db.execute(f"""SELECT id FROM jobs WHERE mode='build'
             AND approval_key IS NOT NULL AND state IN ({marks}) ORDER BY id LIMIT 32""",DUTY_STATES)]
        # One durable thought per role per stable progress state. Oldest
        # unfinished opportunity wins; no global shared turn or failure gate.
        for job_id in ids:
            packet=_safe_scope(job_db,job_id)
            if not packet:continue
            prior=_recent(job_db,packet)
            if any(r['role']==role for r in prior):continue
            return packet
    except (OSError,ValueError,sqlite3.Error):pass
    return None

def current(job_db,packet):
    fresh=_safe_scope(job_db,packet['bound']['job_id'])
    return bool(fresh and fresh['key']==packet['key'])

def evidence(job_db,packet,*,include_preparation=True):
    bound=packet['bound'];original=bound['original'];focus=packet['focus']
    if len(original)>1400:
        from .recovery_council import select_source_section
        original=('Original beginning (verbatim): '+original[:400]+'\nRelevant original (verbatim): '+
                  select_source_section(original,focus,900))
    memory=[r for r in observe_memory_duties(job_db)['reports']
            if r['job_id']==bound['job_id'] and r['request_id']==bound['request_id']]
    peer=[{'role':r['role'],'result':r['result']} for r in _recent(job_db,packet) if r['result']['kind']=='advice']
    progress={'phase':packet['progress']['phase'],
              'saved':sum(s['state'] in ('saved','verified') for s in packet['progress']['steps']),
              'total':len(packet['progress']['steps']),
              'upcoming':[{**s,'description':s['description'][:300]} for s in packet['upcoming']]}
    preparation=''
    if include_preparation:
        from .technical_preparation import advice as preparation_advice
        preparation=preparation_advice(job_db,bound['job_id'],bound['original'],focus,600)
    return ('Original specification SHA: '+bound['spec_sha']+'\n'+original+
            '\nObserved approved progress: '+json.dumps(progress,ensure_ascii=False)[:1300]+
            '\nRelevant historical Memory observations (not current tests): '+json.dumps(memory,ensure_ascii=False)[:650]+
            '\nIndependent peer findings (advisory): '+json.dumps(peer,ensure_ascii=False)[:500]+preparation)

def finish(job_db,role,packet,answer,*,clock=time.time):
    if role not in ROLES:raise ValueError('Unknown cognitive role')
    result=parse(answer)
    if not current(job_db,packet):return None
    item=_envelope(role,packet,result,clock())
    with closing(sqlite3.connect(_path(job_db),timeout=2)) as db,db:
        ensure(db)
        db.execute('BEGIN IMMEDIATE')
        db.execute("DELETE FROM workflow_attention_v59 WHERE stamp<?",(clock()-TTL,))
        added=db.execute("INSERT OR IGNORE INTO workflow_attention_v59 VALUES(?,?,?,?,?,?,?)",
            (role,packet['key'],packet['bound']['job_id'],json.dumps(packet['identity'],sort_keys=True),
             json.dumps(result,sort_keys=True),canonical_sha(item),item['stamp'])).rowcount
        if not added:return None
        db.execute("""DELETE FROM workflow_attention_v59 WHERE rowid IN
            (SELECT rowid FROM workflow_attention_v59 ORDER BY stamp DESC,rowid DESC LIMIT -1 OFFSET ?)""",(MAX_RESULTS,))
    return item if current(job_db,packet) else None

def advice(job_db,job_id,original,focus,*,recipient='implementation',budget=640):
    """Read already produced role findings at a safe checkpoint, no inference."""
    if recipient not in ('implementation','janus','sentinel') or budget<100:return ''
    packet=_safe_scope(job_db,job_id)
    from .reasoning_council import sha
    if not packet or sha(original)!=packet['bound']['spec_sha'] or focus!=packet['focus']:return ''
    from .technical_preparation import advice as preparation_advice
    output=preparation_advice(job_db,job_id,original,focus,budget)
    for item in _recent(job_db,packet):
        if item['role']==recipient or item['result']['kind']!='advice':continue
        line='\n'+item['role'].upper()+' independent advisory finding (not new authority or proof): '+item['result']['finding']+'; '+item['result']['guidance']
        if len(output)+len(line)<=budget:output+=line
    if budget-len(output)>=100:
        from .core_deliberation import advice as core_advice
        output+=core_advice(job_db,packet,recipient,budget-len(output))
    return output

def run_once(job_db,role,counsel,stopped):
    """Called only from a society's own background thread."""
    if stopped():return None
    packet=choose(job_db,role)
    if not packet or stopped():return None
    answer=counsel.request(society=role,goal=packet['focus'],
        problem='Independently anticipate the next useful action or material risk in this active approved project.',
        evidence=evidence(job_db,packet),initiative=True)
    if not answer or stopped():return None
    try:return finish(job_db,role,packet,answer)
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return None
