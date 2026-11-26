"""Install only the fourth intelligent model using the existing verified downloader."""
import json
import shutil
from urllib.request import Request,urlopen
from download_model import download,atomic_json
from deepthort_local.creative_profile import ROOT,REPO,REVISION,path,manifest,installed
from deepthort_local.disk_gate import DiskGate
from deepthort_local.triad_job import verify_root_cap


def main():
    verify_root_cap()
    gate=DiskGate(bytes_per_second=3*1024**2,game_names_path=ROOT/'game_executables.txt',
                  game_flag=ROOT/'state/game-active.flag')
    gate.wait_for_non_game()
    url='https://huggingface.co/api/models/'+REPO+'/revision/'+REVISION+'?blobs=true'
    with urlopen(Request(url,headers={'User-Agent':'DeepThorT-Triad/4'}),timeout=60) as response:
        raw=response.read(4*1024**2+1)
    if len(raw)>4*1024**2:raise ValueError('Oversized metadata')
    data=manifest(json.loads(raw))
    base=path()
    if base.is_symlink() or base.parent.is_symlink():raise ValueError('Linked model location')
    base.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(base).free<sum(x['size'] for x in data['files'].values())+512*1024**2:
        raise RuntimeError('Insufficient disk for creative model')
    for name,entry in sorted(data['files'].items()):
        target=base/name
        if target.is_symlink() or target.with_suffix(target.suffix+'.part').is_symlink():
            raise ValueError('Linked model file')
        print('Creative model: '+name,flush=True)
        download('https://huggingface.co/'+REPO+'/resolve/'+REVISION+'/'+name,target,entry,gate)
    receipt=base/'verified-install.json'
    if receipt.is_symlink() or receipt.with_suffix('.tmp').is_symlink():
        raise ValueError('Linked receipt')
    atomic_json(receipt,data)
    if not installed():raise RuntimeError('Creative checkpoint incomplete')
    print('Fourth intelligent model installed. Run latest test for actual native inference.',flush=True)


if __name__=='__main__':
    main()
