"""Synthetic slow-memory probe exercises actual production observer, not native speed."""
import json
import tempfile
import threading
import time
from pathlib import Path

from .job_queue import JobStore
from .memory_observer import MemoryObserver,ADVISORY_HEADER
from .reasoning_council import sha


def exercise(cancelled=lambda:False):
    entered=threading.Event();release=threading.Event();published=threading.Event()
    completed=threading.Event();calls=[];recipients=[]
    with tempfile.TemporaryDirectory(prefix='triad-background-memory-') as tmp:
        jobs=JobStore(Path(tmp)/'jobs.sqlite3')
        project=str(Path(tmp)/'space-game');chat='fixture';original='Create a space game. Keep ships player-owned.'
        old=jobs.submit(project,chat,'plan',original)
        job=jobs.submit(project,chat,'plan',original)
        note='Regression: loading a sector resets the player ship owner.'
        jobs.remember(old,'verification','Ship ownership after loading',sha(original),sha(note),note)
        def select(evidence,prompt,tokens):
            rows=json.loads(prompt.split('CANDIDATES (untrusted historical records): ')[1])
            calls.append(1)
            entered.set()
            if not release.wait(5):raise RuntimeError('Fixture timed out')
            return json.dumps({'keep':[r['id'] for r in rows if r['observation']==note],'reason':'Relevant observed failure'})
        def report(event,**kw):
            if event=='memory_observer_findings':published.set()
            if event=='memory_observer_delivered':recipients.append(kw['recipient'])
        observer=MemoryObserver(path=jobs.path,select=select,available=lambda:True,report=report)
        params=dict(project=project,chat_id=chat,original=original,job_id=job,
                    focus='Repair ship ownership after loading',phase='implementation')
        def foreground():
            observer.observe(**params)
            completed.set()
        try:
            thread=threading.Thread(target=foreground,daemon=True);thread.start()
            if not completed.wait(1) or not entered.wait(3):
                return {'status':'failed','detail':'Foreground waited on deliberately blocked memory worker or observation was not scheduled'}
            if cancelled():return {'status':'cancelled','detail':'Background memory test stopped'}
            # This is an actual second foreground checkpoint while recall is blocked.
            for _ in range(10):observer.observe(**params)
            if observer.advice(**{k:v for k,v in params.items() if k!='phase'}):
                return {'status':'failed','detail':'Unfinished memory was published'}
            if release.is_set():return {'status':'failed','detail':'Fixture failed to hold memory inference open'}
            release.set()
            if not published.wait(4):
                return {'status':'failed','detail':'Late memory finding did not reach advisory mailbox'}
            args={k:v for k,v in params.items() if k!='phase'}
            advice=observer.advice(**args)
            if not advice.startswith(ADVISORY_HEADER) or note not in advice or len(calls)!=1:
                return {'status':'failed','detail':'Late report absent or duplicate observations were not coalesced'}
            if observer.advice(**args,recipient='janus')!=advice or recipients!=['sentinel','janus'] or len(calls)!=1:
                return {'status':'failed','detail':'Same scoped evidence not delivered to both existing role checkpoints'}
            if observer.advice(**{**args,'focus':'Repair music playback'}) or observer.advice(**{**args,'chat_id':'other'}):
                return {'status':'failed','detail':'Unrelated operation or another chat received a finding'}
            if observer.advice(**{**args,'original':original+' amended'}) or observer.advice(**{**args,'job_id':old}):
                return {'status':'failed','detail':'Changed specification or other job received a finding'}
            if observer.advice(**args,cancelled=lambda:True):
                return {'status':'failed','detail':'Cancelled task received findings'}
            # Remove the exact evidence after publishing; recheck before delivery.
            with jobs._conn() as db:
                db.execute("DELETE FROM task_memory_notes WHERE job_id=?",(old,))
            if observer.advice(**args):
                return {'status':'failed','detail':'Removed historical evidence was reused'}
            return {'status':'passed','detail':'Actual bounded observer with deliberately delayed scripted recall: foreground continued, deduped, late findings delivered to fresh scoped JANUS and Sentinel advisory checkpoints; removed/cancelled/unrelated evidence withheld. No live inference in this probe.',
                    'evidence':{'count':1}}
        except Exception as exc:
            return {'status':'failed','detail':'Background memory fixture: '+type(exc).__name__+': '+str(exc)[:180]}
        finally:
            release.set()
            observer.close()
            if observer._thread:observer._thread.join(timeout=5)
