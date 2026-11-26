"""Required independent memory observation; never await neural recall in a main job.

Only the independent memory model runs here. Reports are untrusted historical
advice for the existing Sentinel review, never a grant or a new review gate.
"""
from collections import OrderedDict
from threading import Condition, Thread
from time import monotonic
from urllib.error import HTTPError, URLError
from .triad_errors import WorkerFailure,http_failure
from .memory_governor import (retrieve, evidence_eligible, canonical, parse_selection,
                              specialist_prompt, MEMORY_SPECIALIST_TOKENS)
from .reasoning_council import sha

MAX_PENDING=16
MAX_REPORTS=24
TTL=300
RETRY_AFTER=90
DEFER_RETRY=15
SCAN_INTERVAL=15

def transient_recall(error):
    if isinstance(error,HTTPError):error=http_failure(error)
    if isinstance(error,WorkerFailure):return error.code in ('worker_busy','memory_pressure','worker_exit','transport_error')
    return isinstance(error,(URLError,TimeoutError,OSError))
ADVISORY_HEADER='\n\nFIFTH AI HISTORICAL FINDINGS (unverified relevance; Sentinel must independently assess against current requirements; no authority):\n'


def identity(project,chat_id,original,job_id):
    return (str(project),chat_id,sha(original),job_id)


