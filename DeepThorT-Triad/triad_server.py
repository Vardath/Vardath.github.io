"""Three resident native OpenVINO CPU processes, all-or-nothing readiness, no swapping."""
import json
import os
import secrets
import socket
import threading
import time
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.request import Request,build_opener,ProxyHandler
from urllib.error import HTTPError
from deepthort_local.triad_errors import WorkerFailure,http_failure,synthetic
from deepthort_local.role_inbox import RoleInbox,serial_rank
from deepthort_local.adaptive_admission import capacity,admission_ready
from deepthort_local.agent_doctrine import VERSION as DOCTRINE_VERSION
from deepthort_local.inference_metrics import measured
from deepthort_local.triad_profiles import ROOT,PROFILES,ALL_PROFILES,MEMORY_PROFILE,memory_installed,MODEL_ID,model_path,runtime_path,ready,total_weights,installed_files
from deepthort_local.triad_job import verify_root_cap,child_server,model_group,worker_budget,CONTROL_RESERVE_BYTES

def validate(body,default):
    if not isinstance(body,dict) or body.get('model',MODEL_ID)!=MODEL_ID or body.get('stream',False):
        raise ValueError('Invalid model request')
    role=body.get('triad_role',default)
    if role not in ALL_PROFILES:raise ValueError('Unknown role')
    messages=body.get('messages')
    if not isinstance(messages,list) or not 1<=len(messages)<=12:raise ValueError('Invalid messages')
    if any(not isinstance(m,dict) or m.get('role') not in ('system','user','assistant') or
           not isinstance(m.get('content'),str) or len(m['content'])>8000 for m in messages):
        raise ValueError('Invalid message')
    if sum(len(m['content']) for m in messages)>15000 or messages[-1]['role']!='user':
        raise ValueError('Context exceeds bounded profile')
    tokens=body.get('max_tokens',96)
    if type(tokens) is not int or not 1<=tokens<=768:raise ValueError('Invalid token limit')
    return role,[{'role':m['role'],'content':m['content']} for m in messages],tokens

def command(role,port,key):
    if role not in ALL_PROFILES:raise ValueError('Unknown role')
    return [str(runtime_path()),'-I',str(ROOT/'triad_openvino_worker.py'),role,str(port),key]

def admission(cap,available,total,weights):
    # Minimum allowance for all weights plus modest runtime overhead.
    # OS cap remains authoritative; runtime/KV allocation may still fail.
    need=weights+1536*1024**2+CONTROL_RESERVE_BYTES
    if cap<need or available<need+total//10:
        raise RuntimeError(f'Three resident models need at least {need/2**30:.2f} GiB headroom; job cap {cap/2**30:.2f} GiB. No model swapping or fallback.')
