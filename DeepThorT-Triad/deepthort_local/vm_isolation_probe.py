"""Fixed benign QEMU guest probe of read-only virtual media.

Checks a real guest boot marker, BIOS read/write behaviour and unchanged host
image bytes. Does not test hypervisor escapes or prove general host isolation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import virtual_computer as vm
from deepthort_local.action_guards import verify_guards
from deepthort_local.disk_gate import DiskGate,require_storage

SCHEMA='deepthortriad-vm-readonly-media-probe-v1'
SUCCESS=b'DTT_VM_READ_OK_WRITE_DENIED\n'
FAILURE=b'DTT_VM_PROBE_FAILED\n'
# Assembled from the fixed 16-bit GNU assembler source in the adjacent test
# fixture documentation. Starts at physical 0x7c00, initializes segments,
# reads CHS sector 2, checks 0x1234, attempts a write of 0x5678, checks
# carry-set, rereads 0x1234, emits the result on debug port 0xe9, then halts.
BOOT=bytes.fromhex('fa31c08ed88ec08ed0bc007cfbfc8816617ce83a007228813e000634127520c70600067856b80103e827007312e81f00720d813e000634127505be627ceb03be7f7cac84c07404e6e9ebf7faf4ebfcb80102bb0006b9020031d28a16617ccd13c3004454545f564d5f524541445f4f4b5f57524954455f44454e4945440a004454545f564d5f50524f42455f4641494c45440a00')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'probe','seconds','trusted_emulator'} or s['probe']!='readonly_guest_media' or s['trusted_emulator'] is not True:
        raise ValueError('Choose fixed benign read-only guest media probe and trusted emulator')
    if type(s['seconds']) is not int or not 10<=s['seconds']<=90:raise ValueError('Choose 10–90 seconds')
    return s

def fixture():
    return BOOT.ljust(510,b'\0')+b'\x55\xaa'+b'\x34\x12'+bytes(1474560-514)

def command(s,exe):
    checked(s)
    return [exe,'-no-user-config','-machine','pc,accel=tcg','-smp','1','-m','128',
            '-nodefaults','-display','none','-monitor','none','-serial','none','-parallel','none','-nic','none',
            '-drive','if=floppy,file=probe.img,format=raw,readonly=on',
            '-debugcon','file=guest.log','-global','isa-debugcon.iobase=0xe9',
            '-boot','order=a','-no-reboot','-no-shutdown']

def validate(root,plan):
    if not isinstance(plan,dict) or 'runtime' not in plan:raise ValueError('Missing reviewed QEMU runtime')
    s,dst,_=guard.validate(root,{k:v for k,v in plan.items() if k!='runtime'},schema=SCHEMA,checked=checked,output_suffix='.json')
    if plan['runtime']!=vm.runtime(root):raise ValueError('Reviewed QEMU runtime changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    plan['runtime']=vm.runtime(root);validate(root,plan)
    return plan,dict(s,command=command(s,plan['runtime']['path']),fixture_sha256=hashlib.sha256(fixture()).hexdigest(),
        scope='Boot a fixed benign guest fixture under trusted QEMU, read known virtual floppy sector, test BIOS write denial, reread and verify unchanged host image. No user code, configured network or shared host directory. This probes one read-only media boundary only, not general VM escape resistance.')

def assess(marker,before,after):
    if marker!=SUCCESS or before!=fixture() or after!=before:raise ValueError('Guest marker or exact media preservation not established')
    return {'guest_boot_marker_verified':True,'guest_read_verified':True,'guest_bios_write_denied':True,
            'host_image_unchanged':True,'fixture_sha256':hashlib.sha256(before).hexdigest(),
            'network_configured':False,'host_shares_configured':False,'general_security_isolation_verified':False,
            'host_filesystem_access_tested':False,'guest_network_access_tested':False}

def run(s,stage,plan):
    from deepthort_local.triad_job import child_server,verify_root_cap
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    cap,available,total=verify_root_cap()
    gaming=DiskGate(game_names_path=vm.ROOT/'game_executables.txt',game_flag=vm.ROOT/'state/game-active.flag')
    sampler=WindowsPressureSampler()
    if cap<2*1024**3 or available<total//10+1024**3 or gaming.gaming():raise ValueError('Protected host headroom unavailable')
    before=fixture();disk=stage/'probe.img';disk.write_bytes(before)
    log=stage/'qemu.log';guest=stage/'guest.log'
    verify_guards([plan['runtime']]);marker=b''
    with child_server(command(s,plan['runtime']['path']),stage,log) as (pid,alive):
        if not alive.member(pid):raise ValueError('QEMU outside cleanup scope')
        deadline=time.monotonic()+s['seconds']
        while alive():
            cpu,free=sampler.read()
            if gaming.gaming() or free is None or free<10 or (cpu is not None and cpu>=90) or time.monotonic()>=deadline or log.stat().st_size>65536:
                raise ValueError('Guest probe stopped on resource, time or log bound')
            if guest.is_file():
                if guest.stat().st_size>256:raise ValueError('Unexpected guest output')
                with guest.open('rb') as f:marker=f.read(257)
                if marker==SUCCESS:break
                if not SUCCESS.startswith(marker) or marker==FAILURE:raise ValueError('Guest probe failed')
            time.sleep(.1)
        else:raise ValueError('Emulator exited before verified guest marker')
    after=guard.read_bound(disk,len(before))
    return marker,before,after

def execute(root,plan,*,backend=None):
    s,dst=validate(root,plan);require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.deepthortriad-guest-probe-',dir=dst.parent) as tmp:
        observed=(backend or run)(s,Path(tmp),plan)
    result=assess(*observed)
    result.update(schema=SCHEMA,backend='native_qemu' if backend is None else 'injected_fixture')
    sha=guard.publish((json.dumps(result,sort_keys=True,indent=2)+'\n').encode(),dst,lambda:validate(root,plan))
    return dict(result,status='guest_readonly_media_probe_saved',output=plan['output'],sha256=sha)

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