class MemoryObserver:
    def __init__(self, *, path, select, available, report=lambda event,**kw:None, clock=monotonic):
        self.path=path
        self.select=select
        self.available=available
        self.report=report
        self.clock=clock
        self._cv=Condition()
        self._pending=OrderedDict()
        self._results=OrderedDict()
        self._attempted=OrderedDict()
        self._active=None
        self._retry_at={}
        self._closed=False
        self._thread=None
        self._duty=None
        self._scan_at=-float('inf')
        self._conversation_scan_turn=False
        self._self_investigation_turn=0

    def _emit(self,event,**kw):
        try:self.report(event,**kw)
        except Exception:pass

    def start_duty(self,duty):
        """Independent initiative; scan and recall on the same worker, never the GUI."""
        with self._cv:
            if self._closed:return
            self._duty=duty
            if self._thread is None:
                self._thread=Thread(target=self._work,name='triad-memory-observer',daemon=True)
                self._thread.start()
            self._cv.notify_all()

    def observe(self, *, project, chat_id, original, focus, phase, job_id=0,
                section='', cancelled=None, scope=''):
        """Foreground: bounded queue insertion only; no DB or model access."""
        if not project or str(project)=='(general)' or not chat_id or not original or not focus:
            return
        if cancelled and cancelled():return
        if type(job_id) is not int or job_id<0 or not isinstance(section,str) or (section and section not in original):return
        binding=identity(project,chat_id,original,job_id)
        focus=str(focus)[:500]
        key=(binding,sha(focus),phase,sha(section))
        if phase=='anticipatory_recall':key+= (sha(str(scope)),)
        packet=dict(project=str(project),chat_id=chat_id,original=original,focus=focus,
                    job_id=job_id,phase=phase,section=section,cancelled=cancelled,scope=str(scope)[:160])
        with self._cv:
            if self._closed:return
            last=self._attempted.get(key)
            if key==self._active or key in self._pending or (last is not None and self.clock()-last<RETRY_AFTER):
                return
            if len(self._pending)+int(self._active is not None)>=MAX_PENDING:
                # Retain admitted work and reserve a slot for an active retry.
                self._emit('memory_observer_backlog_full',pending=len(self._pending))
                return
            self._pending[key]=packet
            if self._thread is None:
                self._thread=Thread(target=self._work,name='triad-memory-observer',daemon=True)
                self._thread.start()
            self._cv.notify()

    def _stopped(self,packet):
        callback=packet.get('cancelled')
        return self._closed or bool(callback and callback())

    def _work(self):
        while True:
            with self._cv:
                while not self._closed and not self._pending and self._duty is None:self._cv.wait()
                if self._closed:return
                duty=self._duty
                due=duty is not None and self.clock()>=self._scan_at
                if due:self._scan_at=self.clock()+SCAN_INTERVAL
            try:ready=self.available()
            except Exception:ready=False
            if not ready:
                if due:self._scan_at=-float('inf')
                with self._cv:self._cv.wait(timeout=2)
                continue
            if due:
                try:
                    for packet in duty.scan():self.observe(**packet)
                except Exception as exc:self._emit('memory_duty_scan_failed',error_type=type(exc).__name__)
                # Same dedicated model, rotating independent attention. Never
                # add a conversation inference to the main workflow.
                self._conversation_scan_turn=not self._conversation_scan_turn
                self._self_investigation_turn=(self._self_investigation_turn+1)%4
                if self._self_investigation_turn==0:
                    try:
                        from .self_investigation import memory_once
                        from .triad_profiles import ROOT
                        from pathlib import Path
                        memory_once(ROOT,Path(self.path).parent,self.select,lambda:self._closed)
                    except Exception as exc:
                        self._emit('self_investigation_memory_deferred',error_type=type(exc).__name__)
                with self._cv:has_pending=bool(self._pending)
                if self._conversation_scan_turn or not has_pending:
                    try:
                        from .conversation_memory import run_once
                        result=run_once(self.path,self.select,lambda:self._closed)
                        if result and result['selected']:
                            self._emit('memory_conversation_findings',count=len(result['selected']))
                    except Exception as exc:
                        self._emit('memory_conversation_deferred' if transient_recall(exc) else 'memory_conversation_failed',
                                   error_type=type(exc).__name__)
            with self._cv:
                if self._closed:return
                if not self._pending:
                    self._cv.wait(timeout=2)
                    continue
                now=self.clock()
                key=next((k for k in self._pending if self._retry_at.get(k,0)<=now),None)
                if key is None:
                    self._cv.wait(timeout=2)
                    continue
                packet=self._pending.pop(key)
                self._retry_at.pop(key,None)
                self._active=key
            retry=False
            try:
                if self._stopped(packet):continue
                args={k:packet[k] for k in ('project','chat_id','original','focus','job_id')}
                rows=retrieve(self.path,**args)
                eligible=[r for r in rows if evidence_eligible(r)]
                if self._stopped(packet):continue
                if not eligible:
                    if duty is not None:duty.complete(packet,[])
                    continue
                prompt=specialist_prompt(packet['original'],packet['focus'],packet['phase'],packet['section'],eligible)
                if len(prompt)>7000:raise ValueError('Memory observation exceeds context budget')
                answer=self.select(sha(canonical(key))+sha(prompt),prompt,MEMORY_SPECIALIST_TOKENS)
                chosen=parse_selection(answer,{r['id'] for r in eligible})
                if self._stopped(packet):continue
                # Work can advance during a slow recall. A new unrelated row
                # is not a reason to drop an unchanged historical finding.
                fresh={r['id']:r for r in retrieve(self.path,**args) if evidence_eligible(r)}
                selected=[r for r in eligible if r['id'] in chosen and fresh.get(r['id'])==r]
                if duty is not None:duty.complete(packet,selected)
                if selected:
                    with self._cv:
                        if not self._closed:
                            self._results[key]=(self.clock(),packet,selected)
                            self._results.move_to_end(key)
                            while len(self._results)>MAX_REPORTS:self._results.popitem(last=False)
                    self._emit('memory_observer_findings',count=len(selected),binding_sha=sha(canonical(key[0])))
                else:self._emit('memory_observer_no_findings')
            except Exception as exc:
                retry=transient_recall(exc)
                self._emit('memory_observer_deferred' if retry else 'memory_observer_failed',error_type=type(exc).__name__)
            finally:
                with self._cv:
                    if retry and not self._closed:
                        self._pending[key]=packet
                        # Resource deferral must not keep other recall work behind
                        # one repeatedly deferred packet. Admitted duties also
                        # remain in the existing durable Memory ledger.
                        self._pending.move_to_end(key)
                        self._retry_at[key]=self.clock()+DEFER_RETRY
                    else:
                        self._attempted[key]=self.clock()
                        self._attempted.move_to_end(key)
                        while len(self._attempted)>MAX_REPORTS*4:self._attempted.popitem(last=False)
                    self._active=None
                    self._cv.notify_all()

    def advice(self, *, project,chat_id,original,focus,job_id=0,budget=600,cancelled=None,recipient='sentinel'):
        """Used by existing JANUS planning or Sentinel review; never starts inference.

        Late reports may be relevant to later operations in the same task.
        Require original scope and fresh authoritative candidate identity at
        the current focus; Sentinel independently weighs present relevance.
        """
        if recipient not in ('janus','sentinel'):raise ValueError('Unknown memory advice recipient')
        if budget<=len(ADVISORY_HEADER) or (cancelled and cancelled()):return ''
        binding=identity(project,chat_id,original,job_id)
        with self._cv:
            reports=[(k,v) for k,v in reversed(self._results.items())
                     if k[0]==binding and self.clock()-v[0]<=TTL]
        duty=self._duty
        if not reports and (duty is None or not duty.has_reports(job_id)):return ''
        # Revalidate against a bounded read-only snapshot of the existing
        # search index. New/changed dirty rows await the Memory worker's
        # next scan; never force foreground index maintenance.
        try:
            current={r['id']:r for r in retrieve(self.path,project=str(project),chat_id=chat_id,
                  original=original,focus=str(focus)[:500],job_id=job_id,read_only=True) if evidence_eligible(r)}
        except Exception:return ''
        out=ADVISORY_HEADER;seen=set()
        for _,(_,packet,rows) in reports:
            try:
                if self._stopped(packet):continue
            except Exception:continue
            for row in rows:
                ident=row['id']
                if ident in seen or current.get(ident)!=row:continue
                line=canonical(row)+'\n'
                if len(out)+len(line)<=budget:
                    out+=line;seen.add(ident)
        if duty is not None:
            try:
                for row in duty.advice_records(project=project,chat_id=chat_id,original=original,job_id=job_id,current=current):
                    ident=row['id'];line=canonical(row)+'\n'
                    if ident not in seen and len(out)+len(line)<=budget:
                        out+=line;seen.add(ident)
            except Exception:pass
        if not seen or (cancelled and cancelled()):return ''
        self._emit('memory_observer_delivered',count=len(seen),binding_sha=sha(canonical(binding)),recipient=recipient)
        return out

    def close(self):
        """Do not wait for an in-flight model; discard its result on return."""
        with self._cv:
            self._closed=True
            self._pending.clear()
            self._retry_at.clear()
            self._results.clear()
            self._cv.notify_all()
