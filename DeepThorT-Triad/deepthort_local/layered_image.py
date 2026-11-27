"""Reviewed editable OpenRaster document with independent raster layers."""
from __future__ import annotations
import argparse,hashlib,io,json,sys,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file
from deepthort_local.image_composition import checked as check_composition,decode_layer,compose
from deepthort_local.texture_pixels import image_module

SCHEMA='janus-layered-image-v1'
MIME=b'image/openraster'

def checked(s):
    if not isinstance(s,dict) or set(s)!={'width','height','background','layers'}:raise ValueError('Expected ordered editable layers')
    if not isinstance(s['layers'],list):raise ValueError('Expected layer list')
    names=set()
    for layer in s['layers']:
        if not isinstance(layer,dict) or set(layer)!={'name','image','x','y','width','height','opacity','visible'}:
            raise ValueError('Each layer needs name, image, geometry, opacity and visibility')
        n=layer['name']
        if not isinstance(n,str) or not n.strip() or len(n)>80 or n.casefold() in names or any(ord(c)<32 for c in n):
            raise ValueError('Use distinct bounded layer names')
        names.add(n.casefold())
        if type(layer['visible']) is not bool:raise ValueError('Visibility must be boolean')
    check_composition({**s,'layers':[{k:v for k,v in layer.items() if k not in ('name','visible')} for layer in s['layers']]})
    if s['width']*s['height']>1024*1024 or sum(l['width']*l['height'] for l in s['layers'])>4*1024*1024:
        raise ValueError('Layered image exceeds canvas or aggregate layer pixel bound')
    return s

def png_bytes(im):
    b=io.BytesIO();im.save(b,format='PNG',compress_level=6);return b.getvalue()

def build(raws,s):
    checked(s)
    if len(raws)!=len(s['layers']):raise ValueError('Layer count mismatch')
    Image=image_module();w,h=s['width'],s['height'];entries={}
    xml=ET.Element('image',{'version':'0.0.3','w':str(w),'h':str(h),'name':'JANUS layered image','xres':'72','yres':'72'})
    stack=ET.SubElement(xml,'stack')
    with Image.new('RGBA',(w,h),tuple(s['background'])+(255,)) as canvas:
        entries['data/background.png']=png_bytes(canvas)
        records=[]
        for i,(layer,raw) in enumerate(zip(s['layers'],raws)):
            path=f'data/layer{i}.png'
            with decode_layer(raw) as source:
                with source.resize((layer['width'],layer['height']),Image.Resampling.LANCZOS) as resized:
                    entries[path]=png_bytes(resized)
                    if layer['visible']:
                        with resized.copy() as active:
                            if layer['opacity']!=255:
                                with active.getchannel('A') as alpha,alpha.point([(v*layer['opacity']+127)//255 for v in range(256)]) as adjusted:active.putalpha(adjusted)
                            canvas.alpha_composite(active,dest=(layer['x'],layer['y']))
            records.append((layer,path))
        with canvas.convert('RGB') as rgb:entries['mergedimage.png']=png_bytes(rgb)
        with canvas.copy() as thumb:
            thumb.thumbnail((256,256));entries['Thumbnails/thumbnail.png']=png_bytes(thumb)
    for layer,path in reversed(records):
        ET.SubElement(stack,'layer',{'name':layer['name'],'src':path,'x':str(layer['x']),'y':str(layer['y']),
             'opacity':format(layer['opacity']/255,'.9f'),'visibility':'visible' if layer['visible'] else 'hidden','composite-op':'svg:src-over'})
    ET.SubElement(stack,'layer',{'name':'Background','src':'data/background.png','x':'0','y':'0','opacity':'1.0','visibility':'visible','composite-op':'svg:src-over'})
    entries['stack.xml']=ET.tostring(xml,encoding='utf-8',xml_declaration=True)
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:
        z.writestr('mimetype',MIME,compress_type=zipfile.ZIP_STORED)
        for name,data in entries.items():z.writestr(name,data,compress_type=zipfile.ZIP_DEFLATED)
    payload=buf.getvalue()
    if len(payload)>guard.MAX_OUTPUT:raise ValueError('Editable image exceeds output bound')
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or z.namelist()!=['mimetype',*entries] or z.read('mimetype')!=MIME or any(z.read(k)!=v for k,v in entries.items()):
            raise ValueError('OpenRaster roundtrip mismatch')
        parsed=ET.fromstring(z.read('stack.xml'))
        if [e.attrib['src'] for e in parsed.find('stack')]!=[path for _,path in reversed(records)]+['data/background.png']:
            raise ValueError('Layer order changed')
    return payload,{'width':w,'height':h,'layer_count':len(records)+1,'editable_raster_layers':True,
         'layer_order_verified':True,'source_sha256':[hashlib.sha256(x).hexdigest() for x in raws],
         'merged_sha256':hashlib.sha256(entries['mergedimage.png']).hexdigest(),'external_editor_acceptance_verified':False,
         'visual_quality_verified':False}

def paths(root,s,exclude):
    pp=[guard.path_for(root,l['image'],exclude,{'.png'},exists=True) for l in s['layers']]
    if sum(p.stat().st_size for p in pp)>guard.MAX_INPUT or any(a.samefile(b) for i,a in enumerate(pp) for b in pp[:i]):
        raise ValueError('Duplicate or oversized layer inputs')
    return pp

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or not 3<=len(plan['guards'])<=7:raise ValueError('Invalid layered image approval')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.ora')
    pp=paths(Path(root).resolve(strict=True),s,plan['exclude'])
    if len(pp)!=len(plan['guards'])-1 or any(snapshot_file(p)!=g for p,g in zip(pp,plan['guards'][1:])):raise ValueError('Reviewed layer changed')
    return s,dst,pp

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.ora')
    pp=paths(Path(plan['root']),s,plan['exclude']);plan['guards'].extend(snapshot_file(p) for p in pp)
    s,_,pp=validate(root,plan)
    _,r=build([guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(pp,plan['guards'][1:])],s)
    return plan,dict(s,verification=r,scope='Editable OpenRaster layers, not a flattened-only PNG.')

def execute(root,plan):
    s,dst,pp=validate(root,plan)
    payload,r=build([guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(pp,plan['guards'][1:])],s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-layered-image-result-v1','status':'editable_layers_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed layer document or source'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
