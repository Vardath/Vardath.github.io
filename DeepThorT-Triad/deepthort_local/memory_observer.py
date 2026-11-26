"""Opportunistic, bounded memory observation; never await a neural recall in a main job.

Only the independent memory model runs here. Reports are untrusted historical
advice for the existing Sentinel review, never a grant or a new review gate.
"""
from collections import OrderedDict
from threading import Condition, Thread
from time import monotonic
from .memory_governor import (retrieve, evidence_eligible, canonical, parse_selection,
                              specialist_prompt, MEMORY_SPECIALIST_TOKENS)
from .reasoning_council import sha

MAX_PENDING=16
MAX_REPORTS=24
TTL=300
RETRY_AFTER=90
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
        self._closed=False
        self._thread=None

    def _emit(self,event,**kw):
        try:self.report(event,**kw)
        except Exception:pass

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
        packet=dict(project=str(project),chat_id=chat_id,original=original,focus=focus,
                    job_id=job_id,phase=phase,section=section,cancelled=cancelled,scope=str(scope)[:160])
        with self._cv:
            if self._closed:return
            last=self._attempted.get(key)
            if key==self._active or key in self._pending or (last is not None and self.clock()-last<RETRY_AFTER):
                return
            self._pending[key]=packet
            while len(self._pending)>MAX_PENDING:self._pending.popitem(last=False)
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
                while not self._closed and not self._pending:self._cv.wait()
                if self._closed:return
            try:ready=self.available()
            except Exception:ready=False
            if not ready:
                with self._cv:self._cv.wait(timeout=2)
                continue
            with self._cv:
                if self._closed:return
                if not self._pending:continue
                key,packet=self._pending.popitem(last=False)
                self._active=key
            try:
                if self._stopped(packet):continue
                args={k:packet[k] for k in ('project','chat_id','original','focus','job_id')}
                rows=retrieve(self.path,**args)
                eligible=[r for r in rows if evidence_eligible(r)]
                if not eligible or self._stopped(packet):continue
                prompt=specialist_prompt(packet['original'],packet['focus'],packet['phase'],packet['section'],eligible)
                if len(prompt)>7000:raise ValueError('Memory observation exceeds context budget')
                answer=self.select(sha(canonical(key))+sha(prompt),prompt,MEMORY_SPECIALIST_TOKENS)
                chosen=parse_selection(answer,{r['id'] for r in eligible})
                if self._stopped(packet):continue
                # Work can advance during a slow recall. A new unrelated row
                # is not a reason to drop an unchanged historical finding.
                fresh={r['id']:r for r in retrieve(self.path,**args) if evidence_eligible(r)}
                selected=[r for r in eligible if r['id'] in chosen and fresh.get(r['id'])==r]
                if selected:
                    with self._cv:
                        if not self._closed:
                            self._results[key]=(self.clock(),packet,selected)
                            self._results.move_to_end(key)
                            while len(self._results)>MAX_REPORTS:self._results.popitem(last=False)
                    self._emit('memory_observer_findings',count=len(selected),binding_sha=sha(canonical(key[0])))
                else:self._emit('memory_observer_no_findings')
            except Exception as exc:
                self._emit('memory_observer_deferred',error_type=type(exc).__name__)
            finally:
                with self._cv:
                    self._attempted[key]=self.clock()
                    self._attempted.move_to_end(key)
                    while len(self._attempted)>MAX_REPORTS*4:self._attempted.popitem(last=False)
                    self._active=None

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
        if not reports:return ''
        # Deterministic retrieval only when a report exists; no neural wait.
        try:
            current={r['id']:r for r in retrieve(self.path,project=str(project),chat_id=chat_id,
                  original=original,focus=str(focus)[:500],job_id=job_id) if evidence_eligible(r)}
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
        if not seen or (cancelled and cancelled()):return ''
        self._emit('memory_observer_delivered',count=len(seen),binding_sha=sha(canonical(binding)),recipient=recipient)
        return out

    def close(self):
        """Do not wait for an in-flight model; discard its result on return."""
        with self._cv:
            self._closed=True
            self._pending.clear()
            self._results.clear()
            self._cv.notify_all()
