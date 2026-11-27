"""Reusable reviewed layered character cutout animation with invariant artwork."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.texture_pixels import decode,image_module
from deepthort_local.audio_conversion import installed
from deepthort_local.video_trimming import encode_verified,MAX_RENDER_RGB
from deepthort_local.disk_gate import require_storage

SCHEMA='deepthortriad-character-animation-v1'

def ints(v,n):
    return isinstance(v,list) and len(v)==n and all(type(x) is int for x in v)

def checked(s):
    keys={'character_name','artwork','mask','background','fps','frames','parts'}
    if not isinstance(s,dict) or set(s)!=keys:raise ValueError('Expected reviewed character artwork, mask, background and part animation')
    for k in ('character_name','artwork','mask','background'):
        if not isinstance(s[k],str) or not 1<=len(s[k].strip())<=300 or any(ord(c)<32 for c in s[k]):
            raise ValueError('Invalid character name or asset path')
    if len({s[k].casefold() for k in ('artwork','mask','background')})!=3:raise ValueError('Choose distinct input assets')
    n=s['frames']
    if type(n) is not int or not 2<=n<=120 or type(s['fps']) is not int or s['fps'] not in (24,25,30):
        raise ValueError('Use 2–120 frames at 24/25/30 fps')
    parts=s['parts'];names=set()
    if not isinstance(parts,list) or not 1<=len(parts)<=8:raise ValueError('Use 1–8 ordered character parts')
    for part in parts:
        if not isinstance(part,dict) or set(part)!={'name','rect','keys'}:raise ValueError('Expected part name, source rectangle and keyframes')
        name=part['name'];rect=part['rect'];keys=part['keys']
        if not isinstance(name,str) or not 1<=len(name.strip())<=60 or any(ord(c)<32 for c in name) or name.casefold() in names:
            raise ValueError('Unique bounded part names required')
        names.add(name.casefold())
        if not ints(rect,4) or min(rect[:2])<0 or min(rect[2:])<1 or rect[0]+rect[2]>640 or rect[1]+rect[3]>480:
            raise ValueError('Invalid artwork rectangle')
        if not isinstance(keys,list) or not 2<=len(keys)<=16:raise ValueError('Use 2–16 part keyframes')
        previous=-1
        for k in keys:
            if not ints(k,3) or not previous<k[0]<n or min(k[1:])<0 or k[1]+rect[2]>640 or k[2]+rect[3]>480:
                raise ValueError('Invalid ordered keyframe [frame,x,y]')
            previous=k[0]
        if keys[0][0]!=0 or keys[-1][0]!=n-1:raise ValueError('Every part needs first and last frame keys')
    if not any(any(k[1:]!=p['keys'][0][1:] for k in p['keys'][1:]) for p in parts):
        raise ValueError('At least one character part must move')
    return s

def position(keys,frame):
    for a,b in zip(keys,keys[1:]):
        if a[0]<=frame<=b[0]:
            span=b[0]-a[0];step=frame-a[0]
            return tuple((a[i]*(span-step)+b[i]*step+span//2)//span for i in (1,2))
    raise ValueError('Frame outside keyframes')

def assets(raws,s):
    checked(s)
    aw,ah,_,art=decode(raws[0],('RGB',));mw,mh,_,mask=decode(raws[1],('L',))
    w,h,_,bg=decode(raws[2],('RGB',))
    if (mw,mh)!=(aw,ah) or not 1<=aw<=640 or not 1<=ah<=480 or not 1<=w<=640 or not 1<=h<=480 or w*h*3*s['frames']>MAX_RENDER_RGB:
        raise ValueError('Artwork, mask or canvas exceeds geometry bounds')
    if set(mask)-{0,255} or not any(mask):raise ValueError('Use a nonempty exact binary mask')
    covered=bytearray(aw*ah);parts=[]
    for part in s['parts']:
        x,y,pw,ph=part['rect']
        if x+pw>aw or y+ph>ah or any(k[1]+pw>w or k[2]+ph>h for k in part['keys']):
            raise ValueError('Part or placement exceeds exact canvas')
        rgb=bytearray();alpha=bytearray()
        for row in range(y,y+ph):
            for col in range(x,x+pw):
                i=row*aw+col
                if covered[i]:raise ValueError('Source part rectangles overlap')
                covered[i]=1;alpha.append(mask[i]);rgb.extend(art[i*3:i*3+3])
        if not any(alpha):raise ValueError('Part has no visible character pixels')
        parts.append((part,pw,ph,bytes(rgb),bytes(alpha)))
    if any(a and not b for a,b in zip(mask,covered)):
        raise ValueError('Every opaque character pixel must belong to a part')
    return (w,h,bg,parts)

def compose(raws,s):
    w,h,bg,parts=assets(raws,s);Image=image_module();out=bytearray();observations=[]
    prepared=[]
    try:
        for part,pw,ph,rgb,mask in parts:
            prepared.append((part,Image.frombytes('RGB',(pw,ph),rgb),Image.frombytes('L',(pw,ph),mask)))
        for i in range(s['frames']):
            with Image.frombytes('RGB',(w,h),bg) as canvas:
                row=[]
                for part,sprite,alpha in prepared:
                    xy=position(part['keys'],i)
                    canvas.paste(sprite,xy,alpha)
                    row.append({'part':part['name'],'position':list(xy)})
                out.extend(canvas.tobytes());observations.append(row)
    finally:
        for _,sprite,alpha in prepared:sprite.close();alpha.close()
    stride=w*h*3
    if len(out)!=stride*s['frames'] or all(out[:stride]==out[i:i+stride] for i in range(stride,len(out),stride)):
        raise ValueError('No observable character motion')
    records=[{'name':part['name'],'rgb_sha256':hashlib.sha256(rgb).hexdigest(),'mask_sha256':hashlib.sha256(mask).hexdigest()}
             for part,_,_,rgb,mask in parts]
    return out,{'width':w,'height':h,'frames':s['frames'],'fps':s['fps'],'character_name':s['character_name'],
        'part_artwork':records,'placements':observations,'rgb_sequence_sha256':hashlib.sha256(out).hexdigest(),
        'same_source_part_pixels_used':True,'neural_pose_generation':False,'semantic_identity_verified':False,
        'visual_quality_verified':False,'audio_supported':False}

def paths(root,s,exclude):
    pp=[guard.path_for(root,s[k],exclude,{'.png'},exists=True) for k in ('artwork','mask','background')]
    if any(p.stat().st_size>guard.MAX_INPUT for p in pp) or any(p.samefile(q) for i,p in enumerate(pp) for q in pp[:i]):
        raise ValueError('Duplicate or oversized source assets')
    return pp

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=6:
        raise ValueError('Invalid animation approval')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.mp4')
    pp=paths(Path(root).resolve(strict=True),s,plan['exclude'])
    if any(snapshot_file(p)!=g for p,g in zip(pp,plan['guards'][1:4])) or tuple(plan['guards'][4:])!=installed(root):
        raise ValueError('Reviewed character assets or codecs changed')
    return s,dst,pp

def inputs(pp,plan):return [guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(pp,plan['guards'][1:4])]

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4')
    plan['guards'].extend(snapshot_file(p) for p in paths(Path(plan['root']),s,plan['exclude']))
    plan['guards'].extend(installed(root))
    _,_,pp=validate(root,plan);w,h,_,parts=assets(inputs(pp,plan),s)
    return plan,dict(s,canvas=[w,h],character_artwork_sha256=plan['guards'][1]['expected'],
        scope='Reuse exact opaque character part pixels across independently keyed integer translations. Bottom-to-top draw order; later parts may occlude earlier parts. No neural pose synthesis, deformation, face identification or automatic publication.')

def execute(root,plan):
    s,dst,pp=validate(root,plan);raws=inputs(pp,plan);selected,receipt=compose(raws,s)
    require_storage(dst.parent);tools=plan['guards'][4:];verify_guards(tools)
    with tempfile.TemporaryDirectory(prefix='.deepthortriad-character-',dir=dst.parent) as tmp:
        payload=encode_verified(selected,(receipt['width'],receipt['height']),s['fps'],s['frames'],tools,Path(tmp))
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'consistent_character_cutout_frames_verified','output':plan['output'],'sha256':sha,
        'artwork_sha256':hashlib.sha256(raws[0]).hexdigest(),'mask_sha256':hashlib.sha256(raws[1]).hexdigest(),
        'background_sha256':hashlib.sha256(raws[2]).hexdigest(),'source_unchanged':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
