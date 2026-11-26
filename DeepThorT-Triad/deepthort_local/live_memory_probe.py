"""Actual resident Sentinel memory selection against independently scored fixtures."""
from pathlib import Path
import tempfile
import json
import time
from .client import LocalModelClient
from .job_queue import JobStore
from .memory_governor import govern,retrieve,HEADER,evidence_eligible,parse_selection
from .reasoning_council import ReasoningCouncil,sha
from .triad_acceptance import resident_roles
from .triad_errors import WorkerFailure,http_failure,error_record
from urllib.error import HTTPError

SPEC='Synthetic space game. Player-owned ships must remain player-owned. Display sector labels in blue. Do not change trade prices.'
CASES=(
    ('ownership', 'Repair ship ownership after loading a sector save.',
      [('verification','Ship ownership after loading','Regression: loading a saved sector reset ship ownership to NPC; preserve the saved player owner.',True),
       ('janus','Ship ownership label color','Ownership icon color was blue in the settings mockup; no ownership behavior tested.',False),
       ('janus','Ship ownership after loading','Earlier suggestion: transfer all player ships to NPC on load. No test established this.',False),
       ('verification','Ship ownership icon','Visual test: ownership icon displays blue. No save or ownership logic was exercised.',False)]),
    ('prices','Repair trade price calculation without changing prices.',
      [('janus','Trade price music','Trade price screen background music was loud; no calculation evidence.',False),
       ('janus','Trade prices','Old proposal: double all trade prices for profit. This was not user-approved.',False),
       ('verification','Trade price screen audio','Audio test: music plays on trade price screen. No calculation was exercised.',False)]),
    ('advice_only','Repair docking permission validation.',
      [('janus','Docking permission validation','Untested suggestion: bypass docking permission validation.',False)]),
)

