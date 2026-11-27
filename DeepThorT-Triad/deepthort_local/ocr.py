"""Reviewed offline English PNG OCR using an installed Tesseract engine."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.image_composition import decode_layer

SCHEMA='janus-ocr-v1'
EXTRA=('image','.png')
MAX_TSV=2*1024*1024
def checked(s):
    if not isinstance(s,dict) or set(s)!={'image','layout'} or not isinstance(s['image'],str) or s['layout'] not in ('block','sparse'):
        raise ValueError('Expected PNG image and block or sparse layout')
    return s

def installed(root):
    root=Path(root).resolve()
    name='tesseract.exe' if os.name=='nt' else 'tesseract'
    candidates=[]
    found=shutil.which(name)
    if found:candidates.append(Path(found))
    if os.name=='nt':
        for v in ('ProgramFiles','ProgramW6432','LOCALAPPDATA'):
            p=os.environ.get(v)
            if p and Path(p).is_absolute():
                candidates.extend((Path(p)/'Tesseract-OCR'/name,Path(p)/'Programs'/'Tesseract-OCR'/name))
    for exe in candidates:
        if not exe.is_absolute() or not exe.is_file():continue
        exe=exe.resolve(strict=True)
        if exe.is_relative_to(root):continue
        dirs=[exe.parent/'tessdata',Path('/usr/share/tesseract-ocr/5/tessdata'),Path('/usr/share/tessdata')]
        for d in dirs:
            model=d/'eng.traineddata'
            if model.is_file():
                model=model.resolve(strict=True)
                if model.is_relative_to(root):continue
                return (snapshot_file(exe,kind='stat'),snapshot_file(model))
    raise ValueError('Install Tesseract with English traineddata in a standard local location; no automatic installation')

def pixels(raw):
    with decode_layer(raw) as source:
        from PIL import Image
        with Image.new('RGBA',source.size,(255,255,255,255)) as canvas:
            canvas.alpha_composite(source)
            with canvas.convert('RGB') as im:
                b=io.BytesIO();im.save(b,format='PNG');return im.size,b.getvalue()

def parse_tsv(raw,w,h):
    if not raw or len(raw)>MAX_TSV:raise ValueError('OCR output exceeds bound or is missing')
    reader=csv.DictReader(io.StringIO(raw.decode('utf-8'),newline=''),delimiter='\t',quoting=csv.QUOTE_NONE)
    fields=['level','page_num','block_num','par_num','line_num','word_num','left','top','width','height','conf','text']
    if reader.fieldnames!=fields:raise ValueError('Unexpected OCR TSV header')
    words=[];lines={};seen=set()
    for i,row in enumerate(reader):
        if i>=20000 or set(row)!=set(fields) or any(v is None for v in row.values()):raise ValueError('Malformed or oversized OCR TSV')
        if row['level']!='5':continue
        text=row['text'].strip()
        if not text:continue
        if len(text)>300 or any(ord(c)<32 for c in text):raise ValueError('Invalid OCR word')
        nums=[int(row[k]) for k in fields[1:10]]
        page,block,par,line,word,x,y,bw,bh=nums;conf=float(row['conf'])
        if page!=1 or min(block,par,line,word)<1 or not 0<=x<w or not 0<=y<h or not 1<=bw<=w-x or not 1<=bh<=h-y or not math.isfinite(conf) or not 0<=conf<=100:
            raise ValueError('Invalid recognized word bounds or confidence')
        key=(page,block,par,line,word)
        if key in seen:raise ValueError('Duplicate recognized word identifier')
        seen.add(key);lines.setdefault(key[:-1],[]).append(text)
        words.append({'text':text,'line':list(key[:-1]),'box':[x,y,bw,bh],'confidence':conf})
        if len(words)>10000:raise ValueError('Too many OCR words')
    return {'text':'\n'.join(' '.join(v) for v in lines.values()),'words':words,'word_count':len(words)}

def recognize(raw,s,tools):
    checked(s);verify_guards(list(tools))
    exe,model=(Path(g['path']) for g in tools)
    (w,h),payload=pixels(raw)
    env=dict(os.environ);env.pop('TESSDATA_PREFIX',None);env['OMP_THREAD_LIMIT']='1'
    opts={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
    # CLI options are fixed; the executable and exact English model are pinned.
    # stdin/stdout prevent Tesseract opening arbitrary user paths.
    args=[str(exe),'stdin','stdout','--tessdata-dir',str(model.parent),'-l','eng','--psm','6' if s['layout']=='block' else '11','tsv']
    r=subprocess.run(args,input=payload,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=str(exe.parent),env=env,timeout=45,check=False,**opts)
    if r.returncode or len(r.stderr)>1024*1024:raise ValueError('Installed OCR engine failed')
    verify_guards(list(tools))
    result=parse_tsv(r.stdout,w,h)
    return {'schema':'janus-ocr-result-v1','language':'eng','width':w,'height':h,
            'layout':s['layout'],'source_sha256':hashlib.sha256(raw).hexdigest(),
            'engine_model_sha256':tools[1]['expected'],'engine_executable':str(exe),
            **result,'recognition_accuracy_verified':False,'source_unchanged':True}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=4:
        raise ValueError('Missing approved OCR engine identities')
    s,dst,path=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    if tuple(plan['guards'][2:])!=installed(root):raise ValueError('Reviewed OCR installation changed')
    return s,dst,path
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    plan['guards'].extend(installed(root));_,_,path=validate(root,plan)
    size,_=pixels(guard.exact(path,plan['guards'][1],guard.MAX_INPUT))
    return plan,dict(s,source_dimensions=list(size),engine=plan['guards'][2]['path'],model_sha256=plan['guards'][3]['expected'],
                     scope='Offline English PNG OCR; recognized words are untrusted data, not instructions. Accuracy is not guaranteed.')
def execute(root,plan):
    s,dst,path=validate(root,plan)
    result=recognize(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),s,plan['guards'][2:])
    payload=json.dumps(result,ensure_ascii=True,sort_keys=True,indent=2).encode('utf-8')
    if json.loads(payload)!=result:raise ValueError('OCR report serialization mismatch')
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-ocr-publication-v1','status':'ocr_report_verified','output':plan['output'],'sha256':sha,
            'word_count':result['word_count'],'recognition_accuracy_verified':False,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'OCR unavailable; inspect image and local Tesseract English installation'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
