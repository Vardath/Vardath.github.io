"""Reviewed pixel-art game sprite sheets, explicit palettes and animation metadata."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.texture_pixels import image_module

SCHEMA='janus-game-sprite-atlas-v1'
def name(s):return isinstance(s,str) and re.fullmatch(r'[a-z][a-z0-9_]{0,47}',s) is not None

def checked(s):
    if not isinstance(s,dict) or set(s)!={'size','palette','sprites','animations'} or type(s['size']) is not int or s['size'] not in (8,16,24,32):
        raise ValueError('Choose an 8/16/24/32 pixel tile and explicit sprite frames')
    p=s['palette']
    if not isinstance(p,dict) or not 1<=len(p)<=16 or any(not isinstance(k,str) or not re.fullmatch(r'[A-Za-z0-9]',k) or not isinstance(v,list) or len(v)!=4 or any(type(n) is not int or not 0<=n<=255 for n in v) or v[3]==0 for k,v in p.items()):
        raise ValueError('Palette needs 1–16 visible RGBA symbols; dot is transparent')
    sprites=s['sprites'];n=s['size']
    if not isinstance(sprites,list) or not 1<=len(sprites)<=32:raise ValueError('Choose 1–32 sprite frames')
    names=set()
    for item in sprites:
        if not isinstance(item,dict) or set(item)!={'name','rows','pivot'} or not name(item['name']) or item['name'] in names:
            raise ValueError('Duplicate or invalid sprite name')
        names.add(item['name']);rows=item['rows'];pivot=item['pivot']
        if not isinstance(rows,list) or len(rows)!=n or any(not isinstance(row,str) or len(row)!=n or any(c not in p and c!='.' for c in row) for row in rows) or all(c=='.' for row in rows for c in row):
            raise ValueError('Every sprite requires exact pixel rows and visible content')
        if not isinstance(pivot,list) or len(pivot)!=2 or any(type(x) is not int or not 0<=x<n for x in pivot):raise ValueError('Invalid sprite pivot')
    animations=s['animations']
    if not isinstance(animations,list) or len(animations)>16:raise ValueError('At most 16 animation definitions')
    anames=set()
    for a in animations:
        if not isinstance(a,dict) or set(a)!={'name','frames','fps','loop'} or not name(a['name']) or a['name'] in anames or type(a['fps']) is not int or not 1<=a['fps']<=30 or type(a['loop']) is not bool:
            raise ValueError('Invalid animation metadata')
        anames.add(a['name'])
        if not isinstance(a['frames'],list) or not 1<=len(a['frames'])<=32 or any(not isinstance(x,str) or x not in names for x in a['frames']):
            raise ValueError('Animation must refer to existing named frames')
    return s

def generate(s):
    checked(s);Image=image_module();n=s['size'];cols=min(8,len(s['sprites']));rows=(len(s['sprites'])+cols-1)//cols
    w,h=cols*n,rows*n;pixels=bytearray(w*h*4);records={}
    for i,item in enumerate(s['sprites']):
        x,y=(i%cols)*n,(i//cols)*n
        for j,row in enumerate(item['rows']):
            for k,c in enumerate(row):
                at=((y+j)*w+x+k)*4
                pixels[at:at+4]=bytes(s['palette'][c]) if c!='.' else b'\0\0\0\0'
        records[item['name']]={'rect':[x,y,n,n],'pivot':item['pivot']}
    stream=io.BytesIO()
    with Image.frombytes('RGBA',(w,h),bytes(pixels)) as im:im.save(stream,format='PNG',compress_level=6)
    png=stream.getvalue()
    with Image.open(io.BytesIO(png),formats=['PNG']) as im:
        im.load()
        if im.mode!='RGBA' or im.size!=(w,h) or im.tobytes()!=pixels:raise ValueError('Atlas pixel roundtrip failed')
    metadata={'schema':'janus-sprite-atlas-v1','image':'atlas.png','size':[w,h],'tile_size':n,
        'sprites':records,'animations':s['animations'],'filter_hint':'nearest'}
    entries={'atlas.png':png,'atlas.json':(json.dumps(metadata,sort_keys=True,indent=2)+'\n').encode('utf-8'),
        'source.json':(json.dumps(s,sort_keys=True,indent=2)+'\n').encode('utf-8')}
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:
        for k,v in sorted(entries.items()):
            info=zipfile.ZipInfo(k,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,v)
    payload=stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or sorted(z.namelist())!=sorted(entries) or any(z.read(k)!=v for k,v in entries.items()):raise ValueError('Atlas archive roundtrip failed')
    return payload,{'width':w,'height':h,'sprites':len(records),'animations':len(s['animations']),
        'pixel_sha256':hashlib.sha256(pixels).hexdigest(),'pixel_roundtrip_verified':True,
        'engine_import_verified':False,'neural_generation_used':False,'visual_quality_verified':False}

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.zip')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip')
    return plan,dict(s,scope='Explicit pixel-art sprite frames, transparent RGBA atlas, animation and pivot metadata. No engine import.')
def execute(root,plan):
    s,dst,_=validate(root,plan);payload,r=generate(s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-game-sprite-atlas-result-v1','status':'sprite_atlas_pixels_verified','output':plan['output'],
        'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed pixel-art atlas or output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
