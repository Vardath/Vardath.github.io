"""Queue-compatible reviewed execution on JANUS's existing separate Windows desktop."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import threading
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.isolated_gui import plan_isolated_gui,run_isolated_gui,MAX_RUN_SECONDS

SCHEMA='janus-background-desktop-execution-v1'
EXTRA=('executable','.exe')
def checked(s):
    if not isinstance(s,dict) or set(s)!={'executable','seconds','expected_window_title'} or not isinstance(s['executable'],str):
        raise ValueError('Choose exact executable, duration and expected window title')
    if type(s['seconds']) is not int or not 1<=s['seconds']<=MAX_RUN_SECONDS:raise ValueError('Invalid observation duration')
    t=s['expected_window_title']
    if not isinstance(t,str) or not 1<=len(t)<=160 or any(ord(c)<32 for c in t):
        raise ValueError('Choose exact expected window title')
    return s

def validate(root,plan):
    s,dst,exe=guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    native=plan_isolated_gui(root,exe,seconds=s['seconds'])
    if native.executable_sha256!=plan['guards'][1]['expected']:raise ValueError('Reviewed executable changed')
    return s,dst,native

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    validate(root,plan)
    return plan,dict(s,scope='Launch the exact trusted executable on a separate Windows desktop for a bounded observation. No foreground switch or input. The binary runs with your user rights; it may access files/network. Existing resource protections and child cleanup apply. Verify expected window title only, not rendering, gameplay or functional correctness.')

def result_for(s,r):
    checked(s)
    if not isinstance(r,dict) or r.get('shared_root_cap_verified') is not True or r.get('separate_desktop') is not True or r.get('foreground_switched') is not False:
        raise ValueError('Native background scope not established')
    status=r.get('status')
    if status not in ('window_observed','no_window','exited_nonzero','cancelled','preempted','window_hung','launch_failed'):
        raise ValueError('Unknown native result')
    windows=r.get('windows')
    if not isinstance(windows,list) or len(windows)>12 or any(not isinstance(w,dict) for w in windows):raise ValueError('Invalid observation')
    found=any(w.get('title')==s['expected_window_title'] and w.get('hung') is False for w in windows)
    return {'schema':SCHEMA,'status':status,'expected_window_observed':found and status=='window_observed',
            'window_count':len(windows),'shared_root_cap_verified':True,'separate_desktop':True,
            'foreground_switched':False,'input_sent':False,'rendering_verified':False,
            'functional_success_verified':False,'host_sandbox':False}

def execute(root,plan):
    s,dst,native=validate(root,plan)
    from deepthort_local.triad_job import verify_root_cap
    verify_root_cap()
    observation=run_isolated_gui(native,threading.Event())
    result=result_for(s,observation)
    result['executable_sha256']=native.executable_sha256
    sha=guard.publish(json.dumps(result,sort_keys=True,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'output':plan['output'],'sha256':sha,**result}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'unconfirmed','error_type':type(e).__name__,'reason':'Reviewed background execution unavailable; executable may already have run'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
