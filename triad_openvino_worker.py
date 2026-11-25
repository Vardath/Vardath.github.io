"""Dedicated resident CPU OpenVINO worker. No model download or remote inference."""
import sys
from pathlib import Path
# -I excludes CWD and script directory. Add only this trusted application root.
sys.path.insert(0,str(Path(__file__).resolve().parent))
import os
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler,HTTPServer
from importlib.metadata import version
from deepthort_local.triad_profiles import PROFILES,RUNTIME_VERSION,model_path,installed_files
from deepthort_local.triad_job import verify_root_cap
from deepthort_local.triad_errors import native_error,synthetic

def probe():
    import openvino as ov
    import openvino_genai as genai
    import numpy as np
    if version('openvino-genai')!=RUNTIME_VERSION:raise RuntimeError('Incorrect installed OpenVINO GenAI version')
    core=ov.Core()
    if 'CPU' not in core.available_devices:raise RuntimeError('OpenVINO CPU device missing')
    x=ov.opset13.parameter([1],ov.Type.f32)
    graph=ov.Model([ov.opset13.add(x,x)],[x])
    compiled=core.compile_model(graph,'CPU',{'INFERENCE_NUM_THREADS':1,'NUM_STREAMS':1})
    out=next(iter(compiled([np.array([2],dtype=np.float32)]).values()))
    if float(out[0])!=4:raise RuntimeError('CPU runtime numerical probe failed')
    if not hasattr(genai,'ChatHistory'):raise RuntimeError('OpenVINO GenAI ChatHistory API missing')
    print('OpenVINO GenAI',version('openvino-genai'),'CPU numerical preflight passed',flush=True)

def bounded_scheduler(genai):
    # Explicit cache block ceiling rather than the latency-oriented default
    # scheduler with unlimited prefill batch and persistent prefix cache.
    cfg=genai.SchedulerConfig()
    cfg.max_num_seqs=1
    cfg.max_num_batched_tokens=128
    cfg.num_kv_blocks=256
    cfg.cache_size=0
    cfg.enable_prefix_caching=False
    return cfg

def final_text(role,answer):
    if not isinstance(answer,str):raise ValueError('Native model did not return text')
    answer=answer.strip()
    # Reasoning-capable checkpoints may return their private scratch work
    # before a real final answer. Preserve genuine final text; never invent
    # a result or treat an unfinished reasoning block as a successful reply.
    if role in ('janus','sentinel'):
        if '</think>' in answer and (role=='janus' or answer.startswith('<think>') or answer.startswith('</think>')):
            answer=answer.split('</think>',1)[1].strip()
        elif answer.startswith('<think>'):
            raise ValueError('Model exhausted its reasoning budget before a final answer')
    if not answer:raise ValueError('Empty model response')
    return answer

class Engine:
    def __init__(self,role):
        import openvino_genai as genai
        installed_files(role)
        if version('openvino-genai')!=RUNTIME_VERSION:raise RuntimeError('OpenVINO runtime version mismatch')
        self.genai=genai
        self.role=role
        self.lock=threading.Lock()
        # Native IR directory only. No GGUF, remote code, or runtime fallback.
        properties={'INFERENCE_NUM_THREADS':1,'NUM_STREAMS':1,'ENABLE_MMAP':False}
        # All three replacement checkpoints use conventional attention.
        # Retain the shared worker-memory cap and explicit cache bounds.
        properties['scheduler_config']=bounded_scheduler(genai)
        properties['KV_CACHE_PRECISION']='u8'
        self.pipe=genai.LLMPipeline(str(model_path(role)),'CPU',**properties)
        print('Native profile:',role,'one CPU thread; bounded scheduler',flush=True)
        self.tokenizer=self.pipe.get_tokenizer()
        print('Resident native OpenVINO CPU model ready:',role,flush=True)

    def generate(self,messages,tokens):
        history=self.genai.ChatHistory()
        for message in messages:history.append(message)
        # Qwen3 must return directly for strict verification/JSON tasks.
        if self.role=='sentinel':
            history.set_extra_context({'enable_thinking':False})
        # JANUS is a reasoning checkpoint. Its thought + final output both
        # count against the existing 768-output / 4096-total hard limits.
        if self.role=='janus':
            tokens=min(768,tokens+256)
        # Bound by actual token count including the model's own chat template.
        # Separate per-request histories prevent role/session KV contamination.
        rendered=self.tokenizer.apply_chat_template(history,add_generation_prompt=True)
        encoded=self.tokenizer.encode(rendered,add_special_tokens=False)
        count=int(encoded.input_ids.shape[-1])
        if count+tokens>4096:raise ValueError(f'Input {count} + output {tokens} exceeds 4096-token Triad profile; use indexed planning')
        config=self.genai.GenerationConfig()
        config.max_new_tokens=tokens
        config.do_sample=False
        config.num_beams=1
        # Tokenized preflight is for length only; generate uses native history.
        out=self.pipe.generate(history,config)
        return final_text(self.role,out.texts[0])

