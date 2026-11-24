"""Explicit Triad-only installation; runtime probe precedes large downloads."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import venv
from pathlib import Path
from urllib.request import urlopen,Request
from deepthort_local.triad_profiles import ROOT,PROFILES,RUNTIME_VERSION,REQUIRED,OPTIONAL,model_path,runtime_path
from deepthort_local.disk_gate import DiskGate

def atomic_json(path,obj):
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj,indent=2),encoding='utf-8')
    os.replace(tmp,path)

def verify(path,entry,gate):
    if not path.is_file() or path.stat().st_size!=entry['size']:return False
    sha=entry['digest']
    h=hashlib.sha256() if len(sha)==64 else hashlib.sha1()
    if len(sha)==40:h.update(('blob '+str(entry['size'])+'\0').encode())
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            gate.pace(len(block));h.update(block)
    return h.hexdigest()==sha

def manifest(role):
    name,repo,rev,minimum=PROFILES[role]
    url='https://huggingface.co/api/models/'+repo+'/revision/'+rev+'?blobs=true'
    with urlopen(Request(url,headers={'User-Agent':'DeepThorT-Triad/2'}),timeout=60) as response:
        data=json.loads(response.read(4*1024**2))
    if data.get('sha')!=rev:raise ValueError('Unexpected publisher revision '+role)
    entries={}
    for row in data['siblings']:
        filename=row['rfilename']
        if filename not in REQUIRED|OPTIONAL:continue
        sha=(row.get('lfs') or {}).get('sha256') or row.get('blobId')
        size=row.get('size')
        if type(size) is not int or size<=0 or not isinstance(sha,str) or len(sha) not in (40,64):
            raise ValueError('Publisher did not provide file size/hash: '+filename)
        entries[filename]={'size':size,'digest':sha}
    if not REQUIRED<=entries.keys() or entries['openvino_model.bin']['size']<minimum:
        raise ValueError('Publisher IR files incomplete: '+role)
    if sum(v['size'] for v in entries.values())>minimum+1_200_000_000:
        raise ValueError('Unexpected model download size')
    return {'repo':repo,'revision':rev,'files':entries}

def download(url,path,meta,gate):
    if verify(path,meta,gate):
        print('Verified existing',path.name,flush=True);return
    part=path.with_suffix(path.suffix+'.part')
    offset=part.stat().st_size if part.exists() else 0
    if offset>meta['size']:part.unlink();offset=0
    if offset==meta['size']:
        if verify(part,meta,gate):os.replace(part,path);return
        part.unlink();offset=0
    headers={'User-Agent':'DeepThorT-Triad/2'}
    if offset:headers['Range']='bytes='+str(offset)+'-'
    with urlopen(Request(url,headers=headers),timeout=120) as response:
        if offset and (response.status!=206 or not response.headers.get('Content-Range','').startswith('bytes '+str(offset)+'-')):
            offset=0
        written=offset;last=offset
        with part.open('ab' if offset else 'wb') as output:
            while True:
                gate.wait_for_non_game()
                block=response.read(1024*1024)
                if not block:break
                written+=len(block)
                if written>meta['size']:raise ValueError('Download exceeds verified size')
                output.write(block);gate.pace(len(block))
                if written-last>=64*1024**2:
                    print(path.parent.name,path.name,round(written/1e9,2),'GB',flush=True);last=written
    if not verify(part,meta,gate):raise ValueError('Incomplete or invalid publisher file: '+path.name)
    os.replace(part,path)

def install_runtime():
    if sys.version_info<(3,10) or sys.maxsize<=2**32:
        raise RuntimeError('Python 3.10+ x64 required')
    exe=runtime_path()
    if not exe.is_file():
        venv.EnvBuilder(with_pip=True).create(exe.parent.parent)
    marker=ROOT/'runtime/openvino-verified.json'
    if marker.exists():marker.unlink()
    # Use isolated venv, never alter original DeepThorT or global Python.
    subprocess.run([str(exe),'-m','pip','--isolated','install','--only-binary=:all:',
        '--index-url','https://pypi.org/simple','openvino-genai=='+RUNTIME_VERSION],check=True)
    subprocess.run([str(exe),'-I',str(ROOT/'triad_openvino_worker.py'),'--probe'],cwd=ROOT,check=True)
    atomic_json(marker,{'version':RUNTIME_VERSION,'backend':'native-openvino-ir-cpu'})

def main():
    from deepthort_local.triad_job import verify_root_cap
    verify_root_cap()
    gate=DiskGate(bytes_per_second=3*1024**2,game_names_path=ROOT/'game_executables.txt',game_flag=ROOT/'state/game-active.flag')
    gate.wait_for_non_game()
    install_runtime()
    manifests={r:manifest(r) for r in PROFILES}
    need=sum(sum(x['size'] for x in m['files'].values()) for m in manifests.values())
    # Conservative free disk estimate (existing valid files may be reused).
    if shutil.disk_usage(ROOT).free<need+512*1024**2:raise RuntimeError('Insufficient free disk space for IR downloads')
    # Validate small Sentinel before larger downloads. No arbitrary remote code.
    for role in ('sentinel','janus','implementation'):
        m=manifests[role];base=model_path(role);base.mkdir(parents=True,exist_ok=True)
        print('Preparing',PROFILES[role][0],flush=True)
        for name,entry in sorted(m['files'].items()):
            download('https://huggingface.co/'+m['repo']+'/resolve/'+m['revision']+'/'+name,base/name,entry,gate)
        atomic_json(base/'verified-install.json',m)
        # First real CPU load and one short synthetic generation before proceeding.
        # This is only a sequential installation smoke test; normal operation
        # requires all three independent model processes resident simultaneously.
        from deepthort_local.triad_job import child_server
        log=ROOT/'state/logs'/('triad-install-'+role+'.log')
        with child_server([str(runtime_path()),'-I',str(ROOT/'triad_openvino_worker.py'),'--smoke',role],ROOT,log) as (_,alive):
            deadline=time.monotonic()+1200
            while alive() and time.monotonic()<deadline:time.sleep(1)
            if alive():raise RuntimeError('Model smoke test timed out: '+role)
            if alive.code()!=0:raise RuntimeError('Model smoke test failed: '+role+' '+alive.failure())
        print('Verified native CPU inference:',role,flush=True)
    print('All three native IR models installed. Start AI for simultaneous residency.',flush=True)

if __name__=='__main__':main()
