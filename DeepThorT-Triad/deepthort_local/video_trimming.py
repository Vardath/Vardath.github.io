"""Reviewed frame-index trimming and sequencing of short silent local MP4 clips."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.audio_conversion import installed
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-video-trimming-v1'
MAX_FRAMES=120
def checked(s):
    if not isinstance(s,dict) or not {'clips','fps'}<=set(s)<= {'clips','fps','transitions','interpolation'} or type(s['fps']) is not int or s['fps'] not in (24,25,30):
        raise ValueError('Choose explicit 24, 25 or 30 fps and ordered clips')
    clips=s['clips']
    if not isinstance(clips,list) or not 1<=len(clips)<=4:raise ValueError('Choose 1–4 distinct MP4 clips')
    names=set();total=0
    for c in clips:
        if not isinstance(c,dict) or set(c) not in ({'video','start_frame','end_frame'},{'video','start_frame','end_frame','edit'}) or not isinstance(c['video'],str):
            raise ValueError('Expected video and inclusive start/exclusive end frame')
        a,b=c['start_frame'],c['end_frame']
        if type(a) is not int or type(b) is not int or not 0<=a<b<=300 or c['video'].casefold() in names:
            raise ValueError('Invalid frame range or repeated source')
        if 'edit' in c:checked_edit(c['edit'])
        names.add(c['video'].casefold());total+=b-a
    if total>MAX_FRAMES:raise ValueError('Initial sequence supports at most 120 selected input frames')
    checked_transitions(s)
    if s.get('interpolation','none') not in ('none','blend2x'):
        raise ValueError('Choose none or blend2x interpolation')
    if s.get('interpolation')=='blend2x' and total>MAX_FRAMES//2:
        raise ValueError('Interpolation supports at most 60 selected source frames')
    return s

def checked_transitions(s):
    clips=s['clips'];transitions=s.get('transitions',[{'kind':'cut','frames':0} for _ in clips[1:]])
    if not isinstance(transitions,list) or len(transitions)!=len(clips)-1:
        raise ValueError('Choose one transition per adjacent clip pair')
    overlaps=[]
    for item in transitions:
        if not isinstance(item,dict) or set(item)!={'kind','frames'} or type(item['frames']) is not int:
            raise ValueError('Invalid transition fields')
        n=item['frames']
        if not ((item['kind']=='cut' and n==0) or (item['kind']=='crossfade' and 1<=n<=12)):
            raise ValueError('Use cut/0 or crossfade/1–12 frames')
        overlaps.append(n)
    for i,c in enumerate(clips):
        before=overlaps[i-1] if i else 0;after=overlaps[i] if i<len(overlaps) else 0
        if before+after>=c['end_frame']-c['start_frame']:
            raise ValueError('Each clip must retain at least one non-transition frame')
    return transitions

def append_transition(selected,edited,size,transition):
    stride=size[0]*size[1]*3;n=transition['frames']
    if not n:
        selected.extend(edited);return
    if len(selected)<n*stride or len(edited)<n*stride:
        raise ValueError('Insufficient transition frames')
    from deepthort_local.texture_pixels import image_module
    Image=image_module();offset=len(selected)-n*stride
    for i in range(n):
        a=offset+i*stride;b=i*stride
        # Exclude endpoint duplicates; exact expected pixels checked after encoding.
        with Image.frombytes('RGB',size,bytes(selected[a:a+stride])) as left:
            with Image.frombytes('RGB',size,edited[b:b+stride]) as right:
                with Image.blend(left,right,(i+1)/(n+1)) as blend:
                    selected[a:a+stride]=blend.tobytes()
    selected.extend(edited[n*stride:])


def checked_edit(e):
    if not isinstance(e,dict) or set(e)!={'crop','rotation','flip'}:
        raise ValueError('Expected crop, rotation and flip')
    crop=e['crop']
    if crop is not None and (not isinstance(crop,list) or len(crop)!=4 or
        any(type(n) is not int for n in crop) or min(crop[:2])<0 or
        not 1<=crop[2]<=640 or not 1<=crop[3]<=480 or crop[0]+crop[2]>640 or crop[1]+crop[3]>480):
        raise ValueError('Invalid crop rectangle')
    if type(e['rotation']) is not int or e['rotation'] not in (0,90,180,270) or e['flip'] not in ('none','horizontal','vertical'):
        raise ValueError('Invalid discrete frame orientation')
    return e

def edited_size(size,edit):
    if edit is None:return size
    checked_edit(edit);w,h=size
    if edit['crop'] is not None:
        x,y,cw,ch=edit['crop']
        if x+cw>w or y+ch>h:raise ValueError('Crop lies outside decoded source')
        w,h=cw,ch
    if edit['rotation'] in (90,270):w,h=h,w
    if not 1<=w<=640 or not 1<=h<=480:raise ValueError('Edited frame exceeds output size bound')
    return w,h

def edit_frames(raw,size,edit):
    if edit is None:return raw
    from deepthort_local.texture_pixels import image_module
    Image=image_module();w,h=size;stride=w*h*3
    out_size=edited_size(size,edit)
    if not raw or len(raw)%stride:raise ValueError('Incomplete RGB frames')
    result=bytearray()
    for start in range(0,len(raw),stride):
        with Image.frombytes('RGB',size,raw[start:start+stride]) as frame:
            current=frame
            try:
                if edit['crop'] is not None:
                    x,y,cw,ch=edit['crop'];current=frame.crop((x,y,x+cw,y+ch))
                rotations={90:Image.Transpose.ROTATE_270,180:Image.Transpose.ROTATE_180,270:Image.Transpose.ROTATE_90}
                operations=[]
                if edit['rotation']:operations.append(rotations[edit['rotation']])
                if edit['flip']!='none':operations.append(Image.Transpose.FLIP_LEFT_RIGHT if edit['flip']=='horizontal' else Image.Transpose.FLIP_TOP_BOTTOM)
                for op in operations:
                    nxt=current.transpose(op)
                    if current is not frame:current.close()
                    current=nxt
                if current.size!=out_size:raise ValueError('Edited frame geometry mismatch')
                result.extend(current.tobytes())
            finally:
                if current is not frame:current.close()
    return bytes(result)

def run(exe,args,cwd,limit=65536):
    opts={'creationflags':subprocess.CREATE_NO_WINDOW} if sys.platform=='win32' else {}
    r=subprocess.run([exe,*args],cwd=str(cwd),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,timeout=60,check=False,**opts)
    if r.returncode or len(r.stdout)>limit or len(r.stderr)>1024*1024:
        raise ValueError('Local video operation failed or exceeded result bounds')
    return r.stdout

def probe(exe,path,*,allow_double=False):
    data=json.loads(run(exe,['-v','error','-protocol_whitelist','file','-f','mov',
        '-enable_drefs','0','-use_absolute_path','0','-show_entries',
        'stream=codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,nb_frames','-of','json',path.name],path.parent))
    streams=data.get('streams',[])
    if len(streams)!=1 or streams[0].get('codec_type')!='video' or streams[0].get('codec_name')!='h264':
        raise ValueError('Initial editor accepts one H.264 video stream only; audio and other streams are refused')
    v=streams[0];w,h=v.get('width'),v.get('height')
    if type(w) is not int or type(h) is not int or not 1<=w<=640 or not 1<=h<=480:
        raise ValueError('Source exceeds 640x480 bounds')
    try:n=int(v['nb_frames'])
    except (KeyError,TypeError,ValueError) as exc:raise ValueError('Source frame count unavailable') from exc
    rate=v.get('avg_frame_rate')
    allowed_rates=('24/1','25/1','30/1','48/1','50/1','60/1') if allow_double else ('24/1','25/1','30/1')
    if not 1<=n<=300 or rate not in allowed_rates or rate!=v.get('r_frame_rate'):
        raise ValueError('Expected short constant-rate video metadata')
    return {'width':w,'height':h,'frames':n,'fps':int(rate.split('/')[0])}

def decode(exe,path,first,last,w,h):
    # Fixed filter expressions contain only checked integer frame indices.
    n=last-first;limit=n*w*h*3
    data=run(exe,['-nostdin','-hide_banner','-loglevel','error','-xerror','-protocol_whitelist','file',
                  '-f','mov','-enable_drefs','0','-use_absolute_path','0','-threads','1','-i',path.name,
                  '-map','0:v:0','-an','-sn','-dn','-filter_threads','1',
                  '-vf',f'trim=start_frame={first}:end_frame={last},setpts=PTS-STARTPTS',
                  '-fps_mode','passthrough','-frames:v',str(n),'-threads','1','-pix_fmt','rgb24',
                  '-f','rawvideo','pipe:1'],path.parent,limit)
    if len(data)!=limit:raise ValueError('Decoded frame count differs from reviewed frame interval')
    return data

def interpolate_frames(raw,size):
    """Insert a midpoint between neighbors; duplicate final frame to retain duration."""
    from deepthort_local.texture_pixels import image_module
    Image=image_module();stride=size[0]*size[1]*3
    if not raw or len(raw)%stride or len(raw)//stride>MAX_FRAMES//2:
        raise ValueError('Invalid interpolation frame count')
    result=bytearray()
    for offset in range(0,len(raw),stride):
        a=bytes(raw[offset:offset+stride])
        result.extend(a)
        if offset+stride==len(raw):result.extend(a);continue
        b=bytes(raw[offset+stride:offset+2*stride])
        with Image.frombytes('RGB',size,a) as left:
            with Image.frombytes('RGB',size,b) as right:
                with Image.blend(left,right,.5) as middle:result.extend(middle.tobytes())
    return result

def observe(raws,s,tools,folder,*,render):
    checked(s)
    if len(raws)!=len(s['clips']):raise ValueError('Clip count mismatch')
    verify_guards(list(tools));ff,fp=(g['path'] for g in tools)
    folder=Path(folder);items=[];dimensions=None;selected=bytearray();transitions=checked_transitions(s)
    interpolation=s.get('interpolation','none');factor=2 if interpolation=='blend2x' else 1
    output_fps=s['fps']*factor
    rendered_transitions=[dict(t,frames=t['frames']*factor) for t in transitions]
    for i,(raw,c) in enumerate(zip(raws,s['clips'])):
        path=folder/f'input-{i}.mp4';path.write_bytes(raw)
        m=probe(fp,path);size=(m['width'],m['height'])
        edit=c.get('edit');out_size=edited_size(size,edit)
        if m['fps']!=s['fps'] or c['end_frame']>m['frames'] or (dimensions is not None and out_size!=dimensions):
            raise ValueError('Source frame range, edited dimensions or rate do not match reviewed sequence')
        dimensions=out_size
        item=dict(c,source_sha256=hashlib.sha256(raw).hexdigest(),source_format=m,edited_size=list(out_size))
        if render:
            frames=decode(ff,path,c['start_frame'],c['end_frame'],*size)
            item['selected_rgb_sha256']=hashlib.sha256(frames).hexdigest()
            edited=edit_frames(frames,size,edit)
            item['edited_rgb_sha256']=hashlib.sha256(edited).hexdigest()
            if factor==2:edited=interpolate_frames(edited,out_size)
            append_transition(selected,edited,out_size,rendered_transitions[i-1] if i else {'kind':'cut','frames':0})
        items.append(item)
    count=(sum(c['end_frame']-c['start_frame'] for c in s['clips'])-sum(t['frames'] for t in transitions))*factor
    if not render:return None,{'clips':items,'width':dimensions[0],'height':dimensions[1],'fps':output_fps,
        'transitions':rendered_transitions,'output_frames':count,'interpolation':interpolation}
    w,h=dimensions
    if len(selected)!=count*w*h*3:raise ValueError('Transition sequence length mismatch')
    raw_path=folder/'sequence.rgb';raw_path.write_bytes(selected)
    out=folder/'sequence.mp4'
    verify_guards(list(tools))
    run(ff,['-nostdin','-hide_banner','-loglevel','error','-xerror','-n','-protocol_whitelist','file',
            '-f','rawvideo','-pixel_format','rgb24','-video_size',f'{w}x{h}','-framerate',str(output_fps),
            '-i',raw_path.name,'-map','0:v:0','-an','-threads','1','-c:v','libx264rgb',
            '-preset','ultrafast','-crf','0','-pix_fmt','rgb24','-map_metadata','-1',
            '-movflags','+faststart',out.name],folder)
    payload=guard.read_bound(out,guard.MAX_OUTPUT)
    meta=probe(fp,out,allow_double=factor==2)
    if meta!={'width':w,'height':h,'frames':count,'fps':output_fps}:
        raise ValueError('Output video format or frame count mismatch')
    if decode(ff,out,0,count,w,h)!=selected:
        raise ValueError('Output RGB frames differ from selected input sequence')
    verify_guards(list(tools))
    return payload,{'clips':items,'width':w,'height':h,'fps':output_fps,'frames':count,
                    'duration_seconds':count/output_fps,'transitions':rendered_transitions,'interpolation':interpolation,'selected_rgb_sha256':hashlib.sha256(selected).hexdigest(),
                    'decoded_rgb_sequence_verified':True,'audio_supported':False,'visual_playback_verified':False,
                    'encoding':'lossless H.264 RGB; playback compatibility may vary'}

def _paths(root,s,exclude):
    paths=[guard.path_for(root,c['video'],exclude,{'.mp4'},exists=True) for c in s['clips']]
    if len({str(p).casefold() for p in paths})!=len(paths) or any(p.stat().st_size>guard.MAX_INPUT for p in paths):
        raise ValueError('Duplicate or oversized video source')
    return paths

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or not 4<=len(plan['guards'])<=7:
        raise ValueError('Invalid video approval')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.mp4')
    paths=_paths(Path(root).resolve(strict=True),s,plan['exclude'])
    if len(plan['guards'])!=len(paths)+3 or tuple(plan['guards'][-2:])!=installed(root):
        raise ValueError('Reviewed source count or codec installation changed')
    if any(snapshot_file(p)!=g for p,g in zip(paths,plan['guards'][1:-2])):
        raise ValueError('Reviewed clip changed')
    return s,dst,paths

def operation(root,plan,render):
    s,dst,paths=validate(root,plan)
    raws=[guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(paths,plan['guards'][1:-2])]
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-video-',dir=dst.parent) as tmp:
        return observe(raws,s,plan['guards'][-2:],tmp,render=render)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4')
    paths=_paths(Path(plan['root']),s,plan['exclude'])
    plan['guards'].extend(snapshot_file(p) for p in paths);plan['guards'].extend(installed(root))
    _,m=operation(root,plan,False)
    return plan,dict(s,observations=m,scope='Short silent H.264 MP4 clips only; frame-index sequence with optional crop, clockwise rotation and flip; optional crossfade/cut transitions and 2x midpoint blending; no audio or motion-compensated interpolation.')
def execute(root,plan):
    _,dst,_=validate(root,plan);payload,r=operation(root,plan,True)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-video-trimming-result-v1','status':'video_frame_sequence_verified','output':plan['output'],
            'sha256':sha,**r,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Video operation unavailable; inspect silent MP4, frame ranges, dimensions and reviewed codec installation'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
