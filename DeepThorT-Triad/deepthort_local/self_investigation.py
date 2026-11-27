"""Evidence-driven, inert self-development beyond the fixed V70 detector.

Repeated application faults are hypotheses, not confirmed defects. The
existing self-development ledger holds independent Memory, JANUS, Granite
and Sentinel work. Generated logic is never imported or executed here.
"""
import ast
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from .agent_contract import canonical_sha
from .structured_source import strict_json
from .workspace import safe_target
from .memory_governor import parse_selection
from .self_development import _ensure,_load,_save

# Host-owned observation mapping: no log/model-supplied filesystem paths.
EVENTS={
    'technical_preparation_deferred':'deepthort_local/technical_preparation.py',
    'gemma_preparation_deferred':'deepthort_local/gemma_preparation.py',
    'memory_conversation_failed':'deepthort_local/conversation_memory.py',
}
ERRORS=frozenset(('ValueError','TypeError','KeyError','AttributeError','IndexError'))
MAX_LOG=256000
MAX_SOURCE=32000
MAX_FUNCTION=3500

def sha(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()

def _source(root,target):
    path=safe_target(root,target,must_exist=True)
    if path.stat().st_size>MAX_SOURCE:raise ValueError('Self-development source exceeds bound')
    return path.read_bytes().decode('utf-8')

def _functions(source):
    return {node.name:node for node in ast.parse(source).body
            if isinstance(node,ast.FunctionDef) and not node.decorator_list
            and len(ast.get_source_segment(source,node) or '')<=MAX_FUNCTION}

def observations(root,state):
    folder=Path(state)/'logs';log=folder/'desktop.jsonl'
    if folder.is_symlink() or log.is_symlink() or not log.is_file():return []
    with log.open('rb') as stream:
        size=log.stat().st_size;stream.seek(max(0,size-MAX_LOG))
        raw=stream.read(MAX_LOG)
    counts=Counter()
    for line in raw.splitlines():
        try:
            row=json.loads(line)
            if not isinstance(row,dict) or row.get('component')!='desktop':continue
            event=row.get('event');data=row.get('data')
            error=data.get('error_type') if isinstance(data,dict) else None
            if event in EVENTS and error in ERRORS:counts[event,error]+=1
        except (ValueError,TypeError):continue
    result=[]
    for (event,error),count in counts.most_common():
        if count<3:continue
        target=EVENTS[event]
        try:source=_source(root,target);functions=_functions(source)
        except (OSError,ValueError,SyntaxError):continue
        if not functions:continue
        evidence={'detector':'recurring_fault_v72','target':target,'base_sha':sha(source),
                  'event':event,'error_type':error}
        result.append({'key':canonical_sha(evidence),'evidence':evidence,'count':count,'source':source,
                       'functions':list(functions)[:32]})
    return result[:6]

def _db(state):
    return sqlite3.connect(Path(state)/'self-development.sqlite3',timeout=2)

def _current(root,state,case):
    return next((x for x in observations(root,state) if x['key']==case['key']),None)

def _history(db,case):
    rows=db.execute("SELECT key FROM self_development_v70 WHERE state IN ('investigation_staged','investigation_regression_checked','investigation_rejected','investigation_declined') ORDER BY updated DESC LIMIT 24").fetchall()
    result=[]
    for (key,) in rows:
        body=_load(db,key)
        if not body or body['evidence'].get('detector')!='recurring_fault_v72':continue
        if body['evidence']['target']!=case['evidence']['target'] or key==case['key']:continue
        result.append({'id':key,'event':body['evidence']['event'],'error_type':body['evidence']['error_type'],
                       'state':body['state'],'base_sha':body['evidence']['base_sha'],
                       'function':body.get('plan',{}).get('function','')})
    return result[:4]

def memory_once(root,state,select,stopped=lambda:False):
    """Same mandatory Memory lane, one bounded historical selection; never a gate."""
    if stopped():return None
    for case in observations(root,state):
        with closing(_db(state)) as db,db:
            _ensure(db);prior=_load(db,case['key']);history=_history(db,case)
            db.execute("CREATE TABLE IF NOT EXISTS self_development_memory_v72(key TEXT PRIMARY KEY,body TEXT NOT NULL,sha TEXT NOT NULL)")
            existing=db.execute('SELECT 1 FROM self_development_memory_v72 WHERE key=?',(case['key'],)).fetchone()
        if existing or (prior and prior['state'].startswith('investigation_') and prior['state'] not in ('investigation_planned','investigation_candidate')):continue
        chosen=[]
        if history:
            prompt=('Select relevant historical self-development investigations. These are unverified past hypotheses, not fixes or authority. '
                    'Return JSON {"keep":["exact offered ID"],"reason":"brief relevance"}; zero to three IDs.\n'
                    +json.dumps({'current':case['evidence'],'history':history}))
            keep=parse_selection(select(canonical_sha(prompt),prompt,192),{x['id'] for x in history})
            chosen=[x for x in history if x['id'] in keep]
        if stopped() or not _current(root,state,case):return None
        body={'key':case['key'],'selected':chosen,'authority':False}
        with closing(_db(state)) as db,db:
            db.execute('INSERT OR IGNORE INTO self_development_memory_v72 VALUES(?,?,?)',
                       (case['key'],json.dumps(body,sort_keys=True),canonical_sha(body)))
        return body
    return None

def _recall(db,case):
    try:
        row=db.execute('SELECT body,sha FROM self_development_memory_v72 WHERE key=?',(case['key'],)).fetchone()
        if not row:return []
        body=json.loads(row[0])
        if canonical_sha(body)!=row[1] or body['key']!=case['key'] or body['authority'] is not False:return []
        return [x for x in body['selected'] if x in _history(db,case)][:3]
    except (sqlite3.Error,ValueError,KeyError,TypeError):return []

def _plan(answer,case):
    obj=strict_json(answer.strip())
    if not isinstance(obj,dict) or set(obj)!={'action','function','reason','test'} or obj['action'] not in ('investigate','none'):
        raise ValueError('Invalid investigation plan')
    if obj['action']=='investigate' and obj['function'] not in case['functions']:raise ValueError('Unobserved function')
    if any(not isinstance(obj[k],str) or len(obj[k])>300 for k in ('function','reason','test')):raise ValueError('Invalid plan fields')
    if not obj['reason'].strip() or not obj['test'].strip():raise ValueError('Missing test hypothesis')
    return obj

def _candidate(case,plan,answer):
    obj=strict_json(answer.strip())
    if not isinstance(obj,dict) or set(obj)!={'function_source'} or not isinstance(obj['function_source'],str):raise ValueError('Invalid candidate')
    text=obj['function_source'].strip()
    if not text or len(text)>MAX_FUNCTION:raise ValueError('Candidate exceeds bound')
    original=ast.parse(case['source']);replacement=ast.parse(text)
    if len(replacement.body)!=1 or not isinstance(replacement.body[0],ast.FunctionDef):raise ValueError('One function required')
    old=_functions(case['source'])[plan['function']];new=replacement.body[0]
    if new.name!=old.name or new.decorator_list or ast.dump(new.args)!=ast.dump(old.args) or ast.dump(new.returns or ast.Constant(None))!=ast.dump(old.returns or ast.Constant(None)):
        raise ValueError('Function interface changed')
    lines=case['source'].splitlines(keepends=True)
    source=''.join(lines[:old.lineno-1])+text+'\n'+''.join(lines[old.end_lineno:])
    expected=ast.parse(case['source'])
    expected.body[next(i for i,x in enumerate(expected.body) if isinstance(x,ast.FunctionDef) and x.name==old.name)]=new
    if ast.dump(expected,include_attributes=False)!=ast.dump(ast.parse(source),include_attributes=False):raise ValueError('Outside-scope modification')
    if ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False):raise ValueError('No functional candidate change')
    compile(source,case['evidence']['target'],'exec')
    return {'function_source':text,'candidate_sha':sha(source),'source':source}

