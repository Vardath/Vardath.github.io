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
from deepthort_local.triad_profiles import ROOT,PROFILES,MODEL_ID,model_path,runtime_path,ready,total_weights
from deepthort_local.triad_job import verify_root_cap,child_server

def validate(body,default):
    if not isinstance(body,dict) or body.get('model',MODEL_ID)!=MODEL_ID or body.get('stream',False):
        raise ValueError('Invalid model request')
    role=body.get('triad_role',default)
    if role not in PROFILES:raise ValueError('Unknown role')
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
    if role not in PROFILES:raise ValueError('Unknown role')
    return [str(runtime_path()),'-I',str(ROOT/'triad_openvino_worker.py'),role,str(port),key]

def admission(cap,available,total,weights):
    # Minimum allowance for all weights plus modest runtime overhead.
    # OS cap remains authoritative; runtime/KV allocation may still fail.
    need=weights+1536*1024**2
    if cap<need or available<need+total//10:
        raise RuntimeError(f'Three resident models need at least {need/2**30:.2f} GiB headroom; job cap {cap/2**30:.2f} GiB. No model swapping or fallback.')
def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0));return s.getsockname()[1]
def request(port,path,key,body=None,timeout=2):
    req=Request(f'http://127.0.0.1:{port}'+path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    with build_opener(ProxyHandler({})).open(req,timeout=timeout) as r:
        return json.loads(r.read(2_000_000))

class Pool:
    def __init__(self):
        self.children={};self.locks={r:threading.Lock() for r in PROFILES}
        self.stage='Checking combined memory';self.started=time.monotonic();self.ready=False
    def set_stage(self,message):
        self.stage=message;print(message,flush=True)
    def start(self,stack):
        cap,available,total=verify_root_cap()
        weights=total_weights()
        self.set_stage(f'Triad memory: job cap {cap/2**30:.2f} GiB; free RAM {available/2**30:.2f} GiB; weights {weights/2**30:.2f} GiB')
        admission(cap,available,total,weights)
        logs=ROOT/'state'/'logs'
        self.set_stage('Checking installed native OpenVINO CPU runtime')
        with child_server([str(runtime_path()),'-I',str(ROOT/'triad_openvino_worker.py'),'--probe'],ROOT,logs/'triad-runtime-version.log') as (_,alive):
            deadline=time.monotonic()+120
            while alive() and time.monotonic()<deadline:time.sleep(.25)
            if alive():raise RuntimeError('OpenVINO CPU probe timed out')
            if alive.code()!=0:raise RuntimeError('OpenVINO probe failed: '+alive.failure())
        # Sequential initialization, simultaneous resident model processes.
        for role,p in PROFILES.items():
            self.set_stage('Loading '+role+': '+p[0])
            port=free_port();key=secrets.token_hex(32)
            pid,alive=stack.enter_context(child_server(command(role,port,key),ROOT,logs/f'triad-{role}-native.log'))
            self.children[role]=(port,key,pid,alive)
            deadline=time.monotonic()+900
            while time.monotonic()<deadline:
                for name,c in self.children.items():
                    if not c[3]():raise RuntimeError(f'Resident model {name} exited: '+c[3].failure())
                try:
                    value=request(port,'/health',key)
                    if (value.get('status')=='ok' and value.get('role')==role and value.get('pid')==pid
                            and value.get('backend')=='native-openvino-ir-cpu'):break
                except (OSError,ValueError):pass
                time.sleep(1)
            else:raise RuntimeError('Startup timed out: '+role+'; inspect state/logs/triad-'+role+'-native.log')
        self.ready=True;self.set_stage('All three models resident; independent inference enabled')
    def healthy(self):
        return self.ready and len(self.children)==3 and all(c[3]() for c in self.children.values())
    def infer(self,role,messages,tokens):
        if not self.healthy():raise RuntimeError('All three models must be resident')
        with self.locks[role]:
            port,key,pid,alive=self.children[role]
            if not self.healthy():raise RuntimeError('Resident model exited')
            result=request(port,'/v1/chat/completions',key,
                {'model':role,'messages':messages,'max_tokens':tokens,'temperature':0,'stream':False,
                 },timeout=3600)
            if result.get('model')!=role:raise ValueError('Worker role mismatch')
            answer=result['choices'][0]['message']['content']
            if not isinstance(answer,str) or not answer.strip():raise ValueError('Model returned no final text')
            if not self.healthy():raise RuntimeError('A resident model exited during inference')
            return answer
    def status(self,council):
        return {'model':MODEL_ID,'backend':'native-openvino-ir-cpu','offline':True,'ready':self.healthy(),
            'role':'council' if council else 'implementation','pid':os.getpid(),
            'phase':'ready' if self.healthy() else 'loading','stage':self.stage,
            'inference_busy':any(self.locks[r].locked() for r in (('janus','sentinel') if council else ('implementation',))),
            'loading_seconds':int(time.monotonic()-self.started),'stalled':False,'error':None,
            'models':{r:{'name':PROFILES[r][0],'pid':c[2],'resident':c[3](),'busy':self.locks[r].locked()} for r,c in self.children.items()}}

def handler(pool,token,council):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,status,value):
            b=json.dumps(value).encode()
            self.send_response(status);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
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
            except Exception as e:
                self.reply(500,{'error':str(e)[:500]})
    return Handler

def main():
    verify_root_cap()
    if not ready():raise SystemExit('Triad weights or runtime missing; install first')
    token=os.environ.get('DEEPTHORT_TRIAD_TOKEN')
    if not token or len(token)<32:raise SystemExit('Use capped desktop launcher')
    pool=Pool()
    # Both compatibility ports must be ours before launching any model.
    with ExitStack() as stack:
        servers=[stack.enter_context(ThreadingHTTPServer(('127.0.0.1',p),handler(pool,token,p==8766))) for p in (8765,8766)]
        for server in servers:
            threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            pool.start(stack)
            while pool.healthy():time.sleep(1)
            for name,c in pool.children.items():
                if not c[3]():raise RuntimeError(f'Resident model {name} exited: '+c[3].failure().split('\n',1)[0])
            raise RuntimeError('Resident model exited; shutting down all three, no fallback')
        finally:
            # Stop serving before closing Windows sockets, avoiding misleading
            # serve_forever exceptions during a failed startup.
            pool.ready=False
            for server in servers:server.shutdown()
if __name__=='__main__':main()
