"""Explicit offline image-to-image generation using the existing local SD1.5 model.

The approved input is hash-bound, the output is a new project file, and no
model installation or network access is performed by this producer.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file
from deepthort_local.texture_pixels import decode,encode,image_module
from deepthort_local.source_security import exclusions

SCHEMA='janus-image-to-image-v1'
FIELDS={'schema','image','source_sha256','output','prompt','size','steps','strength_percent','seed'}
REF_FIELDS={'reference','reference_sha256','palette_strength_percent'}
MASK_FIELDS={'mask','mask_sha256'}
CHARACTER_FIELDS={'character_name','character_region_sha256'}
OUT_FIELDS={'offset_x','offset_y'}
REMOVE_FIELDS={'operation','removed_object'}
REPLACE_FIELDS=REMOVE_FIELDS|{'replacement_object'}
POSE_FIELDS={'guide_kind','guide_layout'}
DEPTH_FIELDS=POSE_FIELDS|{'near_is_white','relief_percent'}
SKETCH_FIELDS=POSE_FIELDS|{'light_background','line_strength_percent'}

def checked(s):
    if not isinstance(s,dict) or set(s) not in (FIELDS,FIELDS|REF_FIELDS,FIELDS|MASK_FIELDS,FIELDS|MASK_FIELDS|CHARACTER_FIELDS,FIELDS|OUT_FIELDS,FIELDS|MASK_FIELDS|REMOVE_FIELDS,FIELDS|MASK_FIELDS|REPLACE_FIELDS,FIELDS|POSE_FIELDS,FIELDS|DEPTH_FIELDS,FIELDS|SKETCH_FIELDS) or s['schema']!=SCHEMA:
        raise ValueError('Invalid image-to-image request')
    if any(not isinstance(s[k],str) or not s[k] for k in ('image','output','prompt','source_sha256')):
        raise ValueError('Missing image, output, description or digest')
    if not re.fullmatch(r'[0-9a-f]{64}',s['source_sha256']) or s['image'].casefold()==s['output'].casefold():
        raise ValueError('Invalid source digest or output')
    if not s['prompt'].strip() or len(s['prompt'])>2000 or any(ord(c)<32 and c not in '\n\t' for c in s['prompt']):
        raise ValueError('Use a bounded image prompt')
    for k,lo,hi in (('steps',10,20),('strength_percent',30,90),('seed',0,4294967295)):
        if type(s[k]) is not int or not lo<=s[k]<=hi:raise ValueError('Invalid generation parameter: '+k)
    if type(s['size']) is not int or s['size'] not in (256,384,512):
        raise ValueError('Invalid generation size')
    if 'reference' in s:
        if not isinstance(s['reference'],str) or not s['reference'] or s['reference'].casefold() in (s['image'].casefold(),s['output'].casefold()):
            raise ValueError('Use a distinct palette reference')
        if not isinstance(s['reference_sha256'],str) or not re.fullmatch(r'[0-9a-f]{64}',s['reference_sha256']):
            raise ValueError('Invalid reference digest')
        if type(s['palette_strength_percent']) is not int or not 1<=s['palette_strength_percent']<=100:
            raise ValueError('Invalid palette strength')
    if 'mask' in s:
        if not isinstance(s['mask'],str) or not s['mask'] or s['mask'].casefold() in (s['image'].casefold(),s['output'].casefold()):
            raise ValueError('Use a distinct binary mask')
        if not isinstance(s['mask_sha256'],str) or not re.fullmatch(r'[0-9a-f]{64}',s['mask_sha256']):
            raise ValueError('Invalid mask digest')
    if 'character_name' in s:
        name=s['character_name']
        if not isinstance(name,str) or not 1<=len(name)<=100 or not name.strip() or any(ord(c)<32 for c in name):
            raise ValueError('Use a bounded character label')
        if not isinstance(s['character_region_sha256'],str) or not re.fullmatch(r'[0-9a-f]{64}',s['character_region_sha256']):
            raise ValueError('Invalid character region digest')
    if 'offset_x' in s:
        for k in ('offset_x','offset_y'):
            if type(s[k]) is not int or not 0<=s[k]<s['size']:raise ValueError('Invalid source offset')
    if 'operation' in s:
        if s['operation'] not in ('remove_object','replace_object') or ('replacement_object' in s)!=(s['operation']=='replace_object'):
            raise ValueError('Unsupported object operation or mismatched fields')
        target=s['removed_object']
        if not isinstance(target,str) or not target.strip() or len(target)>200 or any(ord(c)<32 for c in target):
            raise ValueError('Describe the unwanted object in 1–200 characters')
        if s['operation']=='replace_object':
            replacement=s['replacement_object']
            if not isinstance(replacement,str) or not replacement.strip() or len(replacement)>300 or any(ord(c)<32 for c in replacement):
                raise ValueError('Describe the replacement object in 1–300 characters')
            if ' '.join(target.casefold().split())==' '.join(replacement.casefold().split()):raise ValueError('Replacement must differ from unwanted object')
            if len(positive_prompt(s))>2000:raise ValueError('Combined replacement prompt exceeds bound')
    if 'guide_kind' in s:
        if s['guide_kind']=='pose' and set(s)==FIELDS|POSE_FIELDS:
            if s['guide_layout']!='joint-map-v1':raise ValueError('Invalid pose layout')
        elif s['guide_kind']=='depth' and set(s)==FIELDS|DEPTH_FIELDS:
            if s['guide_layout']!='relative-depth-relief-v1' or type(s['near_is_white']) is not bool or type(s['relief_percent']) is not int or not 0<=s['relief_percent']<=100:
                raise ValueError('Invalid relative-depth guidance settings')
        elif s['guide_kind']=='sketch' and set(s)==FIELDS|SKETCH_FIELDS:
            if s['guide_layout']!='sketch-fit-v1' or type(s['light_background']) is not bool or type(s['line_strength_percent']) is not int or not 10<=s['line_strength_percent']<=100:
                raise ValueError('Invalid sketch guidance settings')
        else:raise ValueError('Unsupported structural guide or mismatched fields')
    return s

POSE_JOINTS=('head','neck','left_shoulder','right_shoulder','left_elbow','right_elbow','left_wrist','right_wrist',
             'left_hip','right_hip','left_knee','right_knee','left_ankle','right_ankle')
POSE_LINKS=(('head','neck'),('neck','left_shoulder'),('neck','right_shoulder'),
            ('left_shoulder','left_elbow'),('left_elbow','left_wrist'),('right_shoulder','right_elbow'),('right_elbow','right_wrist'),
            ('left_shoulder','left_hip'),('right_shoulder','right_hip'),('left_hip','right_hip'),
            ('left_hip','left_knee'),('left_knee','left_ankle'),('right_hip','right_knee'),('right_knee','right_ankle'))

def pose_guide(raw,size):
    """Rasterize an explicit human joint layout; not automatic pose detection."""
    from deepthort_local.structured_source import strict_json
    if len(raw)>16000:raise ValueError('Pose guide exceeds 16 KB')
    spec=strict_json(raw.decode('utf-8'))
    if not isinstance(spec,dict) or set(spec)!={'joints'} or not isinstance(spec['joints'],dict) or set(spec['joints'])!=set(POSE_JOINTS):
        raise ValueError('Expected one complete named 14-joint pose')
    coords={}
    for name,value in spec['joints'].items():
        if not isinstance(value,list) or len(value)!=2 or any(type(v) is not int or not 0<=v<=1000 for v in value):
            raise ValueError('Joint coordinates must be integer thousandths of the canvas')
        coords[name]=tuple(round(v*(size-1)/1000) for v in value)
    if len(set(coords.values()))!=len(coords) or any(sum((coords[a][i]-coords[b][i])**2 for i in (0,1))<4 for a,b in POSE_LINKS):
        raise ValueError('Pose contains collapsed joints or limbs')
    Image=image_module()
    from PIL import ImageDraw
    with Image.new('RGB',(size,size),(224,224,224)) as im:
        draw=ImageDraw.Draw(im)
        torso=[coords[k] for k in ('left_shoulder','right_shoulder','right_hip','left_hip')]
        draw.polygon(torso,fill=(112,112,112))
        for a,b in POSE_LINKS:draw.line((coords[a],coords[b]),fill=(105,105,105),width=max(4,size//23))
        radius=max(2,size//54)
        for x,y in coords.values():draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=(78,78,78))
        x,y=coords['head'];r=max(6,size//21)
        draw.ellipse((x-r,y-r,x+r,y+r),fill=(105,105,105))
        return encode(size,size,'RGB',im.tobytes())

def review_pose(root,image,output,prompt,size=384,steps=15,strength_percent=60,seed=0):
    root=Path(root).resolve(strict=True)
    source=guard.path_for(root,image,exclusions(()),{'.json'},exists=True)
    if source.stat().st_size>16000:raise ValueError('Pose guide exceeds 16 KB')
    s={'schema':SCHEMA,'image':image,'source_sha256':snapshot_file(source)['expected'],'output':output,
       'prompt':prompt,'size':size,'steps':steps,'strength_percent':strength_percent,'seed':seed,
       'guide_kind':'pose','guide_layout':'joint-map-v1'}
    src,_,bound=validate(root,s)
    pose_guide(guard.exact(src,bound,16000),size)
    return s

def depth_guide(raw,size,near_is_white,relief_percent):
    """Render relative depth into a deterministic shaded initialization.

    Depth is relative, not metres. Preserve the supplied geometry and use
    simple finite differences for an optional upper-left lighting cue.
    """
    w,h,_,pixels=decode(raw,('L',))
    if (w,h)!=(size,size):raise ValueError('Use a square grayscale depth PNG matching the output size')
    if max(pixels)-min(pixels)<8:raise ValueError('Depth guide has insufficient variation')
    depth=pixels if near_is_white else bytes(255-v for v in pixels)
    out=bytearray(size*size*3)
    for y in range(size):
        for x in range(size):
            i=y*size+x
            dx=depth[y*size+min(size-1,x+1)]-depth[y*size+max(0,x-1)]
            dy=depth[min(size-1,y+1)*size+x]-depth[max(0,y-1)*size+x]
            shade=max(0,min(255,128+dx+dy))
            base=32+depth[i]*191//255
            tone=(base*(100-relief_percent)+shade*relief_percent+50)//100
            out[i*3:i*3+3]=bytes([tone])*3
    return encode(size,size,'RGB',bytes(out))

def review_depth(root,image,output,prompt,size=384,steps=15,strength_percent=60,seed=0,near_is_white=True,relief_percent=35):
    root=Path(root).resolve(strict=True)
    source=guard.path_for(root,image,exclusions(()),{'.png'},exists=True)
    if source.stat().st_size>guard.MAX_INPUT:raise ValueError('Depth guide exceeds input bound')
    s={'schema':SCHEMA,'image':image,'source_sha256':snapshot_file(source)['expected'],'output':output,
       'prompt':prompt,'size':size,'steps':steps,'strength_percent':strength_percent,'seed':seed,
       'guide_kind':'depth','guide_layout':'relative-depth-relief-v1','near_is_white':near_is_white,'relief_percent':relief_percent}
    src,_,bound=validate(root,s)
    depth_guide(guard.exact(src,bound,guard.MAX_INPUT),size,near_is_white,relief_percent)
    return s

def sketch_guide(raw,size,light_background,line_strength_percent):
    """Normalize line-art contrast and fit the guide without stretching."""
    w,h,mode,pixels=decode(raw,('L','RGB'))
    if w*h>1024*1024:raise ValueError('Sketch exceeds one megapixel')
    Image=image_module()
    from PIL import ImageOps
    with Image.frombytes(mode,(w,h),pixels) as src,src.convert('L') as mono:
        with ImageOps.autocontrast(mono) as contrast:
            if contrast.getextrema()[1]-contrast.getextrema()[0]<8:raise ValueError('Sketch has insufficient contrast')
            with (contrast.copy() if light_background else ImageOps.invert(contrast)) as ink:
                lut=[255-(255-v)*line_strength_percent//100 for v in range(256)]
                with ink.point(lut) as toned:
                    with ImageOps.contain(toned,(size,size),Image.Resampling.LANCZOS) as fit:
                        with Image.new('L',(size,size),255) as canvas:
                            canvas.paste(fit,((size-fit.width)//2,(size-fit.height)//2))
                            with canvas.convert('RGB') as rgb:return encode(size,size,'RGB',rgb.tobytes())

def review_sketch(root,image,output,prompt,size=384,steps=15,strength_percent=65,seed=0,light_background=True,line_strength_percent=100):
    root=Path(root).resolve(strict=True)
    source=guard.path_for(root,image,exclusions(()),{'.png'},exists=True)
    if source.stat().st_size>guard.MAX_INPUT:raise ValueError('Sketch exceeds input bound')
    s={'schema':SCHEMA,'image':image,'source_sha256':snapshot_file(source)['expected'],'output':output,
       'prompt':prompt,'size':size,'steps':steps,'strength_percent':strength_percent,'seed':seed,
       'guide_kind':'sketch','guide_layout':'sketch-fit-v1','light_background':light_background,'line_strength_percent':line_strength_percent}
    src,_,bound=validate(root,s)
    sketch_guide(guard.exact(src,bound,guard.MAX_INPUT),size,light_background,line_strength_percent)
    return s

def positive_prompt(s):
    if s.get('operation')=='replace_object':
        return s['replacement_object'].strip()+', '+s['prompt'].strip()+', integrated into the surrounding scene'
    return s['prompt']

def removal_init(raw,mask_raw,s):
    """Discard original masked object pixels before diffusion.

    Deterministic four-neighbour propagation from the unmasked boundary;
    initialization is not an assertion of background reconstruction.
    """
    from collections import deque
    w,h,pixels,mask=mask_pixels(raw,mask_raw,s)
    if mask.count(255)>w*h*3//4:raise ValueError('Object removal needs at least one-quarter unmasked context')
    out=bytearray(pixels);seen=bytearray(1 if v==0 else 0 for v in mask)
    queue=deque(i for i,v in enumerate(mask) if not v)
    while queue:
        i=queue.popleft();x=i%w;y=i//w
        for j in (i-1 if x else -1,i+1 if x+1<w else -1,i-w if y else -1,i+w if y+1<h else -1):
            if j<0 or seen[j]:continue
            seen[j]=1;out[3*j:3*j+3]=out[3*i:3*i+3];queue.append(j)
    if not all(seen):raise ValueError('Incomplete initialization')
    return encode(w,h,'RGB',bytes(out))

def review_removal(root,image,mask,output,background,removed_object,size=384,steps=15,strength_percent=90,seed=0):
    s=review_mask(root,image,mask,output,background,size,steps,strength_percent,seed)
    s.update(operation='remove_object',removed_object=removed_object)
    src,_,bound=validate(root,s);mp,mb=mask_input(root,s,src)
    removal_init(guard.exact(src,bound,guard.MAX_INPUT),guard.exact(mp,mb,guard.MAX_INPUT),s)
    return s

def review_replacement(root,image,mask,output,context,removed_object,replacement_object,size=384,steps=15,strength_percent=90,seed=0):
    s=review_mask(root,image,mask,output,context,size,steps,strength_percent,seed)
    s.update(operation='replace_object',removed_object=removed_object,replacement_object=replacement_object)
    src,_,bound=validate(root,s);mp,mb=mask_input(root,s,src)
    removal_init(guard.exact(src,bound,guard.MAX_INPUT),guard.exact(mp,mb,guard.MAX_INPUT),s)
    return s

def outpaint_inputs(raw,s):
    w,h,_,pixels=decode(raw,('RGB',));size=s['size'];x,y=s['offset_x'],s['offset_y']
    if x+w>size or y+h>size or w*h==size*size:
        raise ValueError('Source must fit inside a strictly larger canvas')
    # Use clamped edge colours as the initial context, not as generated output.
    data=bytearray(size*size*3);mask=bytearray([255])*(size*size)
    for cy in range(size):
        sy=min(h-1,max(0,cy-y))
        for cx in range(size):
            sx=min(w-1,max(0,cx-x));i=cy*size+cx;j=sy*w+sx
            data[i*3:i*3+3]=pixels[j*3:j*3+3]
        if y<=cy<y+h:mask[cy*size+x:cy*size+x+w]=bytes(w)
    return encode(size,size,'RGB',bytes(data)),encode(size,size,'L',bytes(mask))

def review_outpaint(root,image,output,prompt,size,offset_x,offset_y,steps=15,strength_percent=90,seed=0):
    s=review(root,image,output,prompt,size,steps,strength_percent,seed)
    s.update(offset_x=offset_x,offset_y=offset_y)
    src,_,bound=validate(root,s)
    outpaint_inputs(guard.exact(src,bound,guard.MAX_INPUT),s)
    return s

def mask_input(root,s,source):
    if 'mask' not in s:return None,None
    path=guard.path_for(Path(root).resolve(strict=True),s['mask'],exclusions(()),{'.png'},exists=True)
    if path.samefile(source) or path.stat().st_size+source.stat().st_size>guard.MAX_INPUT:
        raise ValueError('Duplicate or oversized mask inputs')
    bound=snapshot_file(path)
    if bound['expected']!=s['mask_sha256']:raise ValueError('Reviewed mask changed')
    return path,bound

def mask_pixels(raw,mask_raw,s):
    w,h,_,pixels=decode(raw,('RGB',))
    mw,mh,_,mask=decode(mask_raw,('L',))
    if (w,h)!=(s['size'],s['size']) or (mw,mh)!=(w,h):
        raise ValueError('Inpainting requires same-size square source and mask, 256/384/512')
    if any(v not in (0,255) for v in mask) or not any(mask) or all(mask):
        raise ValueError('Mask must select a nonempty proper region, white on black')
    return w,h,pixels,mask

def review_mask(root,image,mask,output,prompt,size=384,steps=15,strength_percent=80,seed=0):
    s=review(root,image,output,prompt,size,steps,strength_percent,seed)
    root=Path(root).resolve(strict=True)
    path=guard.path_for(root,mask,exclusions(()),{'.png'},exists=True)
    if path.stat().st_size>guard.MAX_INPUT:raise ValueError('Mask exceeds input bound')
    s.update(mask=mask,mask_sha256=snapshot_file(path)['expected'])
    source,_,bound=validate(root,s);path,mb=mask_input(root,s,source)
    mask_pixels(guard.exact(source,bound,guard.MAX_INPUT),guard.exact(path,mb,guard.MAX_INPUT),s)
    return s

def character_digest(raw,mask_raw,s):
    """Bind the owner-selected unchanged character pixels and their positions."""
    w,h,pixels,mask=mask_pixels(raw,mask_raw,s)
    if mask.count(0)<w*h//20 or mask.count(255)<w*h//20:
        raise ValueError('Both protected character and editable scene need at least 5% of the canvas')
    identity=hashlib.sha256()
    identity.update(str(w).encode()+b'x'+str(h).encode()+b'\0'+mask)
    identity.update(b''.join(pixels[i:i+3] for i in range(0,len(pixels),3) if not mask[i//3]))
    return identity.hexdigest()

def review_character(root,image,mask,output,scene,name,size=384,steps=15,strength_percent=80,seed=0):
    s=review_mask(root,image,mask,output,scene,size,steps,strength_percent,seed)
    src,_,bound=validate(root,s);mp,mb=mask_input(root,s,src)
    s.update(character_name=name,character_region_sha256=character_digest(
        guard.exact(src,bound,guard.MAX_INPUT),guard.exact(mp,mb,guard.MAX_INPUT),s))
    checked(s)
    return s

def reference_input(root,s,source,bound):
    if 'reference' not in s:return None,None
    path=guard.path_for(Path(root).resolve(strict=True),s['reference'],exclusions(()),{'.png'},exists=True)
    if path.samefile(source) or path.stat().st_size+source.stat().st_size>guard.MAX_INPUT:
        raise ValueError('Duplicate or oversized reference inputs')
    ref=snapshot_file(path)
    if ref['expected']!=s['reference_sha256']:raise ValueError('Reviewed reference changed')
    return path,ref

def validate(root,s):
    checked(s);root=Path(root).resolve(strict=True);exclude=exclusions(())
    source=guard.path_for(root,s['image'],exclude,{'.json'} if s.get('guide_kind')=='pose' else {'.png'},exists=True)
    dst=guard.path_for(root,s['output'],exclude,{'.png'},exists=False)
    if source.stat().st_size>guard.MAX_INPUT:raise ValueError('Image exceeds input bound')
    bound=snapshot_file(source)
    if bound['expected']!=s['source_sha256']:raise ValueError('Reviewed image changed')
    reference_input(root,s,source,bound)
    mask_input(root,s,source)
    return source,dst,bound

def review(root,image,output,prompt,size=384,steps=15,strength_percent=60,seed=0):
    root=Path(root).resolve(strict=True)
    src=guard.path_for(root,image,exclusions(()),{'.png'},exists=True)
    if src.stat().st_size>guard.MAX_INPUT:raise ValueError('Image exceeds input bound')
    s={'schema':SCHEMA,'image':image,'output':output,'prompt':prompt,'size':size,'steps':steps,
       'strength_percent':strength_percent,'seed':seed,'source_sha256':snapshot_file(src)['expected']}
    src,_,bound=validate(root,s)
    decode(guard.exact(src,bound,guard.MAX_INPUT),('RGB',))
    return s

def review_reference(root,image,reference,output,prompt,size=384,steps=15,strength_percent=60,seed=0,palette_strength_percent=80):
    s=review(root,image,output,prompt,size,steps,strength_percent,seed)
    path=guard.path_for(Path(root).resolve(strict=True),reference,exclusions(()),{'.png'},exists=True)
    if path.stat().st_size>guard.MAX_INPUT:raise ValueError('Reference exceeds input bound')
    s.update(reference=reference,reference_sha256=snapshot_file(path)['expected'],palette_strength_percent=palette_strength_percent)
    source,_,bound=validate(root,s)
    path,ref=reference_input(root,s,source,bound)
    # Check the same decoding and palette transform used during generation.
    guide(guard.exact(source,bound,guard.MAX_INPUT),guard.exact(path,ref,guard.MAX_INPUT),s)
    return s

def guide(raw,reference,s):
    from deepthort_local.image_style_transfer import generate
    return generate(raw,reference,{'image':s['image'],'reference':s['reference'],
                    'strength_percent':s['palette_strength_percent']})[0]

def diffuse(model,raw,s):
    model=Path(model).resolve(strict=True)
    if not (model/'model_index.json').is_file():raise RuntimeError('Existing optional diffusion model is not installed')
    for key in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','DIFFUSERS_OFFLINE','OMP_NUM_THREADS','MKL_NUM_THREADS'):
        os.environ[key]='1'
    import torch
    from diffusers import StableDiffusionImg2ImgPipeline
    torch.set_num_threads(1)
    w,h,mode,pixels=decode(raw,('RGB',));Image=image_module();size=s['size']
    with Image.frombytes(mode,(w,h),pixels) as source:
        with source.resize((size,size),Image.Resampling.LANCZOS) as init:
            pipe=StableDiffusionImg2ImgPipeline.from_pretrained(str(model),local_files_only=True,
                use_safetensors=True,safety_checker=None,requires_safety_checker=False,torch_dtype=torch.float32)
            pipe=pipe.to('cpu');pipe.enable_attention_slicing('max')
            gen=torch.Generator(device='cpu').manual_seed(s['seed'])
            result=pipe(prompt=s['prompt'],image=init,strength=s['strength_percent']/100,
                        num_inference_steps=s['steps'],generator=gen).images
            if len(result)!=1:raise ValueError('Expected exactly one generated image')
            with result[0] as im:
                if im.size!=(size,size) or im.mode!='RGB':raise ValueError('Unexpected generated image layout')
                return encode(size,size,'RGB',im.tobytes())

def diffuse_mask(model,raw,mask_raw,s):
    model=Path(model).resolve(strict=True)
    if not (model/'model_index.json').is_file():raise RuntimeError('Existing optional diffusion model is not installed')
    for key in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','DIFFUSERS_OFFLINE','OMP_NUM_THREADS','MKL_NUM_THREADS'):
        os.environ[key]='1'
    import torch
    from diffusers import StableDiffusionInpaintPipeline
    torch.set_num_threads(1)
    w,h,pixels,mask=mask_pixels(raw,mask_raw,s);Image=image_module()
    pipe=StableDiffusionInpaintPipeline.from_pretrained(str(model),local_files_only=True,
        use_safetensors=True,safety_checker=None,requires_safety_checker=False,torch_dtype=torch.float32)
    pipe=pipe.to('cpu');pipe.enable_attention_slicing('max')
    if pipe.unet.config.in_channels not in (4,9):raise ValueError('Unsupported local inpainting UNet')
    with Image.frombytes('RGB',(w,h),pixels) as source, Image.frombytes('L',(w,h),mask) as selection:
        gen=torch.Generator(device='cpu').manual_seed(s['seed'])
        guidance={'negative_prompt':s['removed_object']} if s.get('operation') in ('remove_object','replace_object') else {}
        result=pipe(prompt=positive_prompt(s),image=source,mask_image=selection,width=w,height=h,
            strength=s['strength_percent']/100,num_inference_steps=s['steps'],generator=gen,**guidance).images
        if len(result)!=1:raise ValueError('Expected exactly one generated image')
        with result[0] as im:
            if im.size!=(w,h) or im.mode!='RGB':raise ValueError('Unexpected generated image layout')
            return encode(w,h,'RGB',im.tobytes())

def execute(root,model,s,*,backend=diffuse,mask_backend=diffuse_mask):
    src,dst,bound=validate(root,s)
    raw=guard.exact(src,bound,guard.MAX_INPUT)
    pose=s.get('guide_kind')=='pose';depth=s.get('guide_kind')=='depth';sketch=s.get('guide_kind')=='sketch'
    raster=pose_guide(raw,s['size']) if pose else (depth_guide(raw,s['size'],s['near_is_white'],s['relief_percent']) if depth else (sketch_guide(raw,s['size'],s['light_background'],s['line_strength_percent']) if sketch else raw))
    w,h,_,_=decode(raster,('RGB',))
    ref_path,ref_bound=reference_input(root,s,src,bound)
    initial=guide(raw,guard.exact(ref_path,ref_bound,guard.MAX_INPUT),s) if ref_path else raster
    mask_path,mask_bound=mask_input(root,s,src)
    mask=None
    expanded='offset_x' in s
    if expanded:
        initial,mr=outpaint_inputs(raw,s)
        _,_,original,mask=mask_pixels(initial,mr,s)
        out=mask_backend(model,initial,mr,s)
    elif mask_path:
        mr=guard.exact(mask_path,mask_bound,guard.MAX_INPUT)
        _,_,original,mask=mask_pixels(raw,mr,s)
        if 'character_name' in s and character_digest(raw,mr,s)!=s['character_region_sha256']:
            raise ValueError('Reviewed character region changed')
        initial=removal_init(raw,mr,s) if s.get('operation') in ('remove_object','replace_object') else raw
        out=mask_backend(model,initial,mr,s)
    else:out=backend(model,initial,s)
    if not isinstance(out,bytes) or len(out)>guard.MAX_OUTPUT:raise ValueError('Invalid generated PNG')
    ow,oh,_,pixels=decode(out,('RGB',))
    if (ow,oh)!=(s['size'],s['size']):raise ValueError('Generated dimensions differ from approved size')
    if mask is not None:
        # Diffusion can alter the entire latent image. Copy exact original RGB
        # outside the approved region, regardless of backend behaviour.
        pixels=b''.join(pixels[i:i+3] if mask[i//3] else original[i:i+3] for i in range(0,len(original),3))
        out=encode(ow,oh,'RGB',pixels)
        if any(pixels[i:i+3]!=original[i:i+3] for i in range(0,len(original),3) if not mask[i//3]):
            raise ValueError('Unmasked pixels changed')
    def revalidate():
        current,target,current_bound=validate(root,s)
        if (current,target,current_bound)!=(src,dst,bound):raise ValueError('Reviewed paths changed')
        if reference_input(root,s,current,current_bound)!=(ref_path,ref_bound):raise ValueError('Reviewed reference changed')
        if mask_input(root,s,current)!=(mask_path,mask_bound):raise ValueError('Reviewed mask changed')
    if s.get('operation') in ('remove_object','replace_object') and pixels==original:
        raise ValueError('Object edit produced no pixel change')
    if 'character_name' in s:
        if pixels==original:raise ValueError('Scene generation produced no pixel change')
        if character_digest(out,mr,s)!=s['character_region_sha256']:
            raise ValueError('Protected character pixels differ')
    sha=guard.publish(out,dst,revalidate)
    return {'schema':'janus-image-to-image-result-v1','status':'generated_image_pixels_verified',
            'output':s['output'],'sha256':sha,'source_sha256':s['source_sha256'],
            'pixel_sha256':hashlib.sha256(pixels).hexdigest(),'source_dimensions':[w,h],
            'dimensions':[ow,oh],'seed':s['seed'],'strength_percent':s['strength_percent'],
            'source_unchanged':True,'visual_quality_verified':False,
            **({'reference_sha256':s['reference_sha256'],'palette_strength_percent':s['palette_strength_percent'],
                'conditioning_sha256':hashlib.sha256(initial).hexdigest(),'reference_method':'classical_palette_initialisation',
                'semantic_reference_conditioning':False} if ref_path else {}),
            **({'mask_sha256':hashlib.sha256(mr).hexdigest(),'masked_pixels':sum(v==255 for v in mask),
                'unmasked_pixels_preserved':True,'inpainting_backend':'local_diffusion'} if mask is not None else {}),
            **({'character_name':s['character_name'],'character_region_sha256':s['character_region_sha256'],
                'same_reference_pixels_verified':True,'semantic_character_identity_verified':False,
                'new_pose_generated':False,'scene_variation_only':True} if 'character_name' in s else {}),
            **({'outpainting':True,'source_offset':[s['offset_x'],s['offset_y']],
                'source_pixels_preserved':True,'initial_canvas_sha256':hashlib.sha256(initial).hexdigest()} if expanded else {}),
            **({'operation':'remove_object','removed_object':s['removed_object'],
                'initialisation_sha256':hashlib.sha256(initial).hexdigest(),
                'object_absence_verified':False,'original_masked_pixels_discarded_before_diffusion':True} if s.get('operation')=='remove_object' else {}),
            **({'operation':'replace_object','removed_object':s['removed_object'],'replacement_object':s['replacement_object'],
                'positive_prompt_sha256':hashlib.sha256(positive_prompt(s).encode()).hexdigest(),
                'initialisation_sha256':hashlib.sha256(initial).hexdigest(),'replacement_identity_verified':False,
                'original_masked_pixels_discarded_before_diffusion':True} if s.get('operation')=='replace_object' else {}),
            **({'guide_kind':'pose','guide_layout':s['guide_layout'],'guide_raster_sha256':hashlib.sha256(raster).hexdigest(),
                'pose_conditioning':'joint_raster_initialisation','pose_fidelity_verified':False,'controlnet_used':False} if pose else {}),
            **({'guide_kind':'depth','guide_layout':s['guide_layout'],'guide_raster_sha256':hashlib.sha256(raster).hexdigest(),
                'near_is_white':s['near_is_white'],'relief_percent':s['relief_percent'],
                'depth_conditioning':'relative_depth_raster_initialisation','depth_fidelity_verified':False,'controlnet_used':False} if depth else {}),
            **({'guide_kind':'sketch','guide_layout':s['guide_layout'],'guide_raster_sha256':hashlib.sha256(raster).hexdigest(),
                'line_strength_percent':s['line_strength_percent'],'aspect_preserving_fit':True,
                'sketch_fidelity_verified':False,'controlnet_used':False} if sketch else {})}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--model',required=True)
    p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        result=execute(a.root,a.model,json.loads(a.plan))
        print('IMAGE_TO_IMAGE_RESULT: '+json.dumps(result,sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,
            'reason':'Reviewed image-to-image generation failed; verify the local model, resource headroom and input'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
