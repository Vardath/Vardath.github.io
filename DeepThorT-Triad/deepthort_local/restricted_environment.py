"""Reviewed Python syntax checking in a constrained, clean-environment Windows child."""
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
from deepthort_local.triad_job import child_server,verify_root_cap,isolated_env
from deepthort_local.disk_gate import require_storage
from deepthort_local.execution_isolation import HostPressure,retry_native_ci

SCHEMA='janus-restricted-python-check-v1'
EXTRA=('document','.py')
MAX_SOURCE=120000
PROBE="""import ast,hashlib,json,os,sys
from pathlib import Path
p=Path('reviewed.py')
raw=p.read_bytes()
result={'sha256':hashlib.sha256(raw).hexdigest(),'environment_keys':sorted(os.environ),'isolated':bool(sys.flags.isolated),'no_site':bool(sys.flags.no_site),'cwd':os.getcwd()}
try:
    compile(raw,'reviewed.py','exec',dont_inherit=True)
    result.update(syntax_valid=True,error_line=None)
except SyntaxError as e:
    result.update(syntax_valid=False,error_line=e.lineno)
print(json.dumps(result,sort_keys=True),flush=True)
"""

def checked(s):
    if not isinstance(s,dict) or set(s)!={'document'} or not isinstance(s['document'],str):
        raise ValueError('Choose one project-relative Python source')
    return s

def assess(raw,observed,stage,expected_keys):
    keys={'sha256','environment_keys','isolated','no_site','cwd','syntax_valid','error_line'}
    if not isinstance(observed,dict) or set(observed)!=keys:
        raise ValueError('Unexpected native worker receipt')
    actual=observed['environment_keys']
    if (not isinstance(actual,list) or any(not isinstance(x,str) for x in actual)
        or len(actual)!=len(expected_keys) or {x.upper() for x in actual}!={x.upper() for x in expected_keys}
        or observed['isolated'] is not True or observed['no_site'] is not True
        or not isinstance(observed['cwd'],str) or Path(observed['cwd']).resolve()!=stage.resolve()
        or observed['sha256']!=hashlib.sha256(raw).hexdigest() or type(observed['syntax_valid']) is not bool):
        raise ValueError('Native environment or source identity mismatch')
    line=observed['error_line']
    if (observed['syntax_valid'] and line is not None) or (not observed['syntax_valid'] and (type(line) is not int or line<1)):
        raise ValueError('Invalid syntax evidence')
    return {'schema':SCHEMA,'source_sha256':observed['sha256'],'syntax_valid':observed['syntax_valid'],
            'error_line':line,'clean_environment_verified':True,'isolated_python_flags_verified':True,
            'project_code_executed':False,'security_sandbox':False,'filesystem_isolation':False,'network_isolation':False}

def run(raw,stage):
    if not isinstance(raw,bytes) or not 1<=len(raw)<=MAX_SOURCE:raise ValueError('Source exceeds bound')
    verify_root_cap()
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    sampler=WindowsPressureSampler();_,free=sampler.read()
    if free is None:raise ValueError('Host RAM reading unavailable')
    if free<15:raise HostPressure('Host free RAM below 15% admission reserve')
    (stage/'reviewed.py').write_bytes(raw);log=stage/'worker.log'
    expected=isolated_env(stage)
    exe=str(Path(sys._base_executable).resolve(strict=True))
    with child_server([exe,'-I','-S','-B','-c',PROBE],stage,log,memory_limit=128*1024**2,
                      process_limit=1,clean_environment=True) as (pid,alive):
        if not alive.member(pid):raise ValueError('Missing nested job membership')
        deadline=time.monotonic()+15
        while alive():
            cpu,free=sampler.read()
            if time.monotonic()>=deadline:raise ValueError('Restricted worker timed out')
            if log.stat().st_size>8192:raise ValueError('Restricted worker log exceeds bound')
            if free is None:raise ValueError('Host RAM reading unavailable')
            if free<10 or (cpu is not None and cpu>=90):
                raise HostPressure(f'Restricted worker stopped: CPU busy={cpu!r}, free RAM={free:.1f}%')
            time.sleep(.1)
        if alive.code()!=0:raise ValueError('Restricted worker failed')
    observed=json.loads(guard.read_bound(log,8192).decode('utf-8'))
    return dict(assess(raw,observed,stage,expected),shared_root_cap_verified=True,active_process_limit=1)

def validate(root,plan):
    s,dst,src=guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    if src.stat().st_size>MAX_SOURCE:raise ValueError('Source exceeds bound')
    return s,dst,src

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    validate(root,plan)
    return plan,dict(s,scope='Stage exact reviewed Python bytes into temporary directory; compile for syntax only using fixed trusted worker under clean allowlisted environment, single-process and 128 MiB nested commit limits. No source execution, imports from project, or security sandbox.')

def execute(root,plan):
    s,dst,src=validate(root,plan);raw=guard.exact(src,plan['guards'][1],MAX_SOURCE);require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-restricted-',dir=dst.parent) as tmp:result=run(raw,Path(tmp))
    digest=guard.publish((json.dumps(result,indent=2,sort_keys=True)+'\n').encode(),dst,lambda:validate(root,plan))
    return {'status':'restricted_syntax_check_completed','output':plan['output'],'sha256':digest,**result}

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
            for raw,wanted in ((b'raise RuntimeError("must not execute")\n',True),(b'def broken(:\n',False)):
                def attempt():
                    with tempfile.TemporaryDirectory(prefix='janus-native-restricted-') as tmp:
                        return run(raw,Path(tmp))
                result=retry_native_ci(attempt) if a.ci_receipt else attempt()
                if result['syntax_valid'] is not wanted:raise ValueError('Native syntax verdict mismatch')
                report(result)
        else:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True)
        return 0
    except Exception as e:
        report({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:180]});return 1
if __name__=='__main__':sys.exit(main())