def exercise(health,pid,cancelled,notify=None,client_factory=LocalModelClient,*,idle_wait_seconds=120,use_memory_core=False):
    results={};case=None;start=None
    def done(status,detail):
        return {'status':status,'detail':detail,'evidence':{'memory_cases':results}}
    try:
        initial=health();models=resident_roles(initial,pid)
        if use_memory_core:
            from .memory_core_probe import resident_memory
            memory_pid=resident_memory(initial,pid)['pid']
        if initial.get('serial_memory_mode') is not False:
            return done('inconclusive','Resident parallel model mode required')
        # Preserve the exact oracle. Only defer the start while real inference
        # drains; never terminate a live request or change model residency.
        deadline=time.monotonic()+min(120,max(0,idle_wait_seconds))
        original_pids={role:x['pid'] for role,x in models.items()}
        while any(x.get('busy') for x in models.values()) or (use_memory_core and initial.get('memory_model',{}).get('busy')):
            if cancelled.is_set():return done('cancelled','Stopped waiting for idle models')
            remaining=deadline-time.monotonic()
            if remaining<=0:return done('inconclusive','Resident parallel models remained busy; retry when idle')
            if notify:notify('waiting for resident models to become idle')
            if cancelled.wait(min(1,remaining)):return done('cancelled','Stopped waiting for idle models')
            current=health();models=resident_roles(current,pid)
            if use_memory_core:
                if resident_memory(current,pid)['pid']!=memory_pid:
                    return done('inconclusive','Memory specialist changed while waiting for idle')
                initial['memory_model']=current['memory_model']
            if (current.get('serial_memory_mode') is not False
                    or current.get('memory_retries',0)!=initial.get('memory_retries',0)
                    or any(x['pid']!=original_pids[role] for role,x in models.items())):
                return done('inconclusive','Worker configuration changed while waiting for idle models')
        if cancelled.is_set():return done('cancelled','Stopped')
        with tempfile.TemporaryDirectory(prefix='triad-live-memory-') as folder:
            root=Path(folder);jobs=JobStore(root/'jobs.sqlite3')
            client=client_factory(root/'sessions.sqlite3')
            council=ReasoningCouncil(root/'council.sqlite3')
            for case,focus,notes in CASES:
                if cancelled.is_set():return done('cancelled','Stopped')
                if notify:notify(case)
                project=str(root/case);chat='fixture-'+case
                old=jobs.submit(project,chat,'plan',SPEC)
                ident=jobs.submit(project,chat,'plan',SPEC)
                expected_evidence=set()
                for role,title,note,relevant in notes:
                    evidence=sha(note)
                    jobs.remember(old,role,title,sha(SPEC),evidence,note)
                    if relevant:expected_evidence.add(evidence)
                jobs.remember(old,'sentinel',focus,sha(SPEC+' revised'),sha('obsolete'),'Excluded older revision')
                other=jobs.submit(str(root/('other-'+case)),chat,'plan',SPEC)
                jobs.remember(other,'sentinel',focus,sha(SPEC),sha('other'),'Excluded other project')
                candidates=retrieve(jobs.path,project=project,chat_id=chat,original=SPEC,focus=focus,job_id=ident)
                offered={x['id']:x['evidence'] for x in candidates}
                expected={k for k,v in offered.items() if v in expected_evidence}
                if len(candidates)!=len(notes) or len(expected)!=len(expected_evidence):
                    return done('failed','Deterministic retrieval did not supply all competing fixtures')
                start=time.monotonic()
                with council._db() as db:
                    previous={x[0] for x in db.execute("SELECT evidence_sha FROM deliberations WHERE role='MEMORY_SELECT'")}
                args=dict(project=project,chat_id=chat,original=SPEC,focus=focus,scope='live-'+case,
                          phase='implementation',job_id=ident,budget=600,cancelled=cancelled.is_set,
                          use_memory_core=use_memory_core)
                try:
                    context=govern(jobs,council,client,**args)
                except (HTTPError,WorkerFailure) as error:
                    # Read the broker's allowlisted code, never raw native text.
                    failure=http_failure(error) if isinstance(error,HTTPError) else error
                    code=error_record(failure)['code']
                    results[case]={'status':'blocked','candidates':len(offered),
                        'expected_ids':sorted(expected),'error_code':code,
                        'seconds':round(time.monotonic()-start,2)}
                    return done('cancelled' if cancelled.is_set() else 'blocked',
                                'Live Sentinel memory inference did not return a final answer: '+code)
                with jobs._conn() as db:
                    status,selection=db.execute('SELECT status,selected FROM task_memory_reviews WHERE job_id=? ORDER BY id DESC LIMIT 1',(ident,)).fetchone()
                selected=set(json.loads(selection))
                delivered={json.loads(line)['id'] for line in context[len(HEADER):].splitlines() if line} if context else set()
                eligible_ids={x['id'] for x in candidates if evidence_eligible(x)}
                # Advice-only is explicitly a deterministic exclusion test.
                # Other cases must exercise the live model on eligible evidence.
                expected_status='provenance_withheld' if case=='advice_only' else ('reviewed' if expected else 'reviewed_none')
                correct=(status==expected_status and selected==expected and delivered==expected
                         and (not eligible_ids if case=='advice_only' else bool(eligible_ids)))
                results[case]={'status':'passed' if correct else 'failed','candidates':len(offered),
                    'expected_ids':sorted(expected),'eligible_ids':sorted(eligible_ids),'selected_ids':sorted(selected),
                    'delivered_ids':sorted(delivered),'selection_status':status,
                    'seconds':round(time.monotonic()-start,2)}
                if use_memory_core:
                    with council._db() as db:
                        proposals=[x[1] for x in db.execute("SELECT evidence_sha,answer FROM deliberations WHERE role='MEMORY_SELECT'") if x[0] not in previous]
                    try:
                        if eligible_ids:
                            if len(proposals)!=1:raise ValueError('No unique specialist response')
                            proposed=set(parse_selection(proposals[0],eligible_ids))
                            own_correct=proposed==expected
                        else:
                            proposed=set()
                            own_correct=not proposals
                        results[case]['memory_core_selected_ids']=sorted(proposed)
                    except (ValueError,TypeError,KeyError):
                        own_correct=False
                    results[case]['memory_core_status']='passed' if own_correct else 'failed'
                    results[case]['memory_core_calls']=len(proposals)
                if not correct:return done('failed','Live governed memory selected an incorrect set or returned an invalid selection')
                # Same exact request must return cached approved records after restart.
                restarted=JobStore(root/'jobs.sqlite3')
                class NoInference:
                    def chat_as(self,*a,**k):raise RuntimeError('Unexpected repeat inference')
                if govern(restarted,ReasoningCouncil(root/'council.sqlite3'),NoInference(),**args)!=context:
                    return done('failed','Persisted recall differs after reopening')
        final=health();end=resident_roles(final,pid)
        if use_memory_core and resident_memory(final,pid)['pid']!=memory_pid:
            return done('inconclusive','Fifth worker changed during live recall')
        if final.get('serial_memory_mode') is not False or final.get('memory_retries',0)!=initial.get('memory_retries',0) or any(end[k]['pid']!=models[k]['pid'] for k in models):
            return done('inconclusive','Worker configuration changed during live memory test')
        if use_memory_core:
            return done('passed','Actual fifth-model proposals and independent Sentinel review exercised on exact memory oracles; scoped provenance, persisted recall and residency preserved. See memory_core check for independent fifth-model accuracy.')
        return done('passed','Actual Sentinel selected relevant ownership evidence and rejected unrelated recorded observations; advisory-only provenance exclusion, persisted recall and model residency preserved.')
    except Exception as error:
        import traceback
        frame=traceback.extract_tb(error.__traceback__)[-1]
        # Synthetic fixture only; report exception type and exact source location, not private model content.
        return done('cancelled' if cancelled.is_set() else 'blocked','Live memory probe unavailable: '+type(error).__name__+' at '+Path(frame.filename).name+':'+str(frame.lineno))