def serve(role,port,key):
    engine=Engine(role)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def setup(self):
            self.request.settimeout(30)
            super().setup()
        def reply(self,status,body):
            data=json.dumps(body).encode()
            self.send_response(status);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        def authorized(self):
            return secrets.compare_digest(self.headers.get('Authorization',''),'Bearer '+key)
        def do_GET(self):
            if not self.authorized():return self.reply(403,{'error':'Unauthorized'})
            if self.path!='/health':return self.reply(404,{'error':'Not found'})
            self.reply(200,{'status':'ok','role':role,'pid':os.getpid(),'backend':'native-openvino-ir-cpu'})
        def do_POST(self):
            if not self.authorized():return self.reply(403,{'error':'Unauthorized'})
            if self.path!='/v1/chat/completions':return self.reply(404,{'error':'Not found'})
            messages=None
            try:
                n=int(self.headers.get('Content-Length','0'))
                if not 1<=n<=80000:raise ValueError('Invalid request length')
                body=json.loads(self.rfile.read(n))
                from triad_server import validate
                selected,messages,tokens=validate({'model':'deepthort-triad','triad_role':body['model'],
                    'messages':body['messages'],'max_tokens':body['max_tokens'],'stream':body.get('stream',False)},role)
                if selected!=role:raise ValueError('Wrong worker role')
                with engine.lock:answer=engine.generate(messages,tokens)
                self.reply(200,{'model':role,'choices':[{'message':{'role':'assistant','content':answer}}]})
            except Exception as e:
                code=native_error(e)
                detail=str(e)[:500] if synthetic(role,messages) else type(e).__name__
                print('Native inference failure:',role,code,detail,flush=True)
                self.reply(500,{'error':code,'code':code,'detail':detail})
    # Each model has one dedicated process; execute generation on the main
    # interpreter thread, as in the passing installer smoke test. The broker
    # owns asynchronous health/status and serial request admission.
    with HTTPServer(('127.0.0.1',port),Handler) as server:server.serve_forever()

def main():
    verify_root_cap()
    import faulthandler
    faulthandler.enable()
    args=sys.argv[1:]
    if args==['--probe']:probe();return
    if len(args)==2 and args[0]=='--smoke' and args[1] in PROFILES:
        engine=Engine(args[1])
        result=engine.generate([{'role':'user','content':'What is 2 + 2? Answer only with the number.'}],16)
        print('Synthetic reply:',result[:100],flush=True)
        if result.strip() not in ('4','4.'):raise RuntimeError('Synthetic arithmetic reply failed')
        return
    if len(args)!=3 or args[0] not in PROFILES or not args[1].isdigit() or len(args[2])!=64:
        raise SystemExit('Use supervised Triad broker')
    serve(args[0],int(args[1]),args[2])
if __name__=='__main__':main()
