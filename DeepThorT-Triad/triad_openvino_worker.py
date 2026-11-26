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
from deepthort_local.triad_profiles import ROOT,ALL_PROFILES as PROFILES,RUNTIME_VERSION,model_path,installed_files
from deepthort_local.inference_metrics import measured,runtime_counts
from deepthort_local.triad_job import verify_root_cap
from deepthort_local.triad_errors import native_error,synthetic

def probe():
    from deepthort_local.native_offline import disable_openvino_telemetry
    disable_openvino_telemetry()
    import openvino as ov
    import openvino_genai as genai
    import numpy as np
    if version('openvino-genai')!=RUNTIME_VERSION:raise RuntimeError('Incorrect installed OpenVINO GenAI version')
    core=ov.Core()
    # available_devices probes every registered plugin, including Intel GPU.
    # On this Windows machine its OpenCL loader is incompatible. Ask for CPU
    # explicitly instead; actual CPU compilation below proves availability.
    core.get_property('CPU','FULL_DEVICE_NAME')
    x=ov.opset13.parameter([1],ov.Type.f32)
    graph=ov.Model([ov.opset13.add(x,x)],[x])
    compiled=core.compile_model(graph,'CPU',{'INFERENCE_NUM_THREADS':1,'NUM_STREAMS':1})
    out=next(iter(compiled([np.array([2],dtype=np.float32)]).values()))
    if float(out[0])!=4:raise RuntimeError('CPU runtime numerical probe failed')
    if not hasattr(genai,'ChatHistory'):raise RuntimeError('OpenVINO GenAI ChatHistory API missing')
    print('OpenVINO GenAI',version('openvino-genai'),'CPU numerical preflight passed',flush=True)

# Full V8 scheduler restored for the authorized 40% resource trial.
MAX_CONTEXT_TOKENS=4096
KV_BLOCKS=256
PREFILL_BATCH_TOKENS=128

def bounded_scheduler(genai):
    # Explicit cache block ceiling rather than the latency-oriented default
    # scheduler with unlimited prefill batch and persistent prefix cache.
    cfg=genai.SchedulerConfig()
    cfg.max_num_seqs=1
    cfg.max_num_batched_tokens=PREFILL_BATCH_TOKENS
    cfg.num_kv_blocks=KV_BLOCKS
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

def model_messages(role,messages):
    # Only SmolLM3 receives its documented system-level mode flag.
    # Copy inputs so the durable user specification and caller history
    # are never modified. Keep existing system instructions intact.
    from deepthort_local.agent_doctrine import bind_messages
    result=bind_messages(role,messages)
    if role=='janus':
        if result and result[0]['role']=='system':
            result[0]['content'] += '\n/no_think'
        else:
            result.insert(0,{'role':'system','content':'/no_think'})
    return result

def thinking_enabled(role,tokens):
    # Explicitly budgeted long Sentinel requests may use Qwen's thinking
    # template. Short availability probes and the baseline holistic audit
    # retain the same direct-answer mode as V7.
    return role=='sentinel' and tokens>=512

class Engine:
    def __init__(self,role):
        from deepthort_local.native_offline import disable_openvino_telemetry
        disable_openvino_telemetry()
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
        print('Native profile:',role,'one CPU thread; bounded scheduler;',
              'KV blocks',KV_BLOCKS,'prefill batch',PREFILL_BATCH_TOKENS,
              'context limit',MAX_CONTEXT_TOKENS,flush=True)
        self.tokenizer=self.pipe.get_tokenizer()
        print('Resident native OpenVINO CPU model ready:',role,flush=True)

    def generate_raw(self,messages,tokens):
        from deepthort_local.context_compaction import fit_native
        def prepare(current):
            history=self.genai.ChatHistory()
            for message in model_messages(self.role,current):history.append(message)
            if self.role in ('janus','sentinel'):
                history.set_extra_context({'enable_thinking':thinking_enabled(self.role,tokens)})
            rendered=self.tokenizer.apply_chat_template(history,add_generation_prompt=True)
            encoded=self.tokenizer.encode(rendered,add_special_tokens=False)
            return history,int(encoded.input_ids.shape[-1])
        history,count,removed=fit_native(messages,tokens,MAX_CONTEXT_TOKENS,prepare)
        if removed:print('Native context compacted:',removed,'historical exchanges omitted;',count,'input tokens',flush=True)
        config=self.genai.GenerationConfig()
        config.max_new_tokens=tokens
        config.do_sample=False
        config.num_beams=1
        # Tokenized preflight is for length only; generate uses native history.
        with measured(ROOT/'state',self.role,'native',budget_tokens=tokens,input_tokens=count,omitted_exchanges=removed) as metrics:
            out=self.pipe.generate(history,config)
            metrics.update(runtime_counts(out))
            raw=out.texts[0]
            if not isinstance(raw,str) or not raw.strip():raise RuntimeError('Native inference produced no text')
        return raw

    def generate(self,messages,tokens):
        raw=self.generate_raw(messages,tokens)
        # Qwen's template may prefill the opening tag. Require a completed
        # thought block for thinking-mode requests, never accept a partial
        # chain as the final structured answer.
        if thinking_enabled(self.role,tokens):
            if '</think>' not in raw:raise ValueError('Sentinel reasoning budget ended without completed thought block')
            raw=raw.split('</think>',1)[1]
        return final_text(self.role,raw)

def smoke_result(role,raw):
    """Runtime availability is distinct from strict answer correctness."""
    if not isinstance(raw,str) or not raw.strip():
        raise RuntimeError('Native inference produced no text')
    try:
        answer=final_text(role,raw)
        exact=answer.strip() in ('4','4.')
    except ValueError:
        exact=False
    return {'role':role,'native_generation':'passed',
            'exact_arithmetic_reply':'passed' if exact else 'failed'}

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
    from deepthort_local.win_cpu_cap import suppress_native_error_dialogs
    suppress_native_error_dialogs()
    verify_root_cap()
    import faulthandler
    faulthandler.enable()
    args=sys.argv[1:]
    if args==['--probe']:probe();return
    if len(args)==2 and args[0]=='--smoke' and args[1] in PROFILES:
        engine=Engine(args[1])
        # A nonempty real generation proves the runtime executes, not that
        # the checkpoint follows instructions. Never fabricate the expected 4.
        raw=engine.generate_raw([{'role':'user','content':'What is 2 + 2? Answer only with the number.'}],16)
        result=smoke_result(args[1],raw)
        print('Synthetic reply:',raw[:500],flush=True)
        print('TRIAD_SMOKE_RESULT '+json.dumps(result,sort_keys=True),flush=True)
        if result['exact_arithmetic_reply']!='passed':
            print('QUALITY WARNING: exact arithmetic reply failed; native generation passed. Continue installation, then run strict role acceptance.',flush=True)
        return
    if len(args)!=3 or args[0] not in PROFILES or not args[1].isdigit() or len(args[2])!=64:
        raise SystemExit('Use supervised Triad broker')
    serve(args[0],int(args[1]),args[2])
if __name__=='__main__':main()
