"""Explicit Triad-only installation; runtime probe precedes large downloads."""
import hashlib
import base64
import stat
import tempfile
import zipfile
from urllib.parse import urlsplit
import json
import os
import shutil
import subprocess
import sys
import time
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

# OpenVINO GenAI 2026.4.1.0 publishes Windows x64 wheels for these
# interpreters. Do not use the newest installed Python indiscriminately.
SUPPORTED_RUNTIME_MINORS=(13,12,11,10)
PRIVATE_PYTHON_VERSION='3.13.17'
NUGET_ROOT='https://api.nuget.org/v3-flatcontainer/python/'+PRIVATE_PYTHON_VERSION+'/'
NUGET_NAME='python.'+PRIVATE_PYTHON_VERSION+'.nupkg'
MAX_PYTHON_PACKAGE=40*1024**2
MAX_PYTHON_EXPANDED=160*1024**2

def probe_python(command):
    try:
        result=subprocess.run([*command,'-I','-c',
            'import json,sys,struct,platform; print(json.dumps([sys.executable, list(sys.version_info[:2]), struct.calcsize("P"), platform.machine()]))'],
            check=True,capture_output=True,text=True,timeout=20,
            env={**os.environ,'PYTHON_MANAGER_AUTOMATIC_INSTALL':'0'})
        exe,version,pointer_size,machine=json.loads(result.stdout.strip())
        if (version[0]==3 and version[1] in SUPPORTED_RUNTIME_MINORS
                and pointer_size==8 and machine.casefold() in ('amd64','x86_64')):
            return Path(exe)
    except (OSError,ValueError,TypeError,IndexError,subprocess.SubprocessError):
        pass
    return None

def _metadata(url):
    address=urlsplit(url)
    if address.scheme!='https' or address.netloc!='api.nuget.org':
        raise ValueError('Unexpected Python package metadata host')
    with urlopen(Request(url,headers={'User-Agent':'DeepThorT-Triad/3'}),timeout=60) as response:
        data=response.read(1024**2+1)
    if len(data)>1024**2:raise ValueError('Python metadata too large')
    return json.loads(data)

def python_package_hash():
    # Exact official CPython package from NuGet. The catalog provides the
    # SHA-512 for the immutable package, independent of the archive download.
    leaf=_metadata('https://api.nuget.org/v3/registration5-semver1/python/'+PRIVATE_PYTHON_VERSION+'.json')
    catalog=leaf['catalogEntry']
    data=_metadata(catalog) if isinstance(catalog,str) else catalog
    if data['id'].casefold()!='python' or data['version']!=PRIVATE_PYTHON_VERSION:
        raise ValueError('Unexpected Python package identity')
    if data['packageHashAlgorithm'].casefold()!='sha512':
        raise ValueError('Unexpected Python package hash algorithm')
    expected=base64.b64decode(data['packageHash'],validate=True)
    if len(expected)!=64:raise ValueError('Invalid Python package hash')
    return expected

def extract_python_package(archive,dest):
    """Extract only tools/ into a fresh private directory; no archive paths escape."""
    with zipfile.ZipFile(archive) as z:
        selected=[];seen=set();total=0
        for member in z.infolist():
            name=member.filename
            if not name.startswith('tools/'):continue
            relative=name[len('tools/'):]
            if not relative:continue
            parts=relative.rstrip('/').split('/')
            if ('\\' in relative or any(not p or p in ('.','..') or ':' in p or
                 p.endswith((' ','.')) or p.casefold().split('.')[0] in
                 {'con','prn','aux','nul',*(f'com{i}' for i in range(1,10)),*(f'lpt{i}' for i in range(1,10))}
                 for p in parts) or stat.S_ISLNK(member.external_attr>>16)):
                raise ValueError('Unsafe Python package member')
            key='/'.join(parts).casefold()
            if key in seen:raise ValueError('Duplicate Python package member')
            seen.add(key);total+=member.file_size
            if len(seen)>20000 or total>MAX_PYTHON_EXPANDED:
                raise ValueError('Python package exceeds extraction budget')
            selected.append((member,parts))
        if 'python.exe' not in seen or 'python313.dll' not in seen:
            raise ValueError('Missing Python runtime binaries')
        for member,parts in selected:
            target=dest.joinpath(*parts)
            if member.is_dir():target.mkdir(parents=True,exist_ok=True);continue
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(member) as src,target.open('xb') as out:
                shutil.copyfileobj(src,out,1024*1024)

