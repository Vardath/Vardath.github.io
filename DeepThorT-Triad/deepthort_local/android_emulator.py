"""User-approved Windows Android emulator startup smoke; not boot or APK acceptance."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.source_security import linked
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-android-emulator-smoke-v1'
MAX_LOG=1024*1024

def checked(s):
    if not isinstance(s,dict) or set(s)!={'avd','seconds'} or not isinstance(s['avd'],str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}',s['avd']) or '..' in s['avd']:
        raise ValueError('Choose one installed, dedicated test AVD by name')
    if type(s['seconds']) is not int or not 10<=s['seconds']<=90:
        raise ValueError('Choose a 10–90 second startup observation')
    return s

def real_file(p):
    p=Path(p).absolute()
    if not p.is_file() or any(linked(x) for x in (p,*p.parents) if x.exists()) or p.resolve(strict=True)!=p:
        raise ValueError('Installed SDK/AVD must use regular non-linked paths')
    return p

def resolve_runtime(root,s,env=None):
    checked(s);env=os.environ if env is None else env
    home=env.get('USERPROFILE')
    sdk=env.get('ANDROID_HOME') or env.get('ANDROID_SDK_ROOT')
    if not sdk and env.get('LOCALAPPDATA'):sdk=str(Path(env['LOCALAPPDATA'])/'Android'/'Sdk')
    avds=env.get('ANDROID_AVD_HOME')
    if not avds and env.get('ANDROID_USER_HOME'):avds=str(Path(env['ANDROID_USER_HOME'])/'avd')
    if not avds and home:avds=str(Path(home)/'.android'/'avd')
    if not sdk or not avds or not Path(sdk).is_absolute() or not Path(avds).is_absolute():
        raise ValueError('Installed Android SDK and standard AVD folder required')
    exe=real_file(Path(sdk)/'emulator'/'emulator.exe')
    ini=real_file(Path(avds)/(s['avd']+'.ini'))
    config=real_file(Path(avds)/(s['avd']+'.avd')/'config.ini')
    if any(p.is_relative_to(Path(root).resolve()) for p in (exe,ini,config)):
        raise ValueError('Project-local SDK or AVD refused')
    content=guard.read_bound(ini,65536).decode('utf-8-sig')
    entries=[line.split('=',1)[1].strip() for line in content.splitlines() if line.startswith('path=')]
    if len(entries)!=1 or not Path(entries[0]).is_absolute() or Path(entries[0]).resolve()!=config.parent:
        raise ValueError('AVD descriptor must identify the reviewed standard AVD folder')
    if config.stat().st_size>65536:raise ValueError('AVD configuration exceeds review bound')
    return [snapshot_file(exe,kind='stat'),snapshot_file(ini),snapshot_file(config)]

def command(s,guards):
    checked(s)
    return [guards[0]['path'],'-avd',s['avd'],'-no-window','-no-audio','-no-snapshot','-read-only',
        '-camera-back','none','-camera-front','none','-gpu','swiftshader','-memory','2048']

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=4:
        raise ValueError('Missing reviewed emulator and AVD guards')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.json')
    if plan['guards'][1:]!=resolve_runtime(root,s):raise ValueError('Reviewed SDK or AVD changed')
    return s,dst

def monitor(alive,log,seconds,sampler,*,clock=time.monotonic,sleep=time.sleep):
    deadline=clock()+seconds;last=clock();peak=0;status='startup_process_observed';exit_code=None
    while True:
        if not alive():
            status='emulator_exited';exit_code=alive.code();break
        size=log.stat().st_size
        peak=max(peak,size)
        if size>MAX_LOG:status='log_bound_exceeded';break
        cpu,ram=sampler.read()
        # Conservatively defer under sustained high host pressure regardless of game detection.
        if ram is None or ram<10:status='resource_reserve_unavailable';break
        if cpu is not None and cpu>=90:status='host_cpu_pressure';break
        now=clock()
        if now>=deadline:break
        last=now;sleep(min(0.25,deadline-now))
    return {'status':status,'process_exit_code':exit_code,'observed_seconds':round(max(0,min(seconds,clock()-(deadline-seconds))),3),
            'log_bytes_observed':peak,'android_boot_verified':False,'apk_execution_verified':False}

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    plan['guards'].extend(resolve_runtime(root,s))
    return plan,dict(s,command=command(s,plan['guards'][1:]),scope='Launch an existing dedicated test AVD headlessly under the shared cap; read-only mode and no snapshots. SDK may write temporary host files or use networking. No ADB, no APK installation, no boot proof.')

def execute(root,plan):
    s,dst=validate(root,plan)
    from deepthort_local.triad_job import verify_root_cap,child_server
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    verify_root_cap()
    sampler=WindowsPressureSampler()
    cpu,ram=sampler.read()
    if ram is None or ram<15:raise ValueError('Insufficient observed host RAM reserve')
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-emulator-',dir=dst.parent) as tmp:
        log=Path(tmp)/'emulator.log'
        verify_guards(plan['guards'])
        with child_server(command(s,plan['guards'][1:]),Path(plan['guards'][1]['path']).parent,log) as (pid,alive):
            if not alive.member(pid):raise ValueError('Emulator outside cleanup job')
            result=monitor(alive,log,s['seconds'],sampler)
        result.update(avd=s['avd'],nested_cleanup_scope_closed=True,host_sandbox=False,
            shared_root_cap_verified=True,read_only_requested=True,headless_requested=True)
    payload=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode('utf-8')
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-android-emulator-smoke-result-v1','status':result['status'],
        'output':plan['output'],'sha256':sha,'android_boot_verified':False,'apk_execution_verified':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Emulator smoke unavailable; inspect installed SDK, dedicated AVD, Windows shared cap and host headroom'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
