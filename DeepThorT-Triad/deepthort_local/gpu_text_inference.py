"""Reviewed one-shot native GPU text generation, never the production CPU route."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import re
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.triad_profiles import ROOT,ALL_PROFILES,RUNTIME_VERSION,installed_files,model_path,runtime_path
from deepthort_local.action_guards import snapshot_file
from deepthort_local.source_security import linked
from deepthort_local.agent_contract import canonical_sha
from deepthort_local.disk_gate import DiskGate,require_storage

SCHEMA='deepthortriad-reviewed-gpu-text-v1'
MARKER='DEEPTHORTRIAD_GPU_RESULT '
GIB=1024**3

def checked(s):
    if not isinstance(s,dict) or set(s)!={'role','device','prompt','max_tokens'}:
        raise ValueError('Choose role, explicit GPU device, prompt and token bound')
    if not isinstance(s['role'],str) or s['role'] not in ALL_PROFILES:
        raise ValueError('Choose existing text worker profile')
    if not isinstance(s['device'],str) or not re.fullmatch(r'GPU\.[0-9]{1,2}',s['device']):
        raise ValueError('Choose exact GPU.0 through GPU.99; no AUTO, CPU or fallback')
    if not isinstance(s['prompt'],str) or not 1<=len(s['prompt'])<=500 or not s['prompt'].strip() or any(ord(c)<32 for c in s['prompt']):
        raise ValueError('Choose a bounded single-line text prompt')
    if type(s['max_tokens']) is not int or not 8<=s['max_tokens']<=64:
        raise ValueError('Choose 8–64 generated tokens')
    return s

def inventory(role):
    files=installed_files(role);folder=model_path(role)
    exe=runtime_path()
    for path in (folder,exe.parent,exe,*[folder/n for n in files],folder/'verified-install.json'):
        if linked(path):raise ValueError('Linked local runtime/model member refused')
    entries={n:snapshot_file(folder/n,kind='stat' if n.endswith('.bin') else 'sha256') for n in files}
    return {'role':role,'revision':ALL_PROFILES[role][2],'runtime':RUNTIME_VERSION,
            'runtime_file':snapshot_file(exe,kind='stat'),'receipt':snapshot_file(folder/'verified-install.json'),
            'inventory_sha':canonical_sha(entries)}

def validate(root,plan):
    if not isinstance(plan,dict) or 'model' not in plan:raise ValueError('Invalid GPU approval')
    s,dst,_=guard.validate(root,{k:v for k,v in plan.items() if k!='model'},schema=SCHEMA,checked=checked,output_suffix='.json')
    if plan['model']!=inventory(s['role']):raise ValueError('Reviewed installed model or runtime changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    plan['model']=inventory(s['role']);validate(root,plan)
    return plan,dict(s,model=plan['model'],scope='EXPERIMENTAL: explicitly selected local OpenVINO GPU; one short request, no automatic fallback. GPU VRAM and utilisation are not capped by the Windows Job Object. Close games before approval. Incompatible drivers can fail or crash the GPU plugin. Production CPU workers unchanged.')

def native(s):
    from importlib.metadata import version
    from deepthort_local.triad_job import verify_root_cap
    from deepthort_local.native_offline import disable_openvino_telemetry
    from triad_openvino_worker import model_messages,final_text
    verify_root_cap();disable_openvino_telemetry()
    import openvino as ov
    import openvino_genai as genai
    if version('openvino-genai')!=RUNTIME_VERSION:raise ValueError('Unexpected native runtime version')
    installed_files(s['role'])
    device=s['device'];core=ov.Core()
    name=str(core.get_property(device,'FULL_DEVICE_NAME'))
    total=int(core.get_property(device,'GPU_DEVICE_TOTAL_MEM_SIZE'))
    if not name or total<4*GIB:raise ValueError('GPU device identity or minimum total memory unavailable')
    start=time.monotonic()
    pipe=genai.LLMPipeline(str(model_path(s['role'])),device)
    load=time.monotonic()-start
    history=genai.ChatHistory()
    for item in model_messages(s['role'],[{'role':'user','content':s['prompt']}]):history.append(item)
    if s['role'] in ('janus','sentinel'):history.set_extra_context({'enable_thinking':False})
    cfg=genai.GenerationConfig();cfg.max_new_tokens=s['max_tokens'];cfg.do_sample=False;cfg.num_beams=1
    start=time.monotonic();out=pipe.generate(history,cfg);elapsed=time.monotonic()-start
    text=final_text(s['role'],out.texts[0])
    return {'device':device,'device_name':name,'total_device_memory_bytes':total,
            'text':text,'load_seconds':load,'generation_seconds':elapsed,'runtime':RUNTIME_VERSION,
            'role':s['role'],'max_tokens':s['max_tokens']}

def assess(r,s):
    keys={'device','device_name','total_device_memory_bytes','text','load_seconds','generation_seconds','runtime','role','max_tokens'}
    if not isinstance(r,dict) or set(r)!=keys or any(r[k]!=s[k] for k in ('device','role','max_tokens')) or r['runtime']!=RUNTIME_VERSION:
        raise ValueError('Unexpected GPU inference receipt')
    if not isinstance(r['device_name'],str) or not 1<=len(r['device_name'])<=300 or type(r['total_device_memory_bytes']) is not int or r['total_device_memory_bytes']<4*GIB:
        raise ValueError('GPU identity or memory receipt unavailable')
    if not isinstance(r['text'],str) or not r['text'].strip() or len(r['text'])>8192:
        raise ValueError('Missing bounded generated text')
    if any(type(r[k]) not in (int,float) or not math.isfinite(r[k]) or r[k]<0 for k in ('load_seconds','generation_seconds')):
        raise ValueError('Invalid timings')
    return dict(r,device_requested_explicitly=True,cpu_fallback_configured=False,gpu_utilisation_verified=False,
                gpu_memory_limit_enforced=False,production_backend_changed=False,speedup_verified=False,
                semantic_quality_verified=False)

def run(s,stage):
    from deepthort_local.triad_job import verify_root_cap,child_server
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    cap,available,total=verify_root_cap()
    if cap<4*GIB or available<total//10+4*GIB:raise ValueError('Insufficient protected host headroom')
    gaming=DiskGate(game_names_path=ROOT/'game_executables.txt',game_flag=ROOT/'state/game-active.flag')
    sampler=WindowsPressureSampler()
    if gaming.gaming():raise ValueError('Gaming priority')
    log=stage/'gpu.log';receipt=stage/'receipt.json'
    with child_server([str(runtime_path()),'-I','-B',str(Path(__file__).resolve()),'--inside',json.dumps(s),'--receipt',str(receipt)],stage,log) as (_,alive):
        deadline=time.monotonic()+240
        while alive():
            _,free=sampler.read()
            if gaming.gaming() or free is None or free<15 or time.monotonic()>=deadline or log.stat().st_size>65536:
                raise ValueError('GPU inference stopped on gaming, host reserve, time or log bound')
            time.sleep(.25)
        if alive.code()!=0:raise ValueError('GPU native process failed; device/driver or model unsupported')
    return json.loads(guard.read_bound(receipt,32768))

def execute(root,plan,*,backend=None):
    s,dst=validate(root,plan);require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.deepthortriad-gpu-',dir=dst.parent) as tmp:
        r=assess((backend or run)(s,Path(tmp)),s)
    r.update(schema=SCHEMA,model=plan['model'],backend='native_openvino_gpu' if backend is None else 'injected_fixture')
    payload=(json.dumps(r,ensure_ascii=True,allow_nan=False,indent=2)+'\n').encode()
    if json.loads(payload)!=r:raise ValueError('GPU receipt roundtrip failed')
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return dict(r,status='gpu_text_result_saved',output=plan['output'],sha256=sha)

def main():
    p=argparse.ArgumentParser();p.add_argument('--root');p.add_argument('--plan');p.add_argument('--inside');p.add_argument('--receipt');a=p.parse_args()
    try:
        if a.inside is not None:
            r=native(checked(json.loads(a.inside)))
            with Path(a.receipt).open('x',encoding='utf8') as f:json.dump(r,f,allow_nan=False)
        else:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True)
        return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
