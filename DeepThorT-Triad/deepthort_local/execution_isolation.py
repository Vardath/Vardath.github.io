"""Native Windows single-process job isolation probe, not a security sandbox."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.triad_job import child_server,verify_root_cap
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-single-process-isolation-v1'
CHILD_MARKER='JANUS_CHILD_EXECUTED'
PROBE="""import subprocess,sys
try:
    p=subprocess.run([sys.executable,'-I','-B','-c','print("JANUS_CHILD_EXECUTED")'],capture_output=True,timeout=5)
except OSError:
    print('JANUS_PROCESS_LIMIT spawn_refused',flush=True)
else:
    if b'JANUS_CHILD_EXECUTED' in p.stdout or p.returncode==0:
        raise SystemExit(3)
    print('JANUS_PROCESS_LIMIT child_terminated',flush=True)
"""

def checked(s):
    if not isinstance(s,dict) or set(s)!={'probe'} or s['probe']!='single_process':
        raise ValueError('Only the fixed single-process isolation probe is supported')
    return s

def assess(baseline,restricted):
    if baseline.strip()!=CHILD_MARKER or restricted.strip() not in (
        'JANUS_PROCESS_LIMIT spawn_refused','JANUS_PROCESS_LIMIT child_terminated'):
        raise ValueError('Native process limit evidence unavailable')
    return {'schema':SCHEMA,'baseline_child_executed':True,'active_process_limit':1,
            'descendant_execution_blocked_in_probe':True,'security_sandbox':False,
            'filesystem_isolation':False,'network_isolation':False,'arbitrary_code_safe':False}

class HostPressure(ValueError):
    """Transient observed host resource pressure; never a passed fixture."""

def run(stage):
    verify_root_cap()
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    sampler=WindowsPressureSampler();_,ram=sampler.read()
    if ram is None:raise ValueError('Host RAM reading unavailable')
    if ram<15:raise HostPressure('Host free RAM below 15% admission reserve')
    exe=str(Path(sys._base_executable).resolve(strict=True))
    logs=[]
    for i,code in enumerate(('print("'+CHILD_MARKER+'")',PROBE)):
        log=stage/('probe-'+str(i)+'.log')
        with child_server([exe,'-I','-B','-c',code],stage,log,memory_limit=128*1024**2,
                          process_limit=1 if i else None) as (pid,alive):
            if not alive.member(pid):raise ValueError('Missing exact nested job membership')
            deadline=time.monotonic()+15
            while alive():
                cpu,free=sampler.read()
                if time.monotonic()>=deadline:raise ValueError('Native probe timed out')
                if log.stat().st_size>8192:raise ValueError('Native probe log exceeds bound')
                if free is None:raise ValueError('Host RAM reading unavailable')
                if free<10 or (cpu is not None and cpu>=90):
                    raise HostPressure(f'Native probe stopped: CPU busy={cpu!r}, free RAM={free:.1f}%')
                time.sleep(.1)
            if alive.code()!=0:raise ValueError('Native probe returned nonzero exit status')
        logs.append(guard.read_bound(log,8192).decode('utf-8'))
    return dict(assess(*logs),shared_root_cap_verified=True,nested_job_readback_verified=True)

def retry_native_ci(operation, *, sleep=time.sleep):
    """Retry only transient pressure, with fresh complete probes each time."""
    for attempt in range(5):
        try:return operation()
        except HostPressure:
            if attempt==4:raise
            sleep(5*(attempt+1))

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,scope='Run fixed benign native Windows Python baseline and single-process job probe; verify active-process limit and blocked descendant execution. No user code, filesystem/network security isolation or general sandbox claim.')

def execute(root,plan):
    s,dst,_=validate(root,plan);require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-isolation-',dir=dst.parent) as tmp:
        result=run(Path(tmp))
    payload=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'native_process_limit_probe_passed','output':plan['output'],'sha256':digest,**result}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root');p.add_argument('--plan');p.add_argument('--native-ci',action='store_true');p.add_argument('--inside',action='store_true');p.add_argument('--ci-receipt');a=p.parse_args()
    def report(value):
        encoded=json.dumps(value,sort_keys=True)
        if a.inside and a.ci_receipt:
            with Path(a.ci_receipt).open('a',encoding='utf8') as out:out.write(encoded+'\n')
        print(encoded,flush=True)
    try:
        if a.native_ci:
            from deepthort_local.win_cpu_cap import run_capped
            with tempfile.TemporaryDirectory(prefix='deepthortriad-native-ci-') as temp:
                receipt=Path(temp)/'diagnostic.jsonl'
                code=run_capped([sys.executable,str(Path(__file__).resolve()),'--inside','--ci-receipt',str(receipt)],cwd=str(Path(__file__).resolve().parents[1]))
                if receipt.is_file():
                    print(guard.read_bound(receipt,16384).decode('utf8'),flush=True)
                else:print('Native fixture produced no diagnostic receipt; exit code '+str(code),flush=True)
                return code
        if a.inside:
            def attempt():
                with tempfile.TemporaryDirectory(prefix='janus-native-isolation-') as tmp:
                    return run(Path(tmp))
            report(retry_native_ci(attempt) if a.ci_receipt else attempt())
        else:
            print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True)
        return 0
    except Exception as e:
        report({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:180]});return 1
if __name__=='__main__':sys.exit(main())
