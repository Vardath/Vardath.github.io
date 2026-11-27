"""Explicit one-shot Windows primary-screen region capture and exact snapshot handoff."""
import hashlib
import os
import re
from pathlib import Path
from . import typed_project_tool as guard
from .texture_pixels import encode,decode
from .source_security import exclusions

PREFIX='Reviewed screen snapshot SHA256: '
MAX_PIXELS=2048*1024

def region(values,screen):
    if not isinstance(values,(tuple,list)) or len(values)!=4 or any(type(n) is not int for n in values):
        raise ValueError('Specify integer x, y, width, height')
    x,y,w,h=values
    if not 0<=x or not 0<=y or not 1<=w<=2048 or not 1<=h<=2048 or w*h>MAX_PIXELS or x+w>screen[0] or y+h>screen[1]:
        raise ValueError('Choose a bounded region within the primary monitor')
    return x,y,w,h

def primary_size():
    if os.name!='nt':raise RuntimeError('Windows screen capture required')
    import ctypes
    from .triad_job import verify_root_cap
    verify_root_cap()
    size=(ctypes.windll.user32.GetSystemMetrics(0),ctypes.windll.user32.GetSystemMetrics(1))
    if not 1<=size[0]<=8192 or not 1<=size[1]<=8192 or size[0]*size[1]>16*1024*1024:
        raise ValueError('Primary monitor exceeds capture bounds')
    return size

def native_capture(box):
    from PIL import ImageGrab
    if os.name!='nt':raise RuntimeError('Windows capture required')
    x,y,w,h=region(box,primary_size())
    with ImageGrab.grab(bbox=(x,y,x+w,y+h),include_layered_windows=False,all_screens=False) as im:
        if im.size!=(w,h):raise ValueError('Captured size differs; inspect display scaling')
        with im.convert('RGB') as rgb:return rgb.tobytes()

def capture(box,screen,*,approved=False,backend=native_capture):
    if approved is not True:raise PermissionError('Explicit screenshot approval required')
    x,y,w,h=region(box,screen)
    data=backend((x,y,w,h))
    if not isinstance(data,bytes) or len(data)!=w*h*3:raise ValueError('Incomplete screenshot pixels')
    return encode(w,h,'RGB',data)

def save(root,relative,excluded,payload,*,approved=False):
    if approved is not True:raise PermissionError('Explicit screenshot save approval required')
    root=Path(root).resolve(strict=True);excluded=exclusions(excluded)
    if not isinstance(payload,bytes) or len(payload)>guard.MAX_OUTPUT:raise ValueError('Screenshot exceeds byte bound')
    w,h,_,_=decode(payload,('RGB',))
    if w*h>MAX_PIXELS:raise ValueError('Screenshot exceeds pixel bound')
    def target():return guard.path_for(root,relative,excluded,{'.png'},exists=False)
    sha=guard.publish(payload,target(),target)
    return {'output':relative,'sha256':sha,'width':w,'height':h,'interpreted':False}

def prompt_for(sha):
    if not isinstance(sha,str) or not re.fullmatch(r'[0-9a-f]{64}',sha):raise ValueError('Invalid snapshot identity')
    return PREFIX+sha

def exact_snapshot(root,path,prompt):
    if not isinstance(prompt,str) or not prompt.startswith(PREFIX):raise ValueError('Missing reviewed snapshot identity')
    sha=prompt[len(PREFIX):]
    if prompt_for(sha)!=prompt:raise ValueError('Invalid snapshot prompt')
    root=Path(root).resolve(strict=True);path=Path(path)
    relative=path.relative_to(root).as_posix()
    src=guard.path_for(root,relative,[],{'.png'},exists=True)
    raw=guard.read_bound(src,guard.MAX_INPUT)
    if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Reviewed screen snapshot changed')
    w,h,_,_=decode(raw,('RGB',))
    if w*h>MAX_PIXELS:raise ValueError('Screen snapshot exceeds pixel bound')
    return raw
