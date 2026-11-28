"""Reviewed temporary x86 virtual computer using separately installed QEMU.

Software emulation only; diskless, no network or host sharing configured.
Observation is not guest boot acceptance or an adversarial sandbox guarantee.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.android_emulator import real_file
from deepthort_local.disk_gate import DiskGate,require_storage
from deepthort_local.source_security import linked

SCHEMA='deepthortriad-reviewed-virtual-computer-v1'
ROOT=Path(__file__).resolve().parents[1]
MAX_ISO=256*1024*1024
MAX_LOG=65536

def checked(s):
    if not isinstance(s,dict) or set(s)!={'iso','memory_mib','seconds','trusted_boot_media'} or not isinstance(s['iso'],str):
        raise ValueError('Choose exact boot ISO, guest memory and observation duration')
    if s['trusted_boot_media'] is not True:raise ValueError('Owner must trust boot image and installed emulator')
    if type(s['memory_mib']) is not int or s['memory_mib'] not in (128,256,512):
        raise ValueError('Choose 128, 256 or 512 MiB guest memory')
    if type(s['seconds']) is not int or not 10<=s['seconds']<=120:raise ValueError('Choose 10–120 seconds')
    return s

def runtime(root):
    raw=os.environ.get('QEMU_SYSTEM_X86_64_EXE')
    if not raw or not Path(raw).is_absolute():raise ValueError('Set QEMU_SYSTEM_X86_64_EXE to installed QEMU executable')
    exe=real_file(raw)
    if exe.name.casefold()!='qemu-system-x86_64.exe' or exe.is_relative_to(Path(root).resolve()):
        raise ValueError('Use separately installed trusted QEMU, not a project executable')
    return snapshot_file(exe,kind='stat')

def image(root,s,exclude):
    path=guard.path_for(Path(root).resolve(strict=True),s['iso'],exclude,{'.iso'},exists=True)
    if not 65536<=path.stat().st_size<=MAX_ISO:raise ValueError('ISO must be 64 KiB–256 MiB')
    before=path.stat();digest=hashlib.sha256()
    def stamp(v):return (v.st_dev,v.st_ino,v.st_size,v.st_mtime_ns,v.st_ctime_ns)
    size=0
    with path.open('rb') as f:
        if stamp(os.fstat(f.fileno()))!=stamp(before) and os.name!='nt':raise ValueError('ISO identity changed')
        while block:=f.read(1024*1024):
            size+=len(block)
            if size>MAX_ISO:raise ValueError('ISO exceeds bound')
            digest.update(block)
    if linked(path) or stamp(path.stat())!=stamp(before) or size!=before.st_size:
        raise ValueError('ISO changed during review')
    return path,{'path':str(path),'bytes':size,'sha256':digest.hexdigest()}

def validate(root,plan):
    if not isinstance(plan,dict) or set(plan).issuperset({'image','runtime'}) is False:
        raise ValueError('Missing reviewed emulator and media')
    s,dst,_=guard.validate(root,{k:v for k,v in plan.items() if k not in ('image','runtime')},schema=SCHEMA,checked=checked,output_suffix='.json')
    path,record=image(root,s,plan['exclude'])
    if plan['image']!=record or plan['runtime']!=runtime(root):raise ValueError('Reviewed emulator or ISO changed')
    return s,dst,path

def command(s,exe):
    checked(s)
    # Fixed relative staged image avoids QEMU comma-option injection.
    return [exe,'-no-user-config','-machine','pc,accel=tcg','-smp','1','-m',str(s['memory_mib']),
            '-nodefaults','-device','VGA','-display','none','-monitor','none','-serial','none',
            '-parallel','none','-nic','none','-drive','file=boot.iso,format=raw,media=cdrom,readonly=on',
            '-boot','order=d','-no-reboot','-no-shutdown']

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    _,plan['image']=image(root,s,plan['exclude']);plan['runtime']=runtime(root)
    validate(root,plan)
    return plan,dict(s,media=plan['image'],runtime=plan['runtime'],command=command(s,plan['runtime']['path']),
        scope='Run trusted local boot ISO in temporary QEMU x86 computer, one software-emulated vCPU, fixed guest RAM, no configured network or host shares, no persistent disk, no display. Verify process observation only. Not proof of guest boot or adversarial security isolation. Emulator and its firmware must be trusted.')

def copy_media(source,dst,record,gaming):
    digest=hashlib.sha256();total=0
    with source.open('rb') as f,dst.open('xb') as out:
        while block:=f.read(1024*1024):
            if gaming.gaming():raise ValueError('Gaming priority')
            total+=len(block)
            if total>MAX_ISO:raise ValueError('ISO size changed')
            digest.update(block);out.write(block)
        out.flush();os.fsync(out.fileno())
    if total!=record['bytes'] or digest.hexdigest()!=record['sha256']:raise ValueError('Staged media differs from review')

def run(s,stage,plan,path):
    from deepthort_local.triad_job import verify_root_cap,child_server
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    cap,available,total=verify_root_cap();sampler=WindowsPressureSampler()
    gaming=DiskGate(game_names_path=ROOT/'game_executables.txt',game_flag=ROOT/'state/game-active.flag')
    reserve=1024**3+s['memory_mib']*1024**2
    if cap<reserve or available<total//10+reserve or gaming.gaming():raise ValueError('Insufficient protected host headroom')
    copy_media(path,stage/'boot.iso',plan['image'],gaming)
    verify_guards([plan['runtime']]);log=stage/'qemu.log'
    observed=False;status='observation_elapsed'
    with child_server(command(s,plan['runtime']['path']),stage,log) as (pid,alive):
        if not alive.member(pid):raise ValueError('Emulator not in cleanup scope')
        deadline=time.monotonic()+s['seconds']
        while alive():
            observed=True;cpu,free=sampler.read()
            if gaming.gaming() or free is None or free<10 or (cpu is not None and cpu>=90):
                status='resource_preempted';break
            if log.stat().st_size>MAX_LOG:status='log_bound';break
            if time.monotonic()>=deadline:break
            time.sleep(.25)
        else:status='emulator_exited'
    return {'process_observed':observed,'stop_reason':status,'cleanup_scope_closed':True}

def execute(root,plan,*,backend=None):
    s,dst,path=validate(root,plan);require_storage(dst.parent,install=True)
    with tempfile.TemporaryDirectory(prefix='.deepthortriad-vm-',dir=dst.parent) as tmp:
        r=(backend or run)(s,Path(tmp),plan,path)
    if not isinstance(r,dict) or set(r)!={'process_observed','stop_reason','cleanup_scope_closed'} or type(r['process_observed']) is not bool or r['cleanup_scope_closed'] is not True or r['stop_reason'] not in ('observation_elapsed','resource_preempted','log_bound','emulator_exited'):
        raise ValueError('Invalid emulator observation')
    result=dict(r,schema=SCHEMA,media_sha256=plan['image']['sha256'],guest_memory_mib=s['memory_mib'],
        vcpus=1,software_emulation_requested=True,network_configured=False,host_shares_configured=False,
        persistent_disk_configured=False,guest_boot_verified=False,security_isolation_verified=False,
        backend='native_qemu' if backend is None else 'injected_fixture')
    digest=guard.publish((json.dumps(result,sort_keys=True,indent=2)+'\n').encode(),dst,lambda:validate(root,plan))
    return dict(result,status='virtual_computer_observation_saved',output=plan['output'],sha256=digest)

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