def provision_private_python():
    if os.name!='nt':raise RuntimeError('Automatic private Python requires Windows x64')
    base=ROOT/'runtime'/('cpython-'+PRIVATE_PYTHON_VERSION+'-x64')
    exe=base/'python.exe'
    if exe.is_file() and probe_python([str(exe)]):return exe
    base.parent.mkdir(parents=True,exist_ok=True)
    from deepthort_local.triad_job import verify_root_cap
    verify_root_cap()
    gate=DiskGate(bytes_per_second=3*1024**2,game_names_path=ROOT/'game_executables.txt',game_flag=ROOT/'state/game-active.flag')
    gate.wait_for_non_game()
    print('Preparing private CPython '+PRIVATE_PYTHON_VERSION+' x64; no global Python changes.',flush=True)
    expected=python_package_hash()
    with tempfile.TemporaryDirectory(prefix='python-bootstrap-',dir=base.parent) as temporary:
        stage=Path(temporary)
        archive=stage/NUGET_NAME
        digest=hashlib.sha512();size=0
        with urlopen(Request(NUGET_ROOT+NUGET_NAME,headers={'User-Agent':'DeepThorT-Triad/3'}),timeout=120) as response,archive.open('xb') as out:
            for block in iter(lambda:response.read(256*1024),b''):
                gate.wait_for_non_game()
                size+=len(block)
                if size>MAX_PYTHON_PACKAGE:raise ValueError('Python download exceeds budget')
                digest.update(block);out.write(block);gate.pace(len(block))
        if digest.digest()!=expected:raise ValueError('CPython package SHA-512 mismatch')
        unpacked=stage/'python';unpacked.mkdir()
        extract_python_package(archive,unpacked)
        # Verify the package's ABI before moving to its final location.
        if not probe_python([str(unpacked/'python.exe')]):
            raise RuntimeError('Downloaded CPython could not start as supported x64 Python')
        if base.exists():base.rename(base.with_name(base.name+'-incompatible-'+str(time.time_ns())))
        unpacked.rename(base)
    if not probe_python([str(exe)]):raise RuntimeError('Private Python failed final probe')
    return exe

def choose_runtime_python():
    current=probe_python([sys.executable])
    if current:return current
    launcher=shutil.which('py')
    if launcher:
        for minor in SUPPORTED_RUNTIME_MINORS:
            candidate=probe_python([launcher,'-3.'+str(minor)])
            if candidate:return candidate
    return provision_private_python()

def ensure_runtime_environment(exe):
    if exe.is_file() and probe_python([str(exe)]):
        return
    base=choose_runtime_python()
    environment=exe.parent.parent
    if environment.exists():
        # Keep the failed environment; no recursive deletion and no changes to
        # model weights or project state. A fresh venv is required for a new ABI.
        backup=environment.with_name(environment.name+'-incompatible-'+str(time.time_ns()))
        environment.rename(backup)
        print('Preserved incompatible runtime:',backup,flush=True)
    print('Creating private OpenVINO runtime using',base,flush=True)
    subprocess.run([str(base),'-I','-m','venv','--without-pip',str(environment)],check=True)
    # CPython's reduced NuGet distribution can have pip but no bundled
    # ensurepip wheels. Use its pip to install into the new private venv.
    if probe_python([str(exe)]):
        result=subprocess.run([str(exe),'-I','-m','ensurepip','--upgrade'],check=False)
        if result.returncode:
            subprocess.run([str(base),'-I','-m','pip','--isolated','--python',str(exe),'install',
                '--only-binary=:all:','--index-url','https://pypi.org/simple','pip==25.3'],check=True)
    if not exe.is_file() or not probe_python([str(exe)]):
        raise RuntimeError('New virtual environment did not use a supported x64 Python')

def install_runtime():
    exe=runtime_path()
    marker=ROOT/'runtime/openvino-verified.json'
    if marker.exists():marker.unlink()
    ensure_runtime_environment(exe)
    # Use isolated venv, never alter original DeepThorT or global Python.
    subprocess.run([str(exe),'-I','-m','pip','--isolated','install','--only-binary=:all:',
        '--index-url','https://pypi.org/simple','openvino-genai=='+RUNTIME_VERSION],check=True)
    subprocess.run([str(exe),'-I',str(ROOT/'triad_openvino_worker.py'),'--probe'],cwd=ROOT,check=True)
    atomic_json(marker,{'version':RUNTIME_VERSION,'backend':'native-openvino-ir-cpu'})

def main():
    from deepthort_local.triad_job import verify_root_cap
    verify_root_cap()
    gate=DiskGate(bytes_per_second=3*1024**2,game_names_path=ROOT/'game_executables.txt',game_flag=ROOT/'state/game-active.flag')
    gate.wait_for_non_game()
    args=sys.argv[1:]
    if args and args!=['--runtime-only'] and not (len(args)==2 and args[0]=='--role' and args[1] in PROFILES):
        raise SystemExit('Usage: download_model.py [--runtime-only | --role implementation|janus|sentinel]')
    install_runtime()
    if args==['--runtime-only']:
        print('Verified native OpenVINO runtime (no model downloads).',flush=True);return
    roles=(args[1],) if args else ('sentinel','janus','implementation')
    manifests={r:manifest(r) for r in roles}
    need=sum(sum(x['size'] for x in m['files'].values()) for m in manifests.values())
    # Conservative free disk estimate (existing valid files may be reused).
    if shutil.disk_usage(ROOT).free<need+512*1024**2:raise RuntimeError('Insufficient free disk space for IR downloads')
    # Validate small Sentinel before larger downloads. No arbitrary remote code.
    for role in roles:
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
    print('Selected native IR models installed and individually smoke-tested: '+', '.join(roles),flush=True)
    if not args:print('Start AI for three-model residency under the shared cap.',flush=True)

if __name__=='__main__':main()
