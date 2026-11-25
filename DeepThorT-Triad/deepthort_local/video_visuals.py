"""Scene assets bound to a reviewed storyboard. No publication authorization."""
import hashlib
import json
import os
import sys
import struct
import tempfile
import time
from datetime import datetime,timezone
from pathlib import Path
from .video_planning import canonical,validate_plan
from .reasoning_council import sha
from .artifact_media_checks import png
from .stock_images import MAX_IMAGE
from .local_speech import json_read

ROOT=Path(__file__).resolve().parents[1]
MEMORY_LIMIT=512*1024**2

def stop(cancelled):
    if cancelled and cancelled():raise ValueError('Visual acquisition cancelled or deferred')

def bounded_bytes(path):
    path=Path(path)
    if not path.is_file() or path.is_symlink() or not 1<=path.stat().st_size<=MAX_IMAGE:
        raise ValueError('Image missing or outside 12 MiB bound')
    with path.open('rb') as f:data=f.read(MAX_IMAGE+1)
    if len(data)>MAX_IMAGE or not (data.startswith(b'\x89PNG\r\n\x1a\n') or data.startswith(b'\xff\xd8')):
        raise ValueError('Only bounded PNG/JPEG images are accepted')
    return data

def inspect(path):
    data=bounded_bytes(path)
    png(data)
    w,h=struct.unpack('>II',data[16:24])
    if not 1<=w<=1920 or not 1<=h<=1920:raise ValueError('Normalized image dimensions exceed bounds')
    return {'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'width':w,'height':h}

def supervised(command,folder,*,cancelled=None,memory_limit=MEMORY_LIMIT,seconds=60):
    from .triad_job import verify_root_cap,child_server
    _,available,total=verify_root_cap()
    reserve=memory_limit if memory_limit else 2*1024**3
    if available<total//10+reserve:raise RuntimeError('Insufficient foreground memory reserve for image operation')
    with child_server(command,folder,folder/'worker.log',memory_limit=memory_limit) as (_,alive):
        deadline=time.monotonic()+seconds
        while alive():
            stop(cancelled)
            if time.monotonic()>=deadline:raise TimeoutError('Image operation timed out; cleanup job closed')
            time.sleep(.15)
        if alive.code()!=0:raise RuntimeError('Local image operation failed (exit '+str(alive.code())+')')
    stop(cancelled)

def normalize(data,dest,cancelled=None):
    if os.name!='nt':raise RuntimeError('Native Windows image decoder required')
    ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    with tempfile.TemporaryDirectory(prefix='triad-image-decode-') as temp:
        folder=Path(temp)
        (folder/'input.image').write_bytes(data)
        supervised([str(ps),'-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','RemoteSigned',
            '-File',str(ROOT/'triad_visual.ps1'),'-Folder',str(folder)],folder,cancelled=cancelled)
        result=inspect(folder/'image.png')
        with Path(dest).open('xb') as f:f.write((folder/'image.png').read_bytes())
        if inspect(dest)!=result:raise ValueError('Normalized image changed')
        return result

def generate(description,cancelled=None):
    from .media_tools import cli_image_args
    model=ROOT/'models'/'stable-diffusion-v1-5'
    index=model/'model_index.json'
    if not index.is_file():raise ValueError('Install the optional offline image generator first in Files & Images')
    before=hashlib.sha256(index.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix='triad-video-image-') as temp:
        folder=Path(temp);output=folder/'generated.png'
        command=cli_image_args(sys.executable,ROOT/'run_image.py',model,description,output,384,384,15)
        # Diffusion cannot fit the small auxiliary cap. It remains in the
        # inherited shared hard cap and a nested kill-on-close job.
        supervised(command,folder,cancelled=cancelled,memory_limit=None,seconds=900)
        data=bounded_bytes(output)
    if hashlib.sha256(index.read_bytes()).hexdigest()!=before:raise ValueError('Image model metadata changed')
    return data,{'engine':'local SD1.5 CPU Diffusers','model_index_sha256':before,'prompt_sha256':sha(description),
                 'rights_status':'model/output terms and third-party rights require review','illustration':True}

def root_for(folder,request,plan):
    validate_plan(request,plan)
    digest=sha(canonical(plan))
    root=Path(folder)/('request-'+str(request['id'])+'-'+digest[:20])
    return root,digest

def read_scene(root,digest,scene):
    target=root/f'scene-{scene:02d}'
    if not target.exists():return None
    if target.is_symlink():raise ValueError('Asset folder is a symlink')
    receipt=json_read(target/'receipt.json')
    if (not isinstance(receipt,dict) or set(receipt)!={'plan_sha256','scene','source','original_sha256','image','acquired_utc'}
        or receipt['plan_sha256']!=digest or receipt['scene']!=scene or receipt['image']!=inspect(target/'image.png')):
        raise ValueError('Scene asset receipt or image changed')
    return receipt

def assign(folder,request,plan,scene,mode,*,review=None,select=None,provided=None,cancelled=None,
           searcher=None,downloader=None,generator=None,normalizer=None):
    from . import stock_images
    root,digest=root_for(folder,request,plan)
    if type(scene) is not int or not 1<=scene<=len(plan['scripts']):raise ValueError('Invalid scene number')
    if mode not in ('stock','generate','provided'):raise ValueError('Invalid image source')
    row=plan['scripts'][scene-1]
    # Explicit user-provided imagery can override a planned sourcing intent.
    if mode!='provided' and row['asset_source'] not in (mode,'either'):
        raise ValueError('Scene requires a different source type')
    stop(cancelled)
    root.mkdir(parents=True,exist_ok=True)
    if root.is_symlink():raise ValueError('Asset folder is a symlink')
    old=read_scene(root,digest,scene)
    if old:
        if old['source']['type']!=mode:raise ValueError('Scene already has another asset; use a new reviewed draft')
        if mode=='provided' and hashlib.sha256(bounded_bytes(provided)).hexdigest()!=old['original_sha256']:
            raise ValueError('Scene already has a different supplied image')
        return old
    description=row['visual']
    if mode=='stock':
        options=(searcher or stock_images.search)(description,cancelled)
        if not options:raise ValueError('No bounded Commons images with supported license metadata; try a supplied/generated image')
        if select is None or review is None:raise ValueError('Stock selection and review required')
        ident=select(row,options)
        matches=[c for c in options if type(ident) is int and c['id']==ident]
        if len(matches)!=1:raise ValueError('No valid stock image selected')
        chosen=matches[0]
        if review({'scene':scene,'visual':description,'candidate':chosen},f'Video scene {scene} stock image') is not True:
            raise ValueError('Stock image selection rejected')
        stop(cancelled)
        data=(downloader or stock_images.download)(chosen,cancelled)
        source={'type':'stock','provider':'Wikimedia Commons','candidate':chosen,
                'rights_status':'provider license metadata only; verify source page, other rights and attribution before publication',
                'modified':'normalized to PNG, resized if necessary'}
    elif mode=='generate':
        data,details=(generator or generate)(description,cancelled)
        source={'type':'generate',**details}
    else:
        if provided is None:raise ValueError('Attach exactly one permitted PNG/JPEG image')
        data=bounded_bytes(provided)
        source={'type':'provided','filename':Path(provided).name,
                'rights_status':'user explicitly supplied for use; publication rights not independently verified'}
    if not isinstance(data,bytes) or len(data)>MAX_IMAGE or not (
        data.startswith(b'\x89PNG\r\n\x1a\n') or data.startswith(b'\xff\xd8')):
        raise ValueError('Invalid acquired image bytes')
    stop(cancelled)
    with tempfile.TemporaryDirectory(prefix='.visual-',dir=root) as temp:
        ready=Path(temp)/'complete';ready.mkdir()
        image=ready/'image.png'
        info=(normalizer or normalize)(data,image,cancelled)
        if inspect(image)!=info:raise ValueError('Normalized image evidence mismatch')
        receipt={'plan_sha256':digest,'scene':scene,'source':source,
                 'original_sha256':hashlib.sha256(data).hexdigest(),'image':info,
                 'acquired_utc':datetime.now(timezone.utc).isoformat(timespec='seconds')}
        (ready/'receipt.json').write_text(canonical(receipt),encoding='utf-8')
        stop(cancelled)
        target=root/f'scene-{scene:02d}'
        if target.exists():raise ValueError('Scene output appeared during acquisition')
        ready.rename(target)
    return receipt

def status(folder,request,plan):
    root,digest=root_for(folder,request,plan)
    rows=[read_scene(root,digest,n) for n in range(1,len(plan['scripts'])+1)]
    manifest={'schema':'deepthort-video-visuals-v1','binding':plan['binding'],'plan_sha256':digest,
              'scenes':[x for x in rows if x],'missing':[n for n,x in enumerate(rows,1) if not x],
              'rendered':False,'publication_rights_verified':False}
    if root.exists():
        if root.is_symlink():raise ValueError('Asset folder is a symlink')
        fd,tmp=tempfile.mkstemp(prefix='.visual-manifest-',dir=root)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(canonical(manifest));f.flush();os.fsync(f.fileno())
            os.replace(tmp,root/'visuals.json')
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    return manifest,root
