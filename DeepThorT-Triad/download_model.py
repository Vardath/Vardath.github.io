"""Explicit clone-only installation of SHA256-pinned public GGUF files."""
import hashlib
import os
import shutil
import stat
import tempfile
import zipfile
from urllib.request import urlopen,Request
from pathlib import Path
from deepthort_local.triad_profiles import ROOT,PROFILES,RUNTIME_URL,RUNTIME_SHA256,model_path,runtime_path
from deepthort_local.disk_gate import DiskGate

def fingerprint(path,gate):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            gate.pace(len(block));h.update(block)
    return h.hexdigest()

def download(url,target,digest,maximum,gate):
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.is_file() and fingerprint(target,gate)==digest:
        print('Verified existing',target.name,flush=True);return
    part=target.with_suffix(target.suffix+'.part')
    h=hashlib.sha256();size=0;last=0
    with urlopen(Request(url,headers={'User-Agent':'DeepThorT-Triad/1'}),timeout=120) as response,part.open('wb') as out:
        while True:
            gate.wait_for_non_game()
            block=response.read(1024*1024)
            if not block:break
            size+=len(block)
            if size>maximum:raise ValueError('Download exceeds pinned size budget')
            out.write(block);h.update(block);gate.pace(len(block))
            if size-last>=64*1024**2:
                print(target.name,round(size/1e9,2),'GB',flush=True);last=size
    if h.hexdigest()!=digest:raise ValueError('Publisher SHA256 mismatch: '+target.name)
    os.replace(part,target)
    print('Verified',target.name,flush=True)

def main():
    if os.name!='nt':raise SystemExit('Windows x64 only')
    gate=DiskGate(bytes_per_second=3*1024**2,game_names_path=ROOT/'game_executables.txt',game_flag=ROOT/'state/game-active.flag')
    archive=ROOT/'runtime'/'cpu.zip'
    download(RUNTIME_URL,archive,RUNTIME_SHA256,600*1024**2,gate)
    target=runtime_path().parent
    with tempfile.TemporaryDirectory(dir=archive.parent) as tmp,zipfile.ZipFile(archive) as z:
        entries=z.infolist()
        if len(entries)>2000 or sum(x.file_size for x in entries)>2*1024**3:raise ValueError('Archive too large')
        seen=set()
        for entry in entries:
            name=entry.filename.replace('\\','/')
            if (name.startswith('/') or ':' in name or any(x in ('','.','..') for x in name.rstrip('/').split('/'))
                    or name.casefold() in seen or stat.S_ISLNK(entry.external_attr>>16)):
                raise ValueError('Unsafe runtime archive member')
            seen.add(name.casefold())
        z.extractall(tmp)
        servers=list(Path(tmp).rglob('llama-server.exe'))
        if len(servers)!=1:raise ValueError('Pinned archive missing unique llama-server.exe')
        stage=target.with_name('triad-new')
        if stage.exists():shutil.rmtree(stage)
        shutil.copytree(servers[0].parent,stage)
        if target.exists():shutil.rmtree(target)
        os.replace(stage,target)
    for role,p in PROFILES.items():
        print('Preparing',p[0],flush=True)
        download('https://huggingface.co/'+p[1]+'/resolve/main/'+p[2],model_path(role),p[3],p[4]+700_000_000,gate)
    print('All three verified. Inference is offline.',flush=True)
if __name__=='__main__':main()
