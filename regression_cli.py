"""Run DeepThorT regression modules in isolated subprocesses.

Prevents stale Tkinter background callbacks from contaminating the next test
module. Reports failures instead of hiding intermittent GUI teardown bugs.
No model inference, project write, or network operation is performed here.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import re
import shutil
import subprocess
import sys
from pathlib import Path



def run_isolated(cmd, *, cwd, env, timeout):
    """Run one module in a new process group, killing its *children* on timeout.

    On Linux xvfb-run spawns Xvfb and possibly desktop helper processes. Killing
    only the wrapper can leave descendants holding stdout pipes, defeating a
    normal `subprocess.run(timeout=...)` and hanging the whole regression suite.
    """
    opts = ({'start_new_session':True} if os.name!='nt' else
            {'creationflags':getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0)})
    proc=subprocess.Popen(cmd,cwd=cwd,env=env,text=True,encoding='utf-8',
            errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT,**opts)
    try:
        stdout, _ = proc.communicate(timeout=timeout)
        return proc.returncode,stdout,False
    except subprocess.TimeoutExpired:
        if os.name!='nt':
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        else:
            # taskkill /T is Windows's standard child-tree termination route.
            # This is only the isolated test subprocess, never an app/game.
            try:subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],
                    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                    timeout=5,check=False)
            except (OSError,subprocess.TimeoutExpired):pass
        if proc.poll() is None:proc.kill()
        try:
            stdout, _ = proc.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            stdout='[Timed-out test process retained a pipe unexpectedly]'
        return proc.returncode, stdout, True


def main(argv=None) -> int:
    ap=argparse.ArgumentParser(description='Run local DeepThorT tests in isolated modules')
    ap.add_argument('--report',default='',help='Optional JSON result file')
    ap.add_argument('--timeout',type=int,default=180,help='Per-module timeout in seconds')
    args=ap.parse_args(argv)
    if not 15<=args.timeout<=900:
        ap.error('timeout must be 15..900 seconds')
    root=Path(__file__).resolve().parent
    modules=sorted('tests.'+p.stem for p in (root/'tests').glob('test_*.py'))
    if not modules:
        print('No test modules found',file=sys.stderr)
        return 2
    result=[]
    total=0
    env=os.environ.copy()
    env['PYTHONPATH']=str(root)+os.pathsep+str(root/'tests')+os.pathsep+env.get('PYTHONPATH','')
    env['PYTHONWARNINGS']='ignore::ResourceWarning'
    for module in modules:
        cmd=[sys.executable,'-m','unittest','-q',module]
        # CI often inherits a stale DISPLAY (for example :0 with no X server).
        # Always supply a fresh isolated virtual display when available.
        if os.name!='nt' and shutil.which('xvfb-run'):
            cmd=['xvfb-run','-a',*cmd]
        try:
            code, output, timed_out=run_isolated(cmd,cwd=root,env=env,timeout=args.timeout)
            m=re.search(r'Ran\s+(\d+)\s+tests?',output)
            count=int(m.group(1)) if m else 0
            success=(not timed_out and code==0 and count>0 and re.search(r'\bOK\b',output) is not None)
            excerpt=(f'Module timed out at {args.timeout}s; process group killed\n'
                     if timed_out else '')+(output[-2600:] if not success else '')
        except OSError as exc:
            count=0;success=False;excerpt='Could not launch module: '+str(exc)[:500]
        total+=count
        result.append({'module':module,'tests':count,'passed':success,'error_tail':excerpt})
        print(f'{"PASS" if success else "FAIL"} {module} ({count} tests)',flush=True)
    summary={'modules':len(modules),'tests_run':total,'passed_modules':sum(r['passed'] for r in result),
             'failed_modules':[r['module'] for r in result if not r['passed']], 'results':result}
    if args.report:
        path=Path(args.report)
        path.write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(f"RESULT: {summary['passed_modules']}/{len(modules)} modules; {total} tests observed")
    if summary['failed_modules']:
        print('Failing modules: '+', '.join(summary['failed_modules']),file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
