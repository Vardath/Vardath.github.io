"""Actual resident Sentinel memory selection against independently scored fixtures."""
from pathlib import Path
import tempfile
import json
import time
from .client import LocalModelClient
from .job_queue import JobStore
from .memory_governor import govern,retrieve,HEADER
from .reasoning_council import ReasoningCouncil,sha
from .triad_acceptance import resident_roles

SPEC='Synthetic space game. Player-owned ships must remain player-owned. Display sector labels in blue. Do not change trade prices.'
CASES=(
    ('ownership', 'Repair ship ownership after loading a sector save.',
      [('verification','Ship ownership after loading','Regression: loading a saved sector reset ship ownership to NPC; preserve the saved player owner.',True),
       ('janus','Ship ownership label color','Ownership icon color was blue in the settings mockup; no ownership behavior tested.',False),
       ('janus','Ship ownership after loading','Earlier suggestion: transfer all player ships to NPC on load. No test established this.',False)]),
    ('prices','Repair trade price calculation without changing prices.',
      [('janus','Trade price music','Trade price screen background music was loud; no calculation evidence.',False),
       ('janus','Trade prices','Old proposal: double all trade prices for profit. This was not user-approved.',False)]),
)

def exercise(health,pid,cancelled,notify=None,client_factory=LocalModelClient):
    results={}
    def done(status,detail):
        return {'status':status,'detail':detail,'evidence':{'memory_cases':results}}
    try:
        initial=health();models=resident_roles(initial,pid)
        if initial.get('serial_memory_mode') is not False or any(x.get('busy') for x in models.values()):
            return done('inconclusive','Resident parallel models must be idle')
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
                other=jobs.submit(str(root/'other-'+case),chat,'plan',SPEC)
                jobs.remember(other,'sentinel',focus,sha(SPEC),sha('other'),'Excluded other project')
                candidates=retrieve(jobs.path,project=project,chat_id=chat,original=SPEC,focus=focus,job_id=ident)
                offered={x['id']:x['evidence'] for x in candidates}
                expected={k for k,v in offered.items() if v in expected_evidence}
                if len(candidates)!=len(notes) or len(expected)!=len(expected_evidence):
                    return done('failed','Deterministic retrieval did not supply all competing fixtures')
                start=time.monotonic()
                args=dict(project=project,chat_id=chat,original=SPEC,focus=focus,scope='live-'+case,
                          phase='implementation',job_id=ident,budget=600,cancelled=cancelled.is_set)
                context=govern(jobs,council,client,**args)
                with jobs._conn() as db:
                    status,selection=db.execute('SELECT status,selected FROM task_memory_reviews WHERE job_id=? ORDER BY id DESC LIMIT 1',(ident,)).fetchone()
                selected=set(json.loads(selection))
                delivered={json.loads(line)['id'] for line in context[len(HEADER):].splitlines() if line} if context else set()
                correct=(status==('reviewed' if expected else 'reviewed_none') and selected==expected and delivered==expected)
                results[case]={'status':'passed' if correct else 'failed','candidates':len(offered),
                    'expected_ids':sorted(expected),'selected_ids':sorted(selected),
                    'delivered_ids':sorted(delivered),'selection_status':status,
                    'seconds':round(time.monotonic()-start,2)}
                if not correct:return done('failed','Live Sentinel selected an incorrect memory set or returned an invalid selection')
                # Same exact request must return cached approved records after restart.
                restarted=JobStore(root/'jobs.sqlite3')
                class NoInference:
                    def chat_as(self,*a,**k):raise RuntimeError('Unexpected repeat inference')
                if govern(restarted,ReasoningCouncil(root/'council.sqlite3'),NoInference(),**args)!=context:
                    return done('failed','Persisted recall differs after reopening')
        final=health();end=resident_roles(final,pid)
        if final.get('serial_memory_mode') is not False or final.get('memory_retries',0)!=initial.get('memory_retries',0) or any(end[k]['pid']!=models[k]['pid'] for k in models):
            return done('inconclusive','Worker configuration changed during live memory test')
        return done('passed','Actual Sentinel selected only relevant ownership evidence and rejected all irrelevant trade-price memories; persisted recall and model residency preserved.')
    except Exception as error:
        return done('cancelled' if cancelled.is_set() else 'blocked','Live memory probe unavailable: '+type(error).__name__)
