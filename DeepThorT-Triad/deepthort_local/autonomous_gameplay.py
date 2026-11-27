"""Bounded autonomous route selection and native keyboard play of generated grid games."""
from __future__ import annotations
import hashlib
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local.end_to_end_testing import path
import argparse
from collections import deque
import hashlib
import json
import re
import tempfile
from deepthort_local import typed_project_tool as guard
from deepthort_local.game_project_generation import checked,files
from deepthort_local.android_game_compilation import resolve_runtime,run_profile
from deepthort_local.action_guards import verify_guards
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-autonomous-grid-play-v1'
MARKER='JANUS_AUTO_PLAY '
KEYS={(-1,0):'KEY_LEFT',(1,0):'KEY_RIGHT',(0,-1):'KEY_UP',(0,1):'KEY_DOWN'}
MAX_STEPS=512

def route(s):
    checked(s)
    p=tuple(s['start']);goal=tuple(s['goal']);remaining=set(map(tuple,s['collectibles']))
    walls=set(map(tuple,s['walls']));w,h=s['width'],s['height'];trace=[]
    while remaining or p!=goal:
        targets=sorted(remaining) if remaining else [goal]
        candidates=[(path(p,t,w,h,walls),t) for t in targets]
        moves,_=min(candidates,key=lambda row:(len(row[0]),row[1]))
        for dx,dy in moves:
            p=(p[0]+dx,p[1]+dy);remaining.discard(p)
            trace.append((KEYS[(dx,dy)],p,len(remaining),p==goal and not remaining))
            if len(trace)>MAX_STEPS:raise ValueError('Autonomous route exceeds bounded native input budget')
            if trace[-1][3]:return trace
    raise ValueError('Route did not reach the game objective')

def expected(s):
    return [f'{i} {p[0]} {p[1]} {n} {int(won)}' for i,(_,p,n,won) in enumerate(route(s),1)]

def fixture(s):
    trace=route(s)
    keys=', '.join(row[0] for row in trace)
    script='''extends SceneTree

func _initialize():
    call_deferred("run")

func run():
    var game = load("res://main.tscn").instantiate()
    root.add_child(game)
    await process_frame
    var step := 0
    for key in [%s]:
        var event = InputEventKey.new()
        event.keycode = key
        event.pressed = true
        Input.parse_input_event(event)
        Input.flush_buffered_events()
        await process_frame
        var released = InputEventKey.new()
        released.keycode = key
        released.pressed = false
        Input.parse_input_event(released)
        Input.flush_buffered_events()
        step += 1
        print("JANUS_AUTO_PLAY %%d %%d %%d %%d %%d" %% [step, game.player.x, game.player.y, game.remaining.size(), int(game.won)])
    if not game.won or not game.remaining.is_empty():
        quit(1)
        return
    quit(0)
'''%keys
    return script,{'input_steps':len(trace),'route_policy':'nearest reachable remaining collectible, then goal'}

def assess_log(s,text):
    found=[l[len(MARKER):] for l in text.splitlines() if l.startswith(MARKER)]
    if found!=expected(s) or re.search(r'(?im)^\s*(?:SCRIPT ERROR|ERROR|Parse Error):',text):
        raise ValueError('Native keyboard trajectory did not match expected objective progression')
    return {'native_grid_objective_verified':True,'native_input_trace':found,
            'external_game_tested':False,'visual_playtest_verified':False,'general_game_agent_verified':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=2:raise ValueError('Missing runtime guard')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.json')
    if plan['guards'][1]!=resolve_runtime(root):raise ValueError('Reviewed Godot executable changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    plan['guards'].append(resolve_runtime(root))
    _,r=fixture(s)
    return plan,dict(r,scope='Generate exact grid game and autonomously choose a bounded route; run native headless keyboard events and verify every observed position, remaining item count and victory. No external game, global input, or general agent claim.')

def execute(root,plan):
    s,dst=validate(root,plan);script,r=fixture(s)
    from deepthort_local.triad_job import verify_root_cap
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    verify_root_cap();sampler=WindowsPressureSampler();_,ram=sampler.read()
    if ram is None or ram<15:raise ValueError('Insufficient RAM reserve')
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-auto-play-',dir=dst.parent) as tmp:
        stage=Path(tmp)/'game';stage.mkdir()
        members=files(s)
        for name,data in members.items():(stage/name).write_bytes(data)
        (stage/'probe.gd').write_text(script,encoding='utf-8')
        exe=plan['guards'][1]['path'];verify_guards(plan['guards'])
        run_profile([exe,'--headless','--path',str(stage),'--editor','--import'],stage,Path(tmp)/'import.log',90,sampler)
        log=Path(tmp)/'run.log'
        run_profile([exe,'--headless','--path',str(stage),'--script','res://probe.gd'],stage,log,90,sampler)
        raw=log.read_bytes()
        result=assess_log(s,raw.decode('utf-8',errors='replace'))
        result.update(r,log_sha256=hashlib.sha256(raw).hexdigest(),source_files={n:hashlib.sha256(v).hexdigest() for n,v in members.items()})
    payload=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode()
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'native_autonomous_grid_play_passed','output':plan['output'],'sha256':sha,**result}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Native autonomous keyboard play not verified; inspect engine, resource headroom and trajectory'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
