"""Reviewed cue-timed mouth sprites with exact local PCM speech and verified video/audio mux."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.audio_conversion import installed
from deepthort_local.video_trimming import decode,encode_verified,run,MAX_RENDER_RGB
from deepthort_local.texture_pixels import image_module,decode as decode_png
from deepthort_local.image_composition import decode_layer
from deepthort_local.disk_gate import require_storage
SCHEMA='janus-lip-sync-v1'
RATE=48000

def checked(s):
    if not isinstance(s,dict) or set(s)!={'face','audio','mouth','sprites','cues','fps','frames'} or any(not isinstance(s[k],str) for k in ('face','audio')):
        raise ValueError('Specify face, speech WAV, mouth rectangle, sprite paths and timed cues')
    fps,n=s['fps'],s['frames']
    if type(fps) is not int or fps not in (24,25,30) or type(n) is not int or not 2<=n<=120:
        raise ValueError('Invalid duration or rate')
    r=s['mouth']
    if not isinstance(r,list) or len(r)!=4 or any(type(v) is not int for v in r):raise ValueError('Expected mouth rectangle')
    x,y,w,h=r
    if min(x,y)<0 or not 1<=w<=256 or not 1<=h<=256 or x+w>640 or y+h>480:
        raise ValueError('Mouth rectangle outside bounds')
    sprites=s['sprites']
    if not isinstance(sprites,list) or not 2<=len(sprites)<=4 or any(not isinstance(p,str) for p in sprites):
        raise ValueError('Choose two to four explicit mouth PNGs')
    names=[s['face'],s['audio'],*sprites]
    if len({p.casefold() for p in names})!=len(names):raise ValueError('Choose distinct input paths')
    cues=s['cues']
    if not isinstance(cues,list) or not 2<=len(cues)<=n:raise ValueError('Choose bounded mouth cues')
    last=-1;used=set()
    for c in cues:
        if not isinstance(c,dict) or set(c)!={'frame','sprite'} or type(c['frame']) is not int or not last<c['frame']<n or type(c['sprite']) is not int or not 0<=c['sprite']<len(sprites):
            raise ValueError('Invalid cue frame or sprite')
        last=c['frame'];used.add(c['sprite'])
    if cues[0]['frame']!=0 or len(used)<2:raise ValueError('Require initial cue and changing mouth shape')
    return s

def speech(raw,s):
    try:
        with wave.open(io.BytesIO(raw),'rb') as f:
            n=f.getnframes()
            if (f.getframerate(),f.getnchannels(),f.getsampwidth(),f.getcomptype())!=(RATE,1,2,'NONE') or n!=s['frames']*RATE//s['fps']:
                raise ValueError('Use mono PCM16 48 kHz WAV of exact animation duration')
            pcm=f.readframes(n)
            if len(pcm)!=n*2 or not any(pcm):raise ValueError('Truncated or silent speech')
    except (wave.Error,EOFError) as e:raise ValueError('Invalid speech WAV') from e
    return pcm

def prepare(raws,s):
    checked(s)
    if len(raws)!=2+len(s['sprites']):raise ValueError('Source count differs')
    w,h,_,face=decode_png(raws[0],('RGB',));x,y,mw,mh=s['mouth']
    if not 1<=w<=640 or not 1<=h<=480 or x+mw>w or y+mh>h or s['frames']*w*h*3>MAX_RENDER_RGB:
        raise ValueError('Mouth or frame buffer outside source canvas')
    pcm=speech(raws[1],s);Image=image_module();shapes=[]
    with Image.frombytes('RGB',(w,h),face) as front:
        for raw in raws[2:]:
            with decode_layer(raw) as sprite:
                if sprite.size!=(mw,mh):raise ValueError('Mouth sprite must match exact rectangle')
                with front.convert('RGBA') as canvas:
                    canvas.alpha_composite(sprite,dest=(x,y))
                    with canvas.convert('RGB') as final:shapes.append(final.tobytes())
    if len(set(shapes))!=len(shapes):raise ValueError('Mouth sprites must produce distinct visible frames')
    return (w,h),pcm,shapes

def sequence(shapes,s):
    out=bytearray();cues=s['cues'];j=0
    for i in range(s['frames']):
        if j+1<len(cues) and cues[j+1]['frame']==i:j+=1
        out.extend(shapes[cues[j]['sprite']])
    return out

def paths_for(root,s,exclude):
    pp=[guard.path_for(root,n,exclude,{'.wav'} if i==1 else {'.png'},exists=True)
        for i,n in enumerate([s['face'],s['audio'],*s['sprites']])]
    if any(a.samefile(b) for i,a in enumerate(pp) for b in pp[:i]) or sum(p.stat().st_size for p in pp)>guard.MAX_INPUT:
        raise ValueError('Duplicate or oversized inputs')
    return pp

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or not 7<=len(plan['guards'])<=9:
        raise ValueError('Invalid lip-sync approval')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.mp4')
    pp=paths_for(Path(root).resolve(strict=True),s,plan['exclude'])
    if len(plan['guards'])!=len(pp)+3 or tuple(plan['guards'][-2:])!=installed(root) or any(snapshot_file(p)!=g for p,g in zip(pp,plan['guards'][1:-2])):
        raise ValueError('Reviewed source or codec changed')
    return s,dst,pp

def inputs(pp,plan):
    return [guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(pp,plan['guards'][1:-2])]

def mux(selected,size,pcm,s,tools,folder):
    # First use the existing verified silent encoder. Then copy its H.264 stream
    # and encode speech losslessly as ALAC, checking both decoded streams.
    folder=Path(folder);ff,fp=(g['path'] for g in tools)
    encode_verified(selected,size,s['fps'],s['frames'],tools,folder)
    (folder/'speech.pcm').write_bytes(pcm)
    out=folder/'synced.mp4';verify_guards(tools)
    run(ff,['-nostdin','-hide_banner','-loglevel','error','-xerror','-n','-protocol_whitelist','file',
            '-f','mov','-enable_drefs','0','-use_absolute_path','0','-i','sequence.mp4',
            '-f','s16le','-ar',str(RATE),'-ac','1','-i','speech.pcm','-map','0:v:0','-map','1:a:0',
            '-c:v','copy','-c:a','alac','-threads','1','-map_metadata','-1','-movflags','+faststart',out.name],folder)
    meta=json.loads(run(fp,['-v','error','-protocol_whitelist','file','-f','mov','-enable_drefs','0','-use_absolute_path','0',
            '-show_entries','stream=codec_type,codec_name,width,height,avg_frame_rate,nb_frames,sample_rate,channels,start_time',
            '-of','json',out.name],folder))
    streams=meta.get('streams',[])
    if len(streams)!=2:raise ValueError('Expected exactly two streams')
    v,a=streams
    if (v.get('codec_type'),v.get('codec_name'),v.get('width'),v.get('height'),v.get('avg_frame_rate'),v.get('nb_frames'))!=('video','h264',*size,str(s['fps'])+'/1',str(s['frames'])) or (a.get('codec_type'),a.get('codec_name'),a.get('sample_rate'),a.get('channels'))!=('audio','alac',str(RATE),1) or any(float(x.get('start_time','nan'))!=0 for x in streams):
        raise ValueError('Mux stream geometry or origin mismatch')
    if decode(ff,out,0,s['frames'],*size)!=selected:raise ValueError('Mux video differs')
    observed=run(ff,['-nostdin','-hide_banner','-loglevel','error','-xerror','-protocol_whitelist','file',
        '-f','mov','-enable_drefs','0','-use_absolute_path','0','-i',out.name,'-map','0:a:0','-vn','-sn','-dn',
        '-c:a','pcm_s16le','-f','s16le','pipe:1'],folder,len(pcm))
    if observed!=pcm:raise ValueError('Mux speech bytes differ')
    verify_guards(tools)
    return guard.read_bound(out,guard.MAX_OUTPUT)

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4')
    pp=paths_for(Path(plan['root']),s,plan['exclude']);plan['guards'].extend(snapshot_file(p) for p in pp)
    plan['guards'].extend(installed(root));s,_,pp=validate(root,plan)
    size,pcm,_=prepare(inputs(pp,plan),s)
    return plan,dict(s,canvas=list(size),speech_samples=len(pcm)//2,scope='Explicit timed mouth-sprite cues with exact speech WAV; no phoneme recognition, neural face animation or automatic alignment.')

def execute(root,plan):
    s,dst,pp=validate(root,plan);size,pcm,shapes=prepare(inputs(pp,plan),s);selected=sequence(shapes,s)
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-lip-sync-',dir=dst.parent) as tmp:
        payload=mux(selected,size,pcm,s,plan['guards'][-2:],tmp)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'cue_timed_lip_sync_mux_verified','output':plan['output'],'sha256':digest,
        'frames':s['frames'],'fps':s['fps'],'speech_samples':len(pcm)//2,'speech_pcm_sha256':hashlib.sha256(pcm).hexdigest(),
        'decoded_rgb_verified':True,'decoded_pcm_verified':True,'phoneme_alignment_verified':False,'visual_quality_verified':False,'source_unchanged':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed lip synchronisation unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
