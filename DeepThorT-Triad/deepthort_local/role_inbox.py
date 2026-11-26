"""Bounded per-role inference inboxes and priority ordering for protected serial mode.

Role inboxes schedule actual in-flight inference calls, not project authority.
Durable projects remain in the existing JobStore and TaskGraphStore.
"""
from collections import deque
from threading import Condition
from time import monotonic
from .triad_errors import WorkerFailure

MAX_WAITING=4
WAIT_SECONDS=600
SERIAL_PRIORITY={'sentinel':0,'janus':1,'implementation':2,'memory':3}
AGING_SECONDS=30

def serial_rank(ticket,now):
    stamp,sequence,role=ticket
    priority=SERIAL_PRIORITY[role]
    # Older work eventually ties highest priority, then FIFO wins.
    return (max(0,priority-int(max(0,now-stamp)//AGING_SECONDS)),sequence)

class RoleInbox:
    def __init__(self,role,*,max_waiting=MAX_WAITING,wait_seconds=WAIT_SECONDS,clock=monotonic):
        if role not in {*SERIAL_PRIORITY,'memory'}:raise ValueError('Unknown role inbox')
        self.role=role
        self.max_waiting=max_waiting
        self.wait_seconds=wait_seconds
        self.clock=clock
        self.cv=Condition()
        self.queue=deque()
        self.active=False

    def locked(self):
        with self.cv:return self.active

    def waiting(self):
        with self.cv:return len(self.queue)

    def __enter__(self):
        with self.cv:
            # The dedicated observer owns its backlog; only one recall may enter the broker.
            if self.role=='memory' and (self.active or self.queue):
                raise WorkerFailure('worker_busy','Memory observer already has an active recall')
            if not self.active and not self.queue:
                self.active=True
                return self
            if len(self.queue)>=self.max_waiting:
                raise WorkerFailure('worker_busy','Role inference inbox full; reschedule the task')
            ticket=object()
            self.queue.append(ticket)
            deadline=self.clock()+self.wait_seconds
            try:
                while self.active or self.queue[0] is not ticket:
                    remaining=deadline-self.clock()
                    if remaining<=0:
                        raise WorkerFailure('worker_busy','Role inbox wait expired; reschedule the task')
                    self.cv.wait(min(remaining,.5))
                self.queue.popleft()
                self.active=True
                return self
            except BaseException:
                if ticket in self.queue:self.queue.remove(ticket)
                self.cv.notify_all()
                raise

    def __exit__(self,*_):
        with self.cv:
            self.active=False
            self.cv.notify_all()