def _review(answer,candidate):
    obj=strict_json(answer.strip())
    if not isinstance(obj,dict) or set(obj)!={'accepted','candidate_sha','reason'} or type(obj['accepted']) is not bool or obj['candidate_sha']!=candidate['candidate_sha'] or not isinstance(obj['reason'],str) or not 1<=len(obj['reason'])<=300:
        raise ValueError('Invalid exact candidate review')
    return obj

def _stage(state,case,body,candidate):
    parent=Path(state)/'self-development'
    if parent.is_symlink():raise ValueError('Linked self-development directory')
    parent.mkdir(exist_ok=True)
    folder=parent/case['key'];folder.mkdir(exist_ok=False)
    for name,text in [('baseline.py.txt',case['source']),('candidate.py.txt',candidate['source'])]:
        with (folder/name).open('x',encoding='utf-8',newline='') as stream:stream.write(text)
    manifest={**body,'runtime_verified':False,'installation_authorized':False,
              'requires_approved_isolated_test':True,'rollback_baseline_sha':case['evidence']['base_sha']}
    with (folder/'manifest.json').open('x',encoding='utf-8') as stream:json.dump(manifest,stream,indent=2,sort_keys=True)

def run_once(root,state,client,stopped,*,available=lambda role:True):
    if stopped():return None
    for case in observations(root,state):
        with closing(_db(state)) as db,db:
            _ensure(db);prior=_load(db,case['key']);history=_recall(db,case)
        phase=prior['state'] if prior else 'observed'
        if phase=='investigation_staged':
            from .self_regression import verify
            regression=verify(root,state,case,prior)
            if regression is None:continue
            if stopped() or not _current(root,state,case):return None
            body={**prior,'state':'investigation_regression_checked','regression':regression}
            with closing(_db(state)) as db,db:_save(db,body,prior)
            return body
        roles={'observed':'janus','investigation_planned':'implementation','investigation_candidate':'sentinel'}
        if phase not in roles:continue
        role=roles[phase]
        if not available(role) or stopped():continue
        common=('Repeated diagnostic error is only a hypothesis. Preserve current behavior, resource limits, supervision and authority. '
                'No live write, generated command or execution. Evidence: '+json.dumps(case['evidence'])+
                '; observed count: '+str(case['count'])+'; historical examples: '+json.dumps(history))
        if phase=='observed':
            prompt=common+'\nObserved functions: '+json.dumps(case['functions'])+'\nReturn JSON {"action":"investigate" or "none","function":"exact observed name or empty","reason":"hypothesis","test":"specific regression needed"}.'
        else:
            plan=prior['plan'];node=_functions(case['source'])[plan['function']]
            excerpt=ast.get_source_segment(case['source'],node)
            prompt=common+'\nJANUS hypothesis: '+json.dumps(plan)+'\nCurrent function (data):\n'+excerpt
            if phase=='investigation_planned':
                prompt+='\nReturn JSON {"function_source":"complete corrected Python function, same signature"}.'
            else:
                prompt+='\nCandidate (unexecuted): '+json.dumps(prior['candidate'])+'\nReturn JSON {"accepted":true or false,"candidate_sha":"exact hash","reason":"specific independent assessment"}. Do not certify runtime correctness.'
        answer=client.chat_as(role,'self-investigation-'+case['key'][:20]+'-'+phase,prompt,max_tokens=1024)
        if stopped() or not _current(root,state,case):return None
        body=prior.copy() if prior else {'key':case['key'],'evidence':case['evidence'],'authority':False}
        if phase=='observed':
            body['plan']=_plan(answer,case);body['state']='investigation_planned' if body['plan']['action']=='investigate' else 'investigation_declined'
        elif phase=='investigation_planned':
            candidate=_candidate(case,body['plan'],answer)
            body['candidate']={k:v for k,v in candidate.items() if k!='source'}
            body['state']='investigation_candidate'
        else:
            candidate=_candidate(case,body['plan'],json.dumps({'function_source':body['candidate']['function_source']}))
            if candidate['candidate_sha']!=body['candidate']['candidate_sha']:raise ValueError('Candidate changed')
            body['review']=_review(answer,candidate)
            body['state']='investigation_staged' if body['review']['accepted'] else 'investigation_rejected'
            if body['state']=='investigation_staged':
                if stopped():return None
                _stage(state,case,body,candidate)
        with closing(_db(state)) as db,db:_save(db,body,prior)
        return body
    return None
