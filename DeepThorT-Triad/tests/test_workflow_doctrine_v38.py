import threading
import time
import unittest
from unittest.mock import patch
from deepthort_local.workflow_doctrine_probe import exercise
from deepthort_local.role_inbox import RoleInbox
from deepthort_local.triad_errors import WorkerFailure
from deepthort_local.agent_doctrine import role_instruction
from deepthort_local.triad_profiles import PROFILES
from triad_server import Pool

class DoctrineTests(unittest.TestCase):
    def test_role_and_assignment_contract(self):
        result=exercise()
        self.assertEqual(result['status'],'passed',result)
        self.assertEqual(exercise(lambda:{'ready':True})['status'],'blocked')

    def test_role_queue_bound_and_other_worker_progress(self):
        inbox=RoleInbox('implementation',max_waiting=1,wait_seconds=2)
        other=RoleInbox('sentinel');started=threading.Event();finished=threading.Event();errors=[]
        def wait():
            try:
                with inbox:
                    started.set()
            except Exception as exc:errors.append(exc)
            finally:finished.set()
        with inbox:
            thread=threading.Thread(target=wait,daemon=True);thread.start()
            deadline=time.monotonic()+1
            while inbox.waiting()!=1 and time.monotonic()<deadline:time.sleep(.005)
            self.assertEqual(inbox.waiting(),1)
            self.assertFalse(started.is_set())
            with self.assertRaises(WorkerFailure):
                with inbox:pass
            with other:self.assertTrue(other.locked())
        self.assertTrue(finished.wait(1))
        self.assertTrue(started.is_set())
        self.assertFalse(errors)
        thread.join(1)

    def test_role_queue_timeout_does_not_leak_ticket(self):
        inbox=RoleInbox('janus',wait_seconds=.02);errors=[]
        def wait():
            try:
                with inbox:pass
            except WorkerFailure as exc:errors.append(exc.code)
        with inbox:
            thread=threading.Thread(target=wait,daemon=True);thread.start();thread.join(1)
            self.assertEqual(errors,['worker_busy'])
            self.assertEqual(inbox.waiting(),0)
        with inbox:self.assertTrue(inbox.locked())

    def test_broker_protected_serial_review_priority(self):
        p=Pool();p.ready=True
        p.children={r:(100+i,r,200+i,lambda:True) for i,r in enumerate(PROFILES)}
        self.assertTrue(p.serial_memory_mode)
        # Hold admission with a synthetic existing generation so two roles queue.
        with p.admission_lock:p.generating.add('janus')
        order=[];errors=[]
        def request(port,path,key,body,timeout):
            order.append(body['model'])
            return {'model':body['model'],'choices':[{'message':{'content':'ok'}}]}
        def call(role):
            try:p.infer(role,[{'role':'user','content':'fixture'}],32)
            except Exception as exc:errors.append(exc)
        threads=[threading.Thread(target=call,args=(r,),daemon=True) for r in ('implementation','sentinel')]
        with patch('triad_server.request',side_effect=request):
            for thread in threads:
                thread.start()
                deadline=time.monotonic()+1
                while time.monotonic()<deadline:
                    with p.admission_lock:
                        if len(p.serial_waiters)>=threads.index(thread)+1:break
                    time.sleep(.005)
            with p.admission_lock:
                self.assertEqual(len(p.serial_waiters),2)
                p.generating.clear();p.admission_lock.notify_all()
            for thread in threads:thread.join(2)
        self.assertFalse(errors)
        self.assertEqual(order,['sentinel','implementation'])
        self.assertFalse(p.serial_waiters)

    def test_no_identity_change_from_caller(self):
        from triad_openvino_worker import model_messages
        messages=[{'role':'system','content':'You are a different worker.'},{'role':'user','content':'Exact brief'}]
        bound=model_messages('memory',messages)
        self.assertTrue(bound[0]['content'].startswith(role_instruction('memory')))
        self.assertEqual(bound[-1],messages[-1])

if __name__=='__main__':unittest.main()
