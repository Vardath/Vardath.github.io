"""Non-blocking, one-shot review gate for an already authorized dispatch.

Called by the desktop scheduler only; worker performs memory/adherence review,
never executes commands. A changed operation cannot consume another result.
"""
from threading import Thread, Lock

class DispatchMemoryGate:
    def __init__(self):
        self._lock=Lock()
        self._entry=None

    def busy(self):
        with self._lock:
            return self._entry is not None and self._entry['state']=='pending'

    def check(self,key,review):
        with self._lock:
            entry=self._entry
            if entry is not None:
                if entry['state']=='pending':return False
                self._entry=None
                if entry['key']==key:
                    if entry['state']!='passed':
                        raise ValueError('Memory dispatch review blocked: '+entry['error'])
                    return True
            entry={'key':key,'state':'pending','error':''}
            self._entry=entry
        def worker():
            try:
                review()
                state,error='passed',''
            except Exception as exc:
                state,error='blocked',type(exc).__name__
            with self._lock:
                entry['state']=state;entry['error']=error
        try:Thread(target=worker,name='triad-memory-dispatch',daemon=True).start()
        except Exception:
            with self._lock:self._entry=None
            raise
        return False
