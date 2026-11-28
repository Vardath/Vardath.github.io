"""Lossless bounded numeric weight conversion between SafeTensors and NPZ.

No pickle, model graph execution, model downloads or production model changes.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import io
import json
import math
from pathlib import Path
import re
import struct
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.structured_source import strict_json

SCHEMA='deepthortriad-weight-format-conversion-v1'
DTYPES={'F32':('<f4',4),'F16':('<f2',2),'F64':('<f8',8),'I8':('|i1',1),'U8':('|u1',1),
        'I16':('<i2',2),'I32':('<i4',4),'I64':('<i8',8),'U16':('<u2',2),'U32':('<u4',4),'U64':('<u8',8),'BOOL':('|b1',1)}
FROM_NPY={v[0]:k for k,v in DTYPES.items()}
MAX_HEADER=65536
MAX_TENSORS=128
NAME=re.compile(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,119}')

def name_ok(name):
    return isinstance(name,str) and bool(NAME.fullmatch(name)) and name!='__metadata__' and not name.endswith('.')

def tensor_size(dtype,shape):
    if dtype not in DTYPES or not isinstance(shape,(list,tuple)) or len(shape)>6 or any(type(x) is not int or not 1<=x<=guard.MAX_INPUT for x in shape):
        raise ValueError('Unsupported dtype or nonempty tensor shape')
    n=math.prod(shape)*DTYPES[dtype][1]
    if not 1<=n<=guard.MAX_INPUT:raise ValueError('Tensor exceeds byte bound')
    return n

def validate_tensors(tensors):
    if not isinstance(tensors,dict) or not 1<=len(tensors)<=MAX_TENSORS:raise ValueError('Invalid tensor count')
    total=0
    for name,(dtype,shape,data) in tensors.items():
        if not name_ok(name) or not isinstance(data,bytes) or tensor_size(dtype,shape)!=len(data):
            raise ValueError('Invalid tensor entry')
        if dtype=='BOOL' and any(x not in (0,1) for x in data):raise ValueError('Noncanonical boolean bytes')
        total+=len(data)
        if total>guard.MAX_INPUT:raise ValueError('Combined tensor bytes exceed bound')
    return tensors

def read_safetensors(raw):
    if not 8<len(raw)<=guard.MAX_INPUT:raise ValueError('Invalid SafeTensors byte size')
    n=struct.unpack_from('<Q',raw)[0]
    if not 2<=n<=MAX_HEADER or 8+n>=len(raw):raise ValueError('Invalid SafeTensors header size')
    header=strict_json(raw[8:8+n].decode('utf8'));data=raw[8+n:]
    if not isinstance(header,dict) or not 1<=len(header)<=MAX_TENSORS+1:raise ValueError('Invalid SafeTensors header')
    if '__metadata__' in header:
        meta=header.pop('__metadata__')
        if not isinstance(meta,dict) or meta:raise ValueError('Nonempty metadata cannot be preserved in NPZ')
    out={};ranges=[]
    for name,v in header.items():
        if not name_ok(name) or not isinstance(v,dict) or set(v)!={'dtype','shape','data_offsets'}:
            raise ValueError('Invalid SafeTensors entry')
        dtype,shape,offsets=v['dtype'],v['shape'],v['data_offsets']
        if not isinstance(dtype,str) or not isinstance(shape,list) or not isinstance(offsets,list) or len(offsets)!=2 or any(type(x) is not int for x in offsets):
            raise ValueError('Invalid tensor descriptor')
        a,b=offsets
        if not 0<=a<b<=len(data) or b-a!=tensor_size(dtype,shape):raise ValueError('Invalid tensor offset')
        ranges.append((a,b));out[name]=(dtype,tuple(shape),data[a:b])
    pos=0
    for a,b in sorted(ranges):
        if a!=pos:raise ValueError('Overlapping or unindexed tensor bytes')
        pos=b
    if pos!=len(data):raise ValueError('Unindexed trailing data')
    return validate_tensors(out)

def write_safetensors(tensors):
    validate_tensors(tensors);header={};chunks=[];pos=0
    for name,(dtype,shape,data) in sorted(tensors.items()):
        header[name]={'dtype':dtype,'shape':list(shape),'data_offsets':[pos,pos+len(data)]}
        chunks.append(data);pos+=len(data)
    h=json.dumps(header,ensure_ascii=True,separators=(',',':')).encode('utf8')
    h+=b' '*((-len(h))%8)
    if len(h)>MAX_HEADER:raise ValueError('SafeTensors header too large')
    return struct.pack('<Q',len(h))+h+b''.join(chunks)

def read_npy(raw):
    if not 10<len(raw)<=guard.MAX_INPUT or raw[:6]!=b'\x93NUMPY' or raw[6:8]!=b'\x01\x00':
        raise ValueError('Only NPY version 1.0 supported')
    n=struct.unpack_from('<H',raw,8)[0]
    if not 2<=n<=MAX_HEADER or 10+n>=len(raw):raise ValueError('Invalid NPY header')
    h=raw[10:10+n]
    if not h.endswith(b'\n') or (10+n)%16:raise ValueError('Invalid NPY header alignment')
    try:
        node=ast.parse(h.decode('ascii').strip(),mode='eval').body
        if not isinstance(node,ast.Dict) or len(node.keys)!=3:raise ValueError('Expected exact NPY header')
        keys=[ast.literal_eval(k) for k in node.keys]
        if set(keys)!={'descr','fortran_order','shape'}:raise ValueError('Invalid NPY keys')
        d=ast.literal_eval(node)
    except (SyntaxError,TypeError,ValueError,RecursionError,UnicodeError) as e:raise ValueError('Invalid NPY header') from e
    if not isinstance(d['descr'],str) or d['descr'] not in FROM_NPY or d['fortran_order'] is not False or not isinstance(d['shape'],tuple):
        raise ValueError('Only supported little-endian contiguous numeric arrays; no object or pickle')
    dtype=FROM_NPY[d['descr']];shape=d['shape'];data=raw[10+n:]
    if tensor_size(dtype,shape)!=len(data):raise ValueError('Invalid NPY tensor size')
    return dtype,shape,data

def write_npy(tensor):
    dtype,shape,data=tensor
    h=repr({'descr':DTYPES[dtype][0],'fortran_order':False,'shape':shape}).encode('ascii')
    h+=b' '*((-(10+len(h)+1))%64)+b'\n'
    if len(h)>65535:raise ValueError('NPY header exceeds bound')
    return b'\x93NUMPY\x01\x00'+struct.pack('<H',len(h))+h+data

def read_npz(raw):
    if not 0<len(raw)<=guard.MAX_INPUT:raise ValueError('Invalid NPZ byte size')
    out={};total=0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        members=z.infolist()
        if not 1<=len(members)<=MAX_TENSORS:raise ValueError('Invalid NPZ member count')
        for m in members:
            name=m.filename[:-4]
            if not m.filename.endswith('.npy') or not name_ok(name) or name in out or m.flag_bits&1 or m.compress_type not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED):
                raise ValueError('Unexpected or duplicate NPZ member')
            total+=m.file_size
            if total>guard.MAX_INPUT or m.file_size<11:raise ValueError('NPZ expanded size exceeds bound')
            with z.open(m) as f:data=f.read(m.file_size+1)
            if len(data)!=m.file_size:raise ValueError('NPZ member size mismatch')
            out[name]=read_npy(data)
    return validate_tensors(out)

def write_npz(tensors):
    validate_tensors(tensors);stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,t in sorted(tensors.items()):
            info=zipfile.ZipInfo(name+'.npy');info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,write_npy(t))
    return stream.getvalue()

FORMATS={'safetensors':(read_safetensors,write_safetensors),'npz':(read_npz,write_npz)}

def checked(s,target):
    if not isinstance(s,dict) or set(s)!={'weights'} or not isinstance(s['weights'],str) or not s['weights']:
        raise ValueError('Choose one project-relative model weight file')
    source='npz' if target=='safetensors' else 'safetensors'
    if Path(s['weights']).suffix.casefold()!='.'+source:raise ValueError('Wrong input format')
    return s

def convert(raw,target):
    source='npz' if target=='safetensors' else 'safetensors'
    tensors=FORMATS[source][0](raw);payload=FORMATS[target][1](tensors)
    if len(payload)>guard.MAX_OUTPUT or FORMATS[target][0](payload)!=tensors:
        raise ValueError('Converted tensor roundtrip failed or exceeds bound')
    return payload,{'source_format':source,'output_format':target,'tensor_count':len(tensors),
        'tensor_bytes':sum(len(t[2]) for t in tensors.values()),'tensors':[{'name':name,'dtype':t[0],'shape':list(t[1]),'sha256':hashlib.sha256(t[2]).hexdigest()} for name,t in sorted(tensors.items())],
        'tensor_bytes_exact':True,'architecture_converted':False,'inference_verified':False}

def validation_args(target):
    return dict(schema=SCHEMA+'-'+target,checked=lambda s:checked(s,target),output_suffix='.'+target,
                extra=('weights','.npz' if target=='safetensors' else '.safetensors'))

def validate(root,plan,target='safetensors'):
    return guard.validate(root,plan,**validation_args(target))

def review(root,source,output,exclude=(),target='safetensors'):
    plan,s=guard.review(root,source,output,exclude,**validation_args(target))
    _,_,path=validate(root,plan,target);raw=guard.exact(path,plan['guards'][1],guard.MAX_INPUT)
    _,r=convert(raw,target)
    return plan,dict(s,conversion=r,scope='Lossless bounded numeric weight format conversion only. No graph, tokenizer, model loading, arbitrary code, production model installation or inference claim.')

def execute(root,plan,target='safetensors'):
    s,dst,path=validate(root,plan,target);raw=guard.exact(path,plan['guards'][1],guard.MAX_INPUT)
    payload,r=convert(raw,target)
    sha=guard.publish(payload,dst,lambda:validate(root,plan,target))
    return dict(r,schema=SCHEMA,status='weight_format_roundtrip_verified',output=plan['output'],
                sha256=sha,source_sha256=hashlib.sha256(raw).hexdigest(),source_unchanged=True)

def main(target='safetensors'):
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan),target),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