def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0));return s.getsockname()[1]
def request(port,path,key,body=None,timeout=2):
    req=Request(f'http://127.0.0.1:{port}'+path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    try:
        with build_opener(ProxyHandler({})).open(req,timeout=timeout) as r:
            return json.loads(r.read(2_000_000))
    except HTTPError as error:
        raise http_failure(error,include_detail=bool(body and synthetic(body.get('model'),body.get('messages')))) from None

class Pool:
    def __init__(self,*,resource_sample=None):
        self.resource_sample=resource_sample
        self.resource_slots=0 if resource_sample is not None else 4
        self.resource_sample_at=-float('inf')
        self.children={};self.memory_child=None;self.memory_stage='not installed';self.locks={r:RoleInbox(r) for r in ALL_PROFILES}
        self.admission_lock=threading.Condition()
        self.generating=set()
        self.serial_waiters=[]
        self.serial_sequence=0
        # Start protected. Enable parallel requests only after the compact
        # workers are all resident in the verified shared memory group.
        # A classified allocation failure restores serial mode for this session.
        self.serial_memory_mode=True
        self.worker_commit_limit=0
        self.memory_retries=0
        self.stage='Checking combined memory';self.started=time.monotonic();self.ready_at=None;self.ready=False
    def set_stage(self,message):
        self.stage=message;print(message,flush=True)
    def start(self,stack):
        cap,available,total=verify_root_cap()
        weights=total_weights()
        self.set_stage(f'Triad memory: job cap {cap/2**30:.2f} GiB; free RAM {available/2**30:.2f} GiB; weights {weights/2**30:.2f} GiB')
        admission(cap,available,total,weights)
        group,self.worker_commit_limit=stack.enter_context(model_group())
        logs=ROOT/'state'/'logs'
        self.set_stage('Checking installed native OpenVINO CPU runtime')
        with child_server([str(runtime_path()),'-I',str(ROOT/'triad_openvino_worker.py'),'--probe'],ROOT,logs/'triad-runtime-version.log',group=group) as (_,alive):
            deadline=time.monotonic()+120
            while alive() and time.monotonic()<deadline:time.sleep(.25)
            if alive():raise RuntimeError('OpenVINO CPU probe timed out')
            if alive.code()!=0:raise RuntimeError('OpenVINO probe failed: '+alive.failure())
        # Sequential initialization, simultaneous resident model processes.
        for role,p in PROFILES.items():
            self.set_stage('Loading '+role+': '+p[0])
            port=free_port();key=secrets.token_hex(32)
            pid,alive=stack.enter_context(child_server(command(role,port,key),ROOT,logs/f'triad-{role}-native.log',group=group))
            self.children[role]=(port,key,pid,alive)
            deadline=time.monotonic()+900
            while time.monotonic()<deadline:
                for name,c in self.children.items():
                    if not c[3]():raise RuntimeError(f'Resident model {name} exited: '+c[3].failure())
                try:
                    value=request(port,'/health',key)
                    actual_pid=value.get('pid')
                    if (value.get('status')=='ok' and value.get('role')==role
                            and value.get('backend')=='native-openvino-ir-cpu' and alive.member(actual_pid)):
                        self.children[role]=(port,key,actual_pid,alive)
                        break
                except (OSError,ValueError):pass
                time.sleep(1)
            else:raise RuntimeError('Startup timed out: '+role+'; inspect state/logs/triad-'+role+'-native.log')
        # The fifth intelligent model is independent of the three required
        # baseline workers. Never discard working language models if it fails.
        if memory_installed():
            self.memory_stage='checking resource admission'
            try:
                self.start_memory(stack,group,logs)
            except (OSError,RuntimeError,ValueError,KeyError,TypeError) as exc:
                self.memory_stage='blocked: '+type(exc).__name__
                print('Memory specialist deferred: '+str(exc)[:500],flush=True)
        self.activate_resident_pool()

    def start_memory(self,stack,group,logs):
        # Keep the same inherited hard cap and original worker group. A
        # separate child cleanup/commit cap prevents a runaway memory worker.
        from deepthort_local.triad_job import memory_specialist_admission
        memory_specialist_admission()
        self.memory_stage='loading memory specialist'
        self.set_stage('Loading independent memory specialist: '+MEMORY_PROFILE[0])
        port=free_port();key=secrets.token_hex(32)
        with ExitStack() as trial:
            pid,alive=trial.enter_context(child_server(command('memory',port,key),ROOT,
                logs/'triad-memory-native.log',group=group,memory_specialist=True))
            deadline=time.monotonic()+180
            while time.monotonic()<deadline:
                if not alive():raise RuntimeError('Memory worker exited: '+alive.failure())
                if not all(c[3]() for c in self.children.values()):
                    raise RuntimeError('Baseline worker stopped during memory admission')
                try:
                    value=request(port,'/health',key)
                    actual_pid=value.get('pid')
                    if (value.get('status')=='ok' and value.get('role')=='memory'
                            and value.get('backend')=='native-openvino-ir-cpu' and alive.member(actual_pid)):
                        self.memory_child=(port,key,actual_pid,alive)
                        stack.enter_context(trial.pop_all())
                        self.memory_stage='resident'
                        return
                except (OSError,ValueError):pass
                time.sleep(1)
            raise RuntimeError('Memory specialist startup timed out')

    def memory_ready(self):
        return self.memory_child is not None and self.memory_child[3]()

    def activate_resident_pool(self):
        if (self.worker_commit_limit<=0 or set(self.children)!=set(PROFILES)
                or not all(c[3]() for c in self.children.values())):
            raise RuntimeError('Parallel admission requires three live protected workers')
        with self.admission_lock:
            self.serial_memory_mode=False
            self.ready_at=time.monotonic()
            self.ready=True
            self.set_stage('All three compact models resident; parallel generation enabled, not yet validated')
    def healthy(self):
        return self.ready and len(self.children)==3 and all(c[3]() for c in self.children.values())
    def _slots_locked(self):
        # All accesses to admission state occur under the same condition.
        now=time.monotonic()
        if self.resource_sample is not None and now-self.resource_sample_at>=2:
            try:self.resource_slots=capacity(self.resource_sample())
            except Exception:self.resource_slots=0
            self.resource_sample_at=now
        return min(1,self.resource_slots) if self.serial_memory_mode else self.resource_slots

    def _generate(self,role,messages,tokens):
        # All four text roles are required workers. Recall runs independently,
        # with a lower initial rank but the same bounded aging as other calls.
        # Admission waits occur in the caller's own thread, never the GUI.
        with measured(ROOT/'state',role,'admission',budget_tokens=tokens), self.admission_lock:
            if not self.healthy():raise WorkerFailure('worker_exit')
            self.serial_sequence+=1
            ticket=(time.monotonic(),self.serial_sequence,role)
            self.serial_waiters.append(ticket)
            deadline=ticket[0]+600
            try:
                while not admission_ready(self.generating,self.serial_waiters,ticket,self._slots_locked(),serial_rank,time.monotonic()):
                    if not self.healthy() or (role=='memory' and not self.memory_ready()):raise WorkerFailure('worker_exit')
                    if time.monotonic()>=deadline:raise WorkerFailure('worker_busy','Measured resource admission wait expired; reschedule')
                    self.admission_lock.wait(.5)
                if not self.healthy() or (role=='memory' and not self.memory_ready()):raise WorkerFailure('worker_exit')
                self.generating.add(role)
            finally:
                self.serial_waiters.remove(ticket)
                self.admission_lock.notify_all()
        try:
            child=self.memory_child if role=='memory' else self.children[role]
            if child is None or not child[3]():raise WorkerFailure('worker_exit')
            port,key,pid,alive=child
            result=request(port,'/v1/chat/completions',key,
                {'model':role,'messages':messages,'max_tokens':tokens,'temperature':0,'stream':False},timeout=3600)
            if result.get('model')!=role:raise ValueError('Worker role mismatch')
            answer=result['choices'][0]['message']['content']
            if not isinstance(answer,str) or not answer.strip():raise ValueError('Model returned no final text')
            if not self.healthy():raise WorkerFailure('worker_exit')
            return answer
        except WorkerFailure as error:
            if error.code=='memory_pressure':
                with self.admission_lock:
                    if not self.serial_memory_mode:
                        self.serial_memory_mode=True
                        self.set_stage('Native memory pressure; protected serial generation for this session')
            raise
        finally:
            with self.admission_lock:
                self.generating.discard(role)
                self.admission_lock.notify_all()
    def infer(self,role,messages,tokens):
        with measured(ROOT/'state',role,'broker',budget_tokens=tokens):
            return self._infer(role,messages,tokens)
    def _infer(self,role,messages,tokens):
        if not self.healthy() or (role=='memory' and not self.memory_ready()):raise WorkerFailure('worker_exit')
        with self.locks[role]:
            try:return self._generate(role,messages,tokens)
            except WorkerFailure as error:
                if role=='memory' or error.code!='memory_pressure' or not self.healthy():raise
                with self.admission_lock:
                    self.memory_retries+=1
                print('Native memory pressure:',role,'; retrying once with exclusive generation, all weights resident',flush=True)
                return self._generate(role,messages,tokens)
    def status(self,council):
        with self.admission_lock:
            active=set(self.generating);serial=self.serial_memory_mode;retries=self.memory_retries
            slots=self._slots_locked();waiting=len(self.serial_waiters)
        return {'model':MODEL_ID,'backend':'native-openvino-ir-cpu','offline':True,'ready':self.healthy(),
            'role':'council' if council else 'implementation','pid':os.getpid(),
            'phase':'ready' if self.healthy() else 'loading','stage':self.stage,
            'inference_busy':any(self.locks[r].locked() for r in (('janus','sentinel') if council else ('implementation',))),
            'loading_seconds':int((self.ready_at if self.ready_at is not None else time.monotonic())-self.started),'stalled':False,'error':None,
            'serial_memory_mode':serial,'memory_retries':retries,
            'admission_slots':slots,'admission_waiting':waiting,
            'doctrine_version':DOCTRINE_VERSION,'role_queue_depths':{r:box.waiting() for r,box in self.locks.items()},
            'worker_commit_limit_bytes':self.worker_commit_limit,'control_reserve_bytes':CONTROL_RESERVE_BYTES,
            'memory_model':{'name':MEMORY_PROFILE[0],'revision':MEMORY_PROFILE[2],
                'resident':self.memory_ready(),'pid':self.memory_child[2] if self.memory_ready() else None,
                'busy':self.locks['memory'].locked(),'generating':'memory' in active,'stage':self.memory_stage},
            'models':{r:{'name':PROFILES[r][0],'pid':c[2],'resident':c[3](),'busy':self.locks[r].locked(),'generating':r in active} for r,c in self.children.items()}}

def handler(pool,token,council):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def setup(self):
            self.request.settimeout(30)
            super().setup()
        def reply(self,status,value):
            b=json.dumps(value).encode()
            try:
                self.send_response(status);self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
            except (ConnectionError,TimeoutError):
                # Client abandoned this loopback connection. A failed response
                # write is not an inference failure; never send a second reply.
                self.close_connection=True
        def authorized(self):
            return secrets.compare_digest(self.headers.get('Authorization',''),'Bearer '+token)
        def do_GET(self):
            if not self.authorized():return self.reply(403,{'error':'Unauthorized'})
            if self.path!='/health':return self.reply(404,{'error':'Not found'})
            self.reply(200,pool.status(council))
        def do_POST(self):
            if not self.authorized():return self.reply(403,{'error':'Unauthorized'})
            if self.path!='/v1/chat/completions':return self.reply(404,{'error':'Not found'})
            if not pool.healthy():return self.reply(503,{'error':'All three models not ready'})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 1<=size<=80000:raise ValueError('Invalid request length')
                role,messages,tokens=validate(json.loads(self.rfile.read(size)),'janus' if council else 'implementation')
                answer=pool.infer(role,messages,tokens)
                self.reply(200,{'model':MODEL_ID,'triad_role':role,'choices':[{'message':{'role':'assistant','content':answer},'finish_reason':'stop'}]})
            except WorkerFailure as e:
                self.reply(500,{'error':e.code,'code':e.code,'detail':e.detail})
            except Exception as e:
                self.reply(500,{'error':'native_error','code':'native_error','detail':type(e).__name__})
    return Handler

def main():
    verify_root_cap()
    if not ready():raise SystemExit('Triad weights or runtime missing; install first')
    token=os.environ.get('DEEPTHORT_TRIAD_TOKEN')
    if not token or len(token)<32:raise SystemExit('Use capped desktop launcher')
    pool=Pool(resource_sample=verify_root_cap)
    # Both compatibility ports must be ours before launching any model.
    with ExitStack() as stack:
        servers=[stack.enter_context(ThreadingHTTPServer(('127.0.0.1',p),handler(pool,token,p==8766))) for p in (8765,8766)]
        for server in servers:
            threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            pool.start(stack)
            while pool.healthy():time.sleep(1)
            for name,c in pool.children.items():
                if not c[3]():raise RuntimeError(f'Resident model {name} exited: '+c[3].failure())
            raise RuntimeError('Resident model exited; shutting down all three, no fallback')
        finally:
            # Stop serving before closing Windows sockets, avoiding misleading
            # serve_forever exceptions during a failed startup.
            pool.ready=False
            for server in servers:server.shutdown()
if __name__=='__main__':main()
