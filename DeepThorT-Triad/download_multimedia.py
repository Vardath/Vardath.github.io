"""Explicit GUI-approved, pinned multimedia weights installer. No inference."""
import json
import shutil
from urllib.request import Request, urlopen
from download_model import download, atomic_json
from deepthort_local.multimedia_profile import ROOT, REPO, REVISION, model_path, validate_manifest, installed
from deepthort_local.disk_gate import DiskGate
from deepthort_local.triad_job import verify_root_cap


def main():
    verify_root_cap()
    gate=DiskGate(bytes_per_second=3*1024**2,game_names_path=ROOT/'game_executables.txt',
                  game_flag=ROOT/'state/game-active.flag')
    gate.wait_for_non_game()
    url='https://huggingface.co/api/models/'+REPO+'/revision/'+REVISION+'?blobs=true'
    with urlopen(Request(url,headers={'User-Agent':'DeepThorT-Triad/3'}),timeout=60) as response:
        raw=response.read(4*1024**2+1)
    if len(raw)>4*1024**2:
        raise ValueError('Oversized publisher metadata')
    manifest=validate_manifest(json.loads(raw))
    base=model_path()
    if base.is_symlink() or base.parent.is_symlink():
        raise ValueError('Linked multimedia model location rejected')
    base.mkdir(parents=True,exist_ok=True)
    need=sum(row['size'] for row in manifest['files'].values())
    if shutil.disk_usage(base).free<need+512*1024**2:
        raise RuntimeError('Insufficient disk space for verified multimedia snapshot')
    for name,entry in sorted(manifest['files'].items()):
        target=base/name
        if target.is_symlink() or target.parent.is_symlink() or target.with_suffix(target.suffix+'.part').is_symlink():
            raise ValueError('Linked multimedia file rejected')
        target.parent.mkdir(parents=True,exist_ok=True)
        print('Preparing '+name,flush=True)
        download('https://huggingface.co/'+REPO+'/resolve/'+REVISION+'/'+name,target,entry,gate)
    receipt=base/'verified-install.json'
    if receipt.is_symlink() or receipt.with_suffix('.tmp').is_symlink():
        raise ValueError('Linked multimedia receipt rejected')
    atomic_json(receipt,manifest)
    if not installed():
        raise RuntimeError('Multimedia install receipt did not validate')
    print('Multimedia weights verified. Dedicated native inference and concurrency are not yet proven.',flush=True)


if __name__=='__main__':
    main()
