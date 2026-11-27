"""Reviewed native end-to-end playability fixture for generated Godot grid games."""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.game_project_generation import checked,files
from deepthort_local.android_game_compilation import resolve_runtime,run_profile
from deepthort_local.action_guards import verify_guards
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-grid-game-end-to-end-v1'
MARKER='JANUS_GRID_E2E '
STAGES=['initial','boundary','early_goal','collect_and_win','reset','touch']

def path(start,target,w,h,walls):
    parent={start:None};q=deque([start])
    while q:
        p=q.popleft()
        if p==target:
            steps=[]
            while parent[p] is not None:
                old=parent[p];steps.append((p[0]-old[0],p[1]-old[1]));p=old
            return list(reversed(steps))
        x,y=p
        for v in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=v[0]<w and 0<=v[1]<h and v not in walls and v not in parent:parent[v]=p;q.append(v)
    raise ValueError('No playable route')

def fixture(s):
    checked(s);start=tuple(s['start']);goal=tuple(s['goal']);walls=set(map(tuple,s['walls']))
    w,h=s['width'],s['height'];items=set(map(tuple,s['collectibles']))
    # An early goal check must be meaningful. Refuse fixtures where every goal
    # route collects an item, rather than invent an observed game result.
    try:early=path(start,goal,w,h,walls|items)
    except ValueError:raise ValueError('Choose a level with a goal route avoiding collectibles')
    current=start;win=[]
    for dest in [*map(tuple,s['collectibles']),goal]:
        win.extend(path(current,dest,w,h,walls));current=dest
    if len(win)>10000:raise ValueError('Playtest route exceeds bound')
    # Test an adjacent out-of-bounds or wall movement from some reachable cell.
    blocked=None
    for p in [(x,y) for y in range(h) for x in range(w) if (x,y) not in walls]:
        for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
            n=(p[0]+dx,p[1]+dy)
            if n in walls or not (0<=n[0]<w and 0<=n[1]<h):
                try:r=path(start,p,w,h,walls|items|{goal})
                except ValueError:continue
                blocked=(r,(dx,dy));break
        if blocked:break
    if not blocked:raise ValueError('Choose a level with a reachable blocked movement')
    touch=win[0]
    def vec(p):return 'Vector2i(%d,%d)'%p
    def arr(seq):return '['+', '.join(map(vec,seq))+']'
    script='''extends SceneTree

func _initialize():
    call_deferred("run")

func fail(stage: String):
    print("JANUS_GRID_E2E " + stage + " failed")
    quit(1)

func run():
    var scene = load("res://main.tscn")
    if scene == null:
        fail("initial")
        return
    var game = scene.instantiate()
    root.add_child(game)
    await process_frame
    if game.player != %s or game.remaining.size() != %d or game.won:
        fail("initial")
        return
    print("JANUS_GRID_E2E initial passed")
    for d in %s:
        game._move(d)
    var before = game.player
    game._move(%s)
    if game.player != before:
        fail("boundary")
        return
    print("JANUS_GRID_E2E boundary passed")
    game._reset()
    for d in %s:
        game._move(d)
    if game.player != %s or game.won or game.remaining.size() != %d:
        fail("early_goal")
        return
    print("JANUS_GRID_E2E early_goal passed")
    game._reset()
    for d in %s:
        game._move(d)
    if game.player != %s or not game.won or not game.remaining.is_empty():
        fail("collect_and_win")
        return
    print("JANUS_GRID_E2E collect_and_win passed")
    game._reset()
    if game.player != %s or game.won or game.remaining.size() != %d:
        fail("reset")
        return
    print("JANUS_GRID_E2E reset passed")
    var touch_cell = game.player + %s
    var touch = InputEventScreenTouch.new()
    touch.pressed = true
    touch.position = Vector2(0,48) + (Vector2(touch_cell) + Vector2(0.5,0.5)) * %d
    game._unhandled_input(touch)
    if game.player != touch_cell:
        fail("touch")
        return
    print("JANUS_GRID_E2E touch passed")
    quit(0)
'''%(vec(start),len(items),arr(blocked[0]),vec(blocked[1]),arr(early),vec(goal),len(items),arr(win),vec(goal),vec(start),len(items),vec(touch),s['cell_size'])
    return script,{'win_steps':len(win),'early_goal_steps':len(early),'stages':STAGES.copy()}

def assess_log(text):
    found=[l[len(MARKER):] for l in text.splitlines() if l.startswith(MARKER)]
    if found!=[s+' passed' for s in STAGES] or re.search(r'(?im)^\s*(?:SCRIPT ERROR|ERROR|Parse Error):',text):
        raise ValueError('Native engine did not report all ordered successful stages')
    return {'native_gameplay_fixture_verified':True,'stages':STAGES.copy(),'visual_playtest_verified':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=2:raise ValueError('Missing runtime guard')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.json')
    if plan['guards'][1]!=resolve_runtime(root):raise ValueError('Reviewed Godot executable changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    plan['guards'].append(resolve_runtime(root))
    _,r=fixture(s)
    return plan,dict(r,scope='Generate exact grid game into temporary project and execute fixed native Godot headless scene probe under shared cap. No user-authored code or device/visual testing.')

def execute(root,plan):
    s,dst=validate(root,plan);script,r=fixture(s)
    from deepthort_local.triad_job import verify_root_cap
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    verify_root_cap();sampler=WindowsPressureSampler();_,ram=sampler.read()
    if ram is None or ram<15:raise ValueError('Insufficient RAM reserve')
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-grid-e2e-',dir=dst.parent) as tmp:
        stage=Path(tmp)/'game';stage.mkdir()
        members=files(s)
        for name,data in members.items():(stage/name).write_bytes(data)
        (stage/'probe.gd').write_text(script,encoding='utf-8')
        exe=plan['guards'][1]['path'];verify_guards(plan['guards'])
        run_profile([exe,'--headless','--path',str(stage),'--editor','--import'],stage,Path(tmp)/'import.log',90,sampler)
        log=Path(tmp)/'run.log'
        run_profile([exe,'--headless','--path',str(stage),'--script','res://probe.gd'],stage,log,90,sampler)
        raw=log.read_bytes()
        result=assess_log(raw.decode('utf-8',errors='replace'))
        result.update(r,log_sha256=hashlib.sha256(raw).hexdigest(),source_files={n:hashlib.sha256(v).hexdigest() for n,v in members.items()})
    payload=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode()
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'native_grid_fixture_passed','output':plan['output'],'sha256':sha,**result}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Native grid fixture not verified; inspect engine, resource headroom and fixture prerequisites'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
