"""Reviewed album assembly: shared mastering settings, ordered tagged WAVs and verified archive."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file
from deepthort_local import automated_mastering as mastering
from deepthort_local import music_metadata as metadata

SCHEMA='janus-album-production-v1'
MAX_TRACKS=8
MAX_TOTAL=12*1024*1024
SETTINGS={'threshold_dbfs','ratio','attack_ms','release_ms','target_rms_dbfs','max_boost_db','peak_dbfs'}

def literal(s):
    if not isinstance(s,str) or not s.strip() or len(s)>160 or any(not 32<=ord(c)<=126 for c in s):
        raise ValueError('Album metadata must be bounded printable ASCII')
    return s

def checked(s):
    if not isinstance(s,dict) or set(s)!={'album','artist','tracks','mastering'}:
        raise ValueError('Choose album, artist, ordered tracks and shared mastering settings')
    literal(s['album']);literal(s['artist'])
    if not isinstance(s['mastering'],dict) or set(s['mastering'])!=SETTINGS:
        raise ValueError('Explicit shared mastering settings required')
    mastering.checked(dict(s['mastering'],audio='input.wav'))
    tracks=s['tracks']
    if not isinstance(tracks,list) or not 2<=len(tracks)<=MAX_TRACKS:raise ValueError('Choose 2–8 tracks')
    seen=set()
    for t in tracks:
        if not isinstance(t,dict) or set(t)!={'audio','title'} or not isinstance(t['audio'],str) or t['audio'].casefold() in seen:
            raise ValueError('Distinct reviewed audio sources required')
        literal(t['title']);seen.add(t['audio'].casefold())
    return s

def paths_for(root,s,exclude):
    paths=[guard.path_for(root,t['audio'],exclude,{'.wav'},exists=True) for t in s['tracks']]
    if len(set(paths))!=len(paths) or sum(p.stat().st_size for p in paths)>MAX_TOTAL:
        raise ValueError('Duplicate or oversized album inputs')
    return paths

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or not 3<=len(plan['guards'])<=MAX_TRACKS+1:
        raise ValueError('Invalid album approval')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.zip')
    paths=paths_for(Path(root).resolve(strict=True),s,plan['exclude'])
    if len(paths)!=len(plan['guards'])-1 or any(snapshot_file(p)!=g for p,g in zip(paths,plan['guards'][1:])):
        raise ValueError('Reviewed album input changed')
    return s,dst,paths

def observations(s,paths,plan):
    result=[];fmt=None
    for p,g,t in zip(paths,plan['guards'][1:],s['tracks']):
        raw=guard.exact(p,g,MAX_TOTAL)
        _,r,c,n,rms=mastering.input_pcm(raw)
        if fmt is not None and fmt!=(r,c):raise ValueError('All album sources need matching rate and channels')
        fmt=(r,c)
        result.append({'audio':t['audio'],'title':t['title'],'sha256':g['expected'],'frames':n,'sample_rate':r,'channels':c,
                       'input_rms_dbfs':mastering.db(rms)})
    return result

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip')
    paths=paths_for(Path(plan['root']),s,plan['exclude'])
    plan['guards'].extend(snapshot_file(p) for p in paths)
    s,_,paths=validate(root,plan)
    return plan,dict(s,track_observations=observations(s,paths,plan),
                     scope='Ordered short-track mastering and RIFF INFO tagging, verified offline ZIP; no perceptual quality, store submission or rights certification.')

def bundle(s,paths,plan):
    observed=observations(s,paths,plan)
    entries={};tracks=[]
    for i,(p,g,t,obs) in enumerate(zip(paths,plan['guards'][1:],s['tracks'],observed),1):
        raw=guard.exact(p,g,MAX_TOTAL)
        mastered,report=mastering.master(raw,dict(s['mastering'],audio=t['audio']))
        tags={'title':t['title'],'artist':s['artist'],'album':s['album'],'track':str(i)}
        tagged,tag_receipt=metadata.edit(mastered,metadata.checked({'audio':t['audio'],'tags':tags}))
        if not tag_receipt['audio_bytes_unchanged'] or any(tag_receipt['after'].get(k)!=v for k,v in tags.items()):
            raise ValueError('Album metadata verification failed')
        name=f'tracks/{i:02d}.wav';entries[name]=tagged
        tracks.append({'number':i,'title':t['title'],'file':name,'source_sha256':obs['sha256'],
                       'sha256':hashlib.sha256(tagged).hexdigest(),'mastering':report,'tags':tags})
    receipt={'schema':SCHEMA,'album':s['album'],'artist':s['artist'],'tracks':tracks,
             'source_unchanged':True,'listening_verified':False,'lufs_verified':False,'published_remotely':False}
    entries['ALBUM.json']=(json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode()
    entries['PLAYLIST.m3u8']=(''.join(t['file']+'\n' for t in tracks)).encode()
    if sum(map(len,entries.values()))>guard.MAX_OUTPUT-4096:raise ValueError('Album exceeds archive bound')
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_STORED) as z:
        for name,raw in entries.items():
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));z.writestr(info,raw)
    result=buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(result)) as z:
        if z.testzip() is not None or z.namelist()!=list(entries) or any(z.read(k)!=v for k,v in entries.items()):
            raise ValueError('Album archive verification failed')
    return result,receipt

def execute(root,plan):
    s,dst,paths=validate(root,plan)
    payload,receipt=bundle(s,paths,plan)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'album_bundle_verified','output':plan['output'],'sha256':digest,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed album assembly unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
