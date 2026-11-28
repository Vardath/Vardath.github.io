"""Explicit bounded live screen sampling and local visual caption evidence."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.screen_capture import region,primary_size,capture
from deepthort_local.video_interpretation import captions
from deepthort_local.triad_profiles import ROOT
SCHEMA='janus-bounded-live-screen-v1'

def checked(s):
    if not isinstance(s,dict) or set(s)!={'region','samples','interval_seconds'}:
        raise ValueError('Choose exact primary screen region, samples and interval')
    region(s['region'],(8192,8192))
    if type(s['samples']) is not int or not 2<=s['samples']<=4:raise ValueError('Choose 2–4 samples')
    if type(s['interval_seconds']) is not int or not 1<=s['interval_seconds']<=5:raise ValueError('Choose 1–5 seconds between samples')
    return s

def runtime(root):
    node=shutil.which('node')
    if not node:raise ValueError('Local vision runtime unavailable')
    node=Path(node).resolve(strict=True);script=(ROOT/'vision_caption.mjs').resolve(strict=True)
    if any(x.is_relative_to(Path(root).resolve()) for x in (node,script)):raise ValueError('Project-local vision runtime refused')
    return [snapshot_file(node,kind='stat'),snapshot_file(script)]

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=3:
        raise ValueError('Missing reviewed vision runtime')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.json')
    if plan['guards'][1:]!=runtime(root):raise ValueError('Reviewed vision runtime changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    plan['guards'].extend(runtime(root))
    return plan,dict(s,scope='After a separate visible local confirmation and three-second countdown, capture only the exact primary-screen rectangle 2–4 times. Close sensitive windows first. Local offline Florence model receives these samples; the new JSON retains captions and hashes, not screenshots. Temporary images outside the project are deleted normally. No cloud, ongoing capture, memory ingestion, input, or semantic accuracy claim.')

def samples(s,screen,folder,*,approved=False,screen_size=primary_size,capture_fn=capture,clock=time.monotonic,sleep=time.sleep,stopped=lambda:False):
    checked(s)
    if approved is not True:raise PermissionError('Explicit live screen approval required')
    box=region(s['region'],screen);start=clock();paths=[];rows=[]
    for i in range(s['samples']):
        due=start+i*s['interval_seconds']
        while clock()<due:
            if stopped():raise ValueError('Capture stopped')
            sleep(min(.1,max(0,due-clock())))
        if stopped() or screen_size()!=screen:raise ValueError('Capture stopped or display changed')
        raw=capture_fn(box,screen,approved=True)
        from deepthort_local.texture_pixels import decode
        w,h,_,_=decode(raw,('RGB',))
        if (w,h)!=tuple(box[2:]):raise ValueError('Captured region mismatch')
        path=Path(folder)/f'sample-{i}.png';path.write_bytes(raw)
        paths.append(path);rows.append({'sample':i,'elapsed_seconds':round(clock()-start,3),'sha256':hashlib.sha256(raw).hexdigest()})
    return paths,rows

def interpret(paths,rows,tools,*,captioner=captions):
    values=captioner(paths,tools)
    if not isinstance(values,list) or len(values)!=len(rows):raise ValueError('Missing sampled captions')
    result=[]
    for p,row,value in zip(paths,rows,values):
        if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Sample changed')
        if not isinstance(value,str) or not value.strip() or len(value)>2000 or any(ord(c)<32 and c not in '\n\t' for c in value):
            raise ValueError('Invalid vision observation')
        result.append(dict(row,caption=value))
    return result

def confirm(s,screen):
    import tkinter as tk
    from tkinter import ttk
    win=tk.Tk();win.title('JANUS live screen sampling');win.geometry('640x220')
    accepted=[False]
    ttk.Label(win,text=f"Region {s['region']} on primary display {screen}. {s['samples']} samples, {s['interval_seconds']} seconds apart. Close sensitive windows. Local vision will see these images.",wraplength=600).pack(padx=12,pady=16)
    def approve():accepted[0]=True;win.destroy()
    ttk.Button(win,text='Approve capture + local interpretation',command=approve).pack(pady=5)
    ttk.Button(win,text='Cancel',command=win.destroy).pack(pady=5)
    win.after(60000,win.destroy);win.mainloop()
    if not accepted[0]:raise PermissionError('Live capture not approved')

def execute(root,plan):
    s,dst=validate(root,plan)
    from deepthort_local.triad_job import verify_root_cap
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    from deepthort_local.disk_gate import require_storage
    verify_root_cap();screen=primary_size();region(s['region'],screen);sampler=WindowsPressureSampler()
    def stopped():
        cpu,ram=sampler.read()
        return ram is None or ram<10 or (cpu is not None and cpu>=90)
    if stopped():raise ValueError('Resource reserve unavailable')
    confirm(s,screen)
    time.sleep(3);validate(root,plan)
    require_storage(Path(tempfile.gettempdir()))
    with tempfile.TemporaryDirectory(prefix='janus-live-screen-') as tmp:
        paths,rows=samples(s,screen,tmp,approved=True,stopped=stopped)
        if stopped():raise ValueError('Vision resource reserve unavailable')
        verify_guards(plan['guards'])
        observations=interpret(paths,rows,plan['guards'][1:])
    r={'schema':SCHEMA,'region':s['region'],'observations':observations,'caption_model':'Florence-2-base-ft (local)',
       'continuous_monitoring':False,'screenshots_retained_in_project':False,'semantic_accuracy_verified':False,
       'input_sent':False,'reference_only':True,'shared_root_cap_verified':True}
    digest=guard.publish(json.dumps(r,ensure_ascii=True,sort_keys=True,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'sampled_live_screen_observations','output':plan['output'],'sha256':digest,'samples':len(observations),'semantic_accuracy_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Reviewed live screen sampling unavailable; check local vision, display and resources'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
