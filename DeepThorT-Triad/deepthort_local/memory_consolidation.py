"""Consolidate actual named test observations without inventing semantic facts.

Only the desktop's observed, source-bound named test trace producer writes
these records. No LLM text may promote a proposal. All observations remain
in the authoritative journal; the recall view is derived and reversible.
"""
import json
import re
from pathlib import Path
from .task_memory import sha,append_note
from .test_execution_trace import fingerprint
PREFIX='Named test observation v24: '
HEX=re.compile(r'[a-f0-9]{64}')
TEST=re.compile(r'[\w.]+\.test_\w+')
MAX_PER_TRACE=64

def canonical(value):
    return json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False)

def parse(note):
    if not note.startswith(PREFIX):return None
    try:
        obj=json.loads(note[len(PREFIX):])
        if (not isinstance(obj,dict) or set(obj)!={'test','baseline','status'}
            or not isinstance(obj['test'],str) or len(obj['test'])>240 or not TEST.fullmatch(obj['test'])
            or not isinstance(obj['baseline'],str) or not HEX.fullmatch(obj['baseline'])
            or obj['status'] not in ('passed','failed')):return None
        return obj
    except (ValueError,TypeError,KeyError):return None

def record_trace(jobs,job,original,trace):
    """Record bounded complete observed names, never inferred requirements.

    The supplied trace is built by the fixed local verification path from
    stable before/after sources. Even a passing named test is only historical
    evidence, not proof of current correctness or semantic coverage.
    """
    if (trace.get('schema')!='deepthort-test-execution-v1'
        or trace.get('job_id')!=job['id']
        or trace.get('project')!=str(Path(job['project']).resolve())
        or trace.get('spec_sha256')!=sha(original)
        or trace.get('complete_named_run') is not True):return 0
    hashes=trace.get('source_hashes')
    argv=trace.get('argv_sha256')
    if (not isinstance(hashes,dict) or not hashes or not isinstance(argv,str) or not HEX.fullmatch(argv)
        or any(not isinstance(k,str) or not isinstance(v,str) or not HEX.fullmatch(v) for k,v in hashes.items())):
        return 0
    baseline=sha(canonical([hashes,argv]))
    evidence=fingerprint(trace);observed={}
    for file in trace.get('files',[]):
        if hashes.get(file['path'])!=file['sha256']:continue
        for row in file['tests']:
            name=row['test'];status=row['status']
            if (isinstance(name,str) and len(name)<=240 and TEST.fullmatch(name)
                and ((status=='passed' and trace['exit_code']==0)
                     or (status=='failed' and trace['exit_code']!=0))):
                observed.setdefault(name,[]).append(status)
    changed=0
    with jobs._conn() as db:
        current=db.execute('SELECT project,chat_id FROM jobs WHERE id=?',(job['id'],)).fetchone()
        if not current or tuple(current)!=(job['project'],job['chat_id']):return 0
        for name,states in sorted(observed.items())[:MAX_PER_TRACE]:
            if len(states)!=1:continue
            note=PREFIX+canonical({'test':name,'baseline':baseline,'status':states[0]})
            changed+=int(append_note(db,job['id'],'verification','Named test '+name,
                                      sha(original),evidence,note))
    if changed:jobs.journal(job['id'])
    return changed

def recall_group(db,row,project,chat_id,spec_sha):
    """Return one representative and a digest binding every matching observation.

    Contradictory outcomes on identical pinned inputs are explicitly uncertain.
    Distinct baselines are distinct histories, not contradictory observations.
    """
    if row['role']!='verification':return None
    claim=parse(row['note'])
    if not claim or row['focus']!='Named test '+claim['test']:return None
    related=[]
    for other in db.execute("""SELECT n.id,n.note,n.evidence_sha FROM task_memory_notes n
        JOIN jobs j ON j.id=n.job_id WHERE j.project=? AND j.chat_id=? AND n.spec_sha=?
        AND n.role='verification' AND n.focus=? ORDER BY n.id""",(project,chat_id,spec_sha,row['focus'])):
        parsed=parse(other['note'])
        if parsed and parsed['test']==claim['test'] and parsed['baseline']==claim['baseline']:
            related.append((other['id'],other['evidence_sha'],parsed['status']))
    if not related:return None
    statuses={x[2] for x in related}
    if len(statuses)>1:
        observation='Conflicting named test outcomes on the same recorded input baseline (pass and fail); rerun this test. No current result established.'
    else:
        observation='Historical named test '+next(iter(statuses))+f'; {len(related)} recorded observation(s), baseline '+claim['baseline'][:12]+'. Revalidate current inputs.'
    return {'id':'N'+str(related[0][0]),'kind':'historical_verification',
            'focus':row['focus'][:100],'observation':observation,
            'evidence':sha(canonical([claim['test'],claim['baseline'],related]))}
