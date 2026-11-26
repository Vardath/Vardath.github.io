"""V70 governed, inert self-development preparation.

An observed diagnostic inconsistency is investigated by JANUS, implemented
as a bounded text-only candidate by Granite, and independently reviewed by
Sentinel. Only exact source snapshots and inert staged files are written.
No live code, installation, shell command, execution grant or runtime
configuration is changed. Static evidence is not runtime acceptance.
"""
import ast
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from .agent_contract import canonical_sha
from .structured_source import strict_json
from .workspace import safe_target
from .flight_recorder import record

TARGET='deepthort_local/diagnostics.py'
CAP_SOURCE='deepthort_local/win_cpu_cap.py'
MAX_BYTES=32000

def _source(root,name):
    path=safe_target(root,name,must_exist=True)
    if path.stat().st_size>MAX_BYTES:raise ValueError('Self-inspection source too large')
    return path.read_bytes().decode('utf-8')

def _sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def observe(root):
    """First supported detector: exact stale diagnostic resource-cap text."""
    source=_source(root,TARGET)
    caps_source=_source(root,CAP_SOURCE)
    caps={}
    for node in ast.parse(caps_source).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            name=node.targets[0].id
            if name in ('MAX_CPU_PERCENT','MAX_RAM_PERCENT') and isinstance(node.value,ast.Constant) and type(node.value.value) is int:
                caps[name]=node.value.value
    if set(caps)!={'MAX_CPU_PERCENT','MAX_RAM_PERCENT'}:return None
    matches=[node.value for node in ast.walk(ast.parse(source)) if isinstance(node,ast.Constant)
             and isinstance(node.value,str) and node.value.startswith('System resource protection:')]
    if len(matches)!=1:return None
    old=matches[0]
    if all(str(value)+'%' in old for value in caps.values()):return None
    evidence={'target':TARGET,'base_sha':_sha(source),'cap_source_sha':_sha(caps_source),
              'observed':old,'caps':caps,'detector':'diagnostic_cap_text_v70'}
    return {'key':canonical_sha(evidence),'evidence':evidence,'source':source}

def _ensure(db):
    db.execute("""CREATE TABLE IF NOT EXISTS self_development_v70(
        key TEXT PRIMARY KEY, state TEXT NOT NULL, body TEXT NOT NULL,
        sha TEXT NOT NULL, updated REAL NOT NULL)""")

def _load(db,key):
    row=db.execute('SELECT state,body,sha FROM self_development_v70 WHERE key=?',(key,)).fetchone()
    if not row:return None
    body=json.loads(row[1])
    if canonical_sha(body)!=row[2] or body.get('state')!=row[0] or body.get('key')!=key:
        raise ValueError('Self-development receipt changed')
    return body

def _save(db,body,prior):
    db.execute('BEGIN IMMEDIATE')
    current=_load(db,body['key'])
    if current!=prior:raise ValueError('Concurrent self-development stage changed')
    db.execute('INSERT OR REPLACE INTO self_development_v70 VALUES(?,?,?,?,?)',
        (body['key'],body['state'],json.dumps(body,sort_keys=True),canonical_sha(body),time.time()))

def _plan(answer):
    obj=strict_json(answer.strip())
    if not isinstance(obj,dict) or set(obj)!={'action','reason','test'} or obj['action'] not in ('repair','none'):
        raise ValueError('Invalid self-development plan')
    for key in ('reason','test'):
        if not isinstance(obj[key],str) or not 1<=len(obj[key])<=300 or any(ord(c)<32 for c in obj[key]):
            raise ValueError('Invalid bounded self-development plan')
    return obj

def _candidate(observed,answer):
    obj=strict_json(answer.strip())
    if not isinstance(obj,dict) or set(obj)!={'replacement'}:
        raise ValueError('Expected one diagnostic string replacement')
    new=obj['replacement'];old=observed['evidence']['observed'];source=observed['source']
    if not isinstance(new,str) or not 20<=len(new)<=400 or any(ord(c)<32 for c in new):
        raise ValueError('Invalid diagnostic replacement')
    if not new.startswith('System resource protection:') or 'up to' not in new.lower():
        raise ValueError('Diagnostic must distinguish configured maximum from measured enforcement')
    caps=observed['evidence']['caps']
    if not all(str(value)+'%' in new for value in caps.values()) or '35%' in new:
        raise ValueError('Candidate fails exact observed cap regression')
    # Change only the single AST string literal, not executable syntax.
    tree=ast.parse(source)
    matches=[x for x in ast.walk(tree) if isinstance(x,ast.Constant) and x.value==old]
    if len(matches)!=1:raise ValueError('Diagnostic literal is ambiguous')
    literal=matches[0]
    segment=ast.get_source_segment(source,literal)
    if not segment or source.count(segment)!=1:raise ValueError('Exact literal not unique')
    candidate=source.replace(segment,repr(new),1)
    literal.value=new
    if ast.dump(tree,include_attributes=False)!=ast.dump(ast.parse(candidate),include_attributes=False):
        raise ValueError('Candidate changes executable structure')
    compile(candidate,TARGET,'exec')  # compilation only, never execution
    return {'replacement':new,'candidate_sha':_sha(candidate),
            'static_checks':['exact_base_and_cap_source','exact_cap_values','single_string_literal_ast_equivalence','python_compile'],
            'source':candidate}

