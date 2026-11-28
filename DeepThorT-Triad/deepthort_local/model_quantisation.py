"""Reviewed symmetric per-tensor signed INT8 weight quantisation.

Output is a portable weight bundle plus explicit scales, not a runnable
quantised LLM or native OpenVINO model. No installed model is modified.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import model_format_conversion as formats

SCHEMA='deepthortriad-reviewed-weight-int8-v1'
EXTRA=('weights','.safetensors')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'weights','tensors','max_abs_error'} or not isinstance(s['weights'],str) or not s['weights']:
        raise ValueError('Expected weights, exact selected tensor names and absolute error ceiling')
    names=s['tensors']
    if not isinstance(names,list) or not 1<=len(names)<=formats.MAX_TENSORS or any(not formats.name_ok(n) for n in names) or len(set(names))!=len(names):
        raise ValueError('Choose distinct supported tensor names')
    limit=s['max_abs_error']
    if type(limit) not in (int,float) or not math.isfinite(limit) or not 0<=limit<=1e10:
        raise ValueError('Invalid maximum absolute reconstruction error')
    return s

def quantise(t,limit):
    dtype,shape,data=t
    if dtype not in ('F16','F32'):raise ValueError('Selected tensor must be F16 or F32')
    fmt='<e' if dtype=='F16' else '<f'
    peak=0.
    for (x,) in struct.iter_unpack(fmt,data):
        if not math.isfinite(x):raise ValueError('Nonfinite selected weight')
        peak=max(peak,abs(x))
    scale=peak/127 if peak else 1.
    out=bytearray();worst=0.;squared=0.;count=0
    for (x,) in struct.iter_unpack(fmt,data):
        q=max(-127,min(127,round(x/scale)))
        error=abs(q*scale-x)
        worst=max(worst,error);squared+=error*error;count+=1
        out.append(q&255)
    if worst>limit:raise ValueError('Reconstructed weight exceeds approved absolute error ceiling')
    return ('I8',shape,bytes(out)),{'original_dtype':dtype,'shape':list(shape),'scale':scale,'zero_point':0,
        'max_abs_error':worst,'rmse':math.sqrt(squared/count),'original_bytes':len(data),'quantized_bytes':len(out)}

def bundle(raw,s):
    checked(s);source=formats.read_safetensors(raw)
    if not set(s['tensors'])<=source.keys():raise ValueError('Selected tensor not found')
    result=dict(source);metrics={}
    for name in s['tensors']:
        result[name],metrics[name]=quantise(source[name],s['max_abs_error'])
    weights=formats.write_safetensors(result)
    reopened=formats.read_safetensors(weights)
    if reopened!=result:raise ValueError('Quantised tensor roundtrip failed')
    for name,t in source.items():
        if name not in metrics:
            if reopened[name]!=t:raise ValueError('Unselected tensor changed')
            continue
        dtype,shape,data=t;fmt='<e' if dtype=='F16' else '<f'
        q=reopened[name][2];scale=metrics[name]['scale']
        worst=max(abs(x[0]-y[0]*scale) for x,y in zip(struct.iter_unpack(fmt,data),struct.iter_unpack('b',q)))
        if worst!=metrics[name]['max_abs_error'] or worst>s['max_abs_error']:
            raise ValueError('Independent stored INT8 reconstruction check failed')
    manifest={'schema':SCHEMA,'algorithm':'symmetric_per_tensor_int8_round_to_nearest_even',
              'reconstruction':'float_value = signed_int8 * scale','source_sha256':hashlib.sha256(raw).hexdigest(),
              'weights_sha256':hashlib.sha256(weights).hexdigest(),'max_abs_error_limit':s['max_abs_error'],
              'quantized_tensors':metrics,'unchanged_tensors':sorted(set(source)-set(metrics)),
              'source_tensor_bytes':sum(len(t[2]) for t in source.values()),
              'output_tensor_bytes':sum(len(t[2]) for t in result.values()),
              'weight_error_verified':True,'model_accuracy_verified':False,'runtime_compatibility_verified':False}
    entries={'quantized.safetensors':weights,'quantization.json':(json.dumps(manifest,sort_keys=True,allow_nan=False,indent=2)+'\n').encode()}
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in entries.items():z.writestr(name,data)
    payload=stream.getvalue()
    if len(payload)>guard.MAX_OUTPUT:raise ValueError('Quantisation bundle exceeds output bound')
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if sorted(z.namelist())!=sorted(entries) or any(z.read(n)!=v for n,v in entries.items()):
            raise ValueError('Quantisation bundle roundtrip failed')
    return payload,manifest

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
    _,_,path=validate(root,plan);_,r=bundle(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),s)
    return plan,dict(s,quantisation=r,scope='Selected F16/F32 weights only; signed INT8 with per-tensor scale and explicit reconstruction error ceiling. Unselected tensors preserved. No installed model change, executable inference graph, language-model quality or speed claim.')

def execute(root,plan):
    s,dst,path=validate(root,plan);payload,r=bundle(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),s)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return dict(r,status='int8_weight_bundle_verified',output=plan['output'],sha256=digest,source_unchanged=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
