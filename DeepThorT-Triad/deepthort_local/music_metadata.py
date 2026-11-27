"""Reviewed RIFF/WAVE INFO metadata editing without changing audio data."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard

SCHEMA='janus-music-metadata-v1'
EXTRA=('audio','.wav')
TAGS={'title':b'INAM','artist':b'IART','album':b'IPRD','year':b'ICRD','genre':b'IGNR',
      'track':b'ITRK','comment':b'ICMT','copyright':b'ICOP'}
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'audio','tags'} or not isinstance(spec['audio'],str) or not isinstance(spec['tags'],dict) or not spec['tags']:
        raise ValueError('Expected WAV source and explicit tag changes')
    for key,value in spec['tags'].items():
        if key not in TAGS:raise ValueError('Unsupported WAV INFO tag')
        if value is not None and (not isinstance(value,str) or not 1<=len(value)<=1000 or any(not 32<=ord(c)<=126 for c in value)):
            raise ValueError('INFO tag must be printable ASCII or null (remove)')
    return spec

def chunks(raw):
    pos=0;out=[]
    while pos<len(raw):
        if pos+8>len(raw) or len(out)>=1024:raise ValueError('Malformed or excessive RIFF chunks')
        code=raw[pos:pos+4];size=struct.unpack_from('<I',raw,pos+4)[0]
        end=pos+8+size;pad=end+(size&1)
        if pad>len(raw):raise ValueError('Truncated RIFF chunk')
        out.append((code,raw[pos+8:end],raw[pos:pad]));pos=pad
    return out
def chunk(code,data):return code+struct.pack('<I',len(data))+data+(b'\0' if len(data)&1 else b'')
def parse(raw):
    if len(raw)<12 or raw[:4]!=b'RIFF' or raw[8:12]!=b'WAVE' or struct.unpack_from('<I',raw,4)[0]!=len(raw)-8:
        raise ValueError('Expected complete little-endian RIFF WAVE file')
    top=chunks(raw[12:]);info=[i for i,(c,d,_) in enumerate(top) if c==b'LIST' and d[:4]==b'INFO']
    if len(info)>1 or sum(c==b'data' for c,d,_ in top)!=1 or sum(c==b'fmt ' for c,d,_ in top)!=1:
        raise ValueError('Ambiguous WAVE or INFO structure')
    if any(c.lower()==b'id3 ' for c,d,_ in top):
        raise ValueError('Mixed ID3/INFO WAV metadata is not supported')
    tags=chunks(top[info[0]][1][4:]) if info else []
    if len({c for c,d,_ in tags})!=len(tags):raise ValueError('Duplicate INFO tag')
    known={}
    for key,code in TAGS.items():
        for c,d,_ in tags:
            if c==code:
                if not d.endswith(b'\0') or b'\0' in d[:-1] or len(d)>1001:
                    raise ValueError('Unsupported existing INFO text')
                text=d[:-1].decode('ascii')
                if any(not 32<=ord(ch)<=126 for ch in text):raise ValueError('Unsupported existing INFO characters')
                known[key]=text
    try:
        with wave.open(io.BytesIO(raw),'rb') as f:
            params=f.getparams();audio=f.readframes(params.nframes)
            if not audio or len(audio)!=params.nframes*params.nchannels*params.sampwidth:
                raise ValueError('Invalid or empty PCM audio')
    except (wave.Error,EOFError) as e:raise ValueError('Unsupported PCM WAVE') from e
    return top,info[0] if info else None,tags,known,params,audio

def edit(raw,spec):
    top,idx,tags,before,params,audio=parse(raw)
    changes={TAGS[k]:v for k,v in spec['tags'].items()}
    outtags=[]
    for code,data,original in tags:
        if code in changes:
            value=changes.pop(code)
            if value is not None:outtags.append(chunk(code,value.encode('ascii')+b'\0'))
        else:outtags.append(original)
    for code,value in changes.items():
        if value is not None:outtags.append(chunk(code,value.encode('ascii')+b'\0'))
    newinfo=chunk(b'LIST',b'INFO'+b''.join(outtags)) if outtags else b''
    body=b'WAVE'+b''.join(newinfo if i==idx else original for i,(code,data,original) in enumerate(top))
    if idx is None:body+=newinfo
    result=b'RIFF'+struct.pack('<I',len(body))+body
    after_top,after_idx,after_tags,after,after_params,after_audio=parse(result)
    expected=dict(before)
    for key,value in spec['tags'].items():
        if value is None:expected.pop(key,None)
        else:expected[key]=value
    other=[original for i,(c,d,original) in enumerate(top) if i!=idx]
    after_other=[original for i,(c,d,original) in enumerate(after_top) if i!=after_idx]
    unedited=[original for c,d,original in tags if c not in {TAGS[k] for k in spec['tags']}]
    unedited_after=[original for c,d,original in after_tags if c not in {TAGS[k] for k in spec['tags']}]
    if after!=expected or other!=after_other or unedited!=unedited_after or params!=after_params or audio!=after_audio:
        raise ValueError('Audio or untouched chunk verification failed')
    return result,{'before':before,'after':after,'audio_sha256':hashlib.sha256(audio).hexdigest(),'audio_bytes_unchanged':True,'untouched_chunks_verified':True}

def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
    _,_,path=validate(root,plan);raw=guard.exact(path,plan['guards'][1],guard.MAX_INPUT)
    _,receipt=edit(raw,spec)
    return plan,dict(spec,reviewed_metadata=receipt)
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);payload,receipt=edit(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-music-metadata-result-v1','status':'metadata_and_audio_verified','output':plan['output'],
            'sha256':sha,**receipt,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        result=execute(a.root,json.loads(a.plan));result.pop('before');result.pop('after')
        print(json.dumps(result,sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Metadata editing unavailable; inspect PCM WAV and INFO tags'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