def _review(answer,candidate):
    obj=strict_json(answer.strip())
    if not isinstance(obj,dict) or set(obj)!={'accepted','reason','candidate_sha'} or type(obj['accepted']) is not bool:
        raise ValueError('Invalid independent review')
    if obj['candidate_sha']!=candidate['candidate_sha'] or not isinstance(obj['reason'],str) or not 1<=len(obj['reason'])<=300:
        raise ValueError('Review not bound to exact staged source')
    return obj

def _stage(state,observed,candidate,body):
    state=Path(state).resolve(strict=True)
    parent=state/'self-development'
    if parent.is_symlink():raise ValueError('Linked staging directory')
    parent.mkdir(exist_ok=True)
    folder=parent/observed['key']
    # Never overwrite an older candidate or reuse a partial stage after a crash.
    folder.mkdir(exist_ok=False)
    for name,text in [('baseline.py.txt',observed['source']),('candidate.py.txt',candidate['source'])]:
        with (folder/name).open('x',encoding='utf-8',newline='') as stream:stream.write(text)
    manifest={**body,'target':TARGET,'baseline_sha':observed['evidence']['base_sha'],
              'candidate_sha':candidate['candidate_sha'],'runtime_verified':False,
              'installation_authorized':False,'rollback':'Retained exact baseline; no live source was replaced.'}
    with (folder/'manifest.json').open('x',encoding='utf-8') as stream:json.dump(manifest,stream,indent=2,sort_keys=True)
    return folder

def run_once(root,state,client,stopped,*,available=lambda role:True):
    if stopped():return None
    observed=observe(root)
    if not observed:return None
    state=Path(state).resolve(strict=True);path=state/'self-development.sqlite3'
    with closing(sqlite3.connect(path,timeout=2)) as db,db:
        _ensure(db);prior=_load(db,observed['key'])
    phase=prior['state'] if prior else 'observed'
    if phase not in ('observed','planned','candidate'):return None
    role={'observed':'janus','planned':'implementation','candidate':'sentinel'}[phase]
    if not available(role) or stopped():return None
    evidence=json.dumps(observed['evidence'],ensure_ascii=False)
    common=('Governed application self-development: improve only diagnostic wording, never change resource enforcement, models, permissions, or executable logic. '
            'No installation or execution is authorized. Exact observed source evidence: '+evidence+'\n')
    if phase=='observed':
        prompt=common+'Return JSON {"action":"repair" or "none","reason":"specific diagnosis","test":"testable check"}.'
    elif phase=='planned':
        prompt=common+'JANUS plan: '+json.dumps(prior['plan'])+'\nReturn ONLY JSON {"replacement":"one corrected diagnostic sentence"}. Include actual CPU limit and up to the observed RAM-sized commit maximum; do not claim enforcement was tested.'
    else:
        prompt=common+'JANUS plan: '+json.dumps(prior['plan'])+'\nGranite candidate and static checks: '+json.dumps(prior['candidate'])+'\nIndependently reject misleading wording or any unsupported assurance. Return JSON {"accepted":true or false,"reason":"specific review","candidate_sha":"exact candidate hash"}.'
    answer=client.chat_as(role,'self-development-'+observed['key'][:20]+'-'+phase,prompt,max_tokens=256)
    fresh=observe(root)
    if stopped() or not fresh or fresh['key']!=observed['key']:return None
    body=prior.copy() if prior else {'key':observed['key'],'evidence':observed['evidence'],'authority':False}
    if phase=='observed':
        body['plan']=_plan(answer);body['state']='planned' if body['plan']['action']=='repair' else 'declined'
    elif phase=='planned':
        candidate=_candidate(observed,answer)
        body['candidate']={k:v for k,v in candidate.items() if k!='source'}
        body['state']='candidate'
    else:
        candidate=_candidate(observed,json.dumps({'replacement':prior['candidate']['replacement']}))
        if candidate['candidate_sha']!=prior['candidate']['candidate_sha']:raise ValueError('Candidate changed')
        body['review']=_review(answer,candidate)
        body['state']='staged' if body['review']['accepted'] else 'rejected'
        if body['state']=='staged':
            if stopped():return None
            _stage(state,observed,candidate,body)
    with closing(sqlite3.connect(path,timeout=2)) as db,db:
        _save(db,body,prior)
    record(state,'desktop','self_development_stage',stage=body['state'],scope_sha=observed['key'])
    return body
