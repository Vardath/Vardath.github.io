"""Actual rendered viewport pixel checks for a reviewed generated Godot grid game."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.game_project_generation import checked,files
from deepthort_local.end_to_end_testing import path
from deepthort_local.android_game_compilation import resolve_runtime,run_profile
from deepthort_local.action_guards import verify_guards
from deepthort_local.disk_gate import require_storage
from deepthort_local.texture_pixels import decode
SCHEMA='janus-rendered-grid-playtest-v1'
PLAYER=(102,201,255)
MARKER='JANUS_GRID_VISUAL '
def movement(s):
    checked(s)
    route=path(tuple(s['start']),tuple(s['collectibles'][0]),s['width'],s['height'],set(map(tuple,s['walls'])))
    if not route:raise ValueError('No reachable movement')
    dx,dy=route[0];x,y=s['start']
    return (dx,dy),(x+dx,y+dy)

def script(s):
    delta,dest=movement(s)
    key={(-1,0):'KEY_LEFT',(1,0):'KEY_RIGHT',(0,-1):'KEY_UP',(0,1):'KEY_DOWN'}[delta]
    return '''extends SceneTree

func _initialize():
    call_deferred("run")

func snapshot(name: String):
    await process_frame
    await RenderingServer.frame_post_draw
    var image = root.get_texture().get_image()
    if image == null or image.is_empty():
        return false
    image.convert(Image.FORMAT_RGB8)
    return image.save_png("res://" + name) == OK

func run():
    if DisplayServer.get_name() == "headless":
        quit(1)
        return
    var game = load("res://main.tscn").instantiate()
    root.add_child(game)
    if not await snapshot("before.png"):
        quit(1)
        return
    print("JANUS_GRID_VISUAL before")
    var event = InputEventKey.new()
    event.keycode = %s
    event.pressed = true
    Input.parse_input_event(event)
    Input.flush_buffered_events()
    await process_frame
    event = event.duplicate()
    event.pressed = false
    Input.parse_input_event(event)
    Input.flush_buffered_events()
    if game.player != Vector2i(%d,%d):
        quit(1)
        return
    if not await snapshot("after.png"):
        quit(1)
        return
    print("JANUS_GRID_VISUAL after")
    quit(0)
'''%(key,*dest)

def inspect(s,before,after,log):
    checked(s);_,dest=movement(s)
    if [x[len(MARKER):] for x in log.splitlines() if x.startswith(MARKER)]!=['before','after'] or re.search(r'(?im)^\s*(?:SCRIPT ERROR|ERROR|Parse Error):',log):
        raise ValueError('Missing ordered native visual evidence')
    w=max(s['width']*s['cell_size'],320);h=s['height']*s['cell_size']+48
    def pixel(raw,point):
        rw,rh,_,data=decode(raw,('RGB',))
        if (rw,rh)!=(w,h):raise ValueError('Rendered viewport size mismatch')
        x=point[0]*s['cell_size']+s['cell_size']//2
        y=48+point[1]*s['cell_size']+s['cell_size']//2
        i=(y*w+x)*3
        return tuple(data[i:i+3])
    def player(p):return all(abs(a-b)<=10 for a,b in zip(p,PLAYER))
    if (before==after or not player(pixel(before,s['start'])) or player(pixel(before,dest))
        or player(pixel(after,s['start'])) or not player(pixel(after,dest))):
        raise ValueError('Rendered player movement pixel oracle failed')
    return {'schema':SCHEMA,'viewport':[w,h],'start':s['start'],'destination':list(dest),
            'rendered_pixel_movement_verified':True,'native_keyboard_event_requested':True,
            'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest(),
            'full_gameplay_verified':False,'visual_quality_verified':False,'external_game_tested':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=2:raise ValueError('Missing exact engine guard')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.zip')
    if plan['guards'][1]!=resolve_runtime(root):raise ValueError('Reviewed engine changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip')
    plan['guards'].append(resolve_runtime(root));_,dest=movement(s)
    return plan,dict(s,expected_first_move=list(dest),scope='Generate a fresh grid game and execute a fixed non-headless Godot render probe. A visible window may appear briefly; no global input. Check actual before/after viewport pixels and state after one synthetic in-engine key event. Save only generated game frames and receipt. Requires native GPU/display and engine; no arbitrary project game or overall quality claim.')

def execute(root,plan):
    s,dst=validate(root,plan)
    from deepthort_local.triad_job import verify_root_cap
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    verify_root_cap();sampler=WindowsPressureSampler();_,ram=sampler.read()
    if ram is None or ram<15:raise ValueError('Insufficient RAM reserve')
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-grid-visual-',dir=dst.parent) as tmp:
        stage=Path(tmp)/'game';stage.mkdir()
        for name,data in files(s).items():(stage/name).write_bytes(data)
        (stage/'probe.gd').write_text(script(s),encoding='utf-8')
        exe=plan['guards'][1]['path'];verify_guards(plan['guards'])
        run_profile([exe,'--headless','--path',str(stage),'--editor','--import'],stage,Path(tmp)/'import.log',90,sampler)
        log=Path(tmp)/'render.log'
        run_profile([exe,'--path',str(stage),'--rendering-method','gl_compatibility','--resolution',f"{max(s['width']*s['cell_size'],320)}x{s['height']*s['cell_size']+48}",'--script','res://probe.gd'],stage,log,60,sampler)
        before=guard.read_bound(stage/'before.png',guard.MAX_INPUT);after=guard.read_bound(stage/'after.png',guard.MAX_INPUT)
        result=inspect(s,before,after,log.read_text(encoding='utf-8',errors='replace'))
    result.update(shared_root_cap_verified=True,native_engine_invoked=True)
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_STORED) as z:
        z.writestr('before.png',before);z.writestr('after.png',after)
        z.writestr('receipt.json',json.dumps(result,sort_keys=True,indent=2))
    payload=buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or z.read('before.png')!=before or z.read('after.png')!=after or json.loads(z.read('receipt.json'))!=result:raise ValueError('Visual evidence bundle mismatch')
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'native_rendered_grid_movement_verified','output':plan['output'],'sha256':digest,**result}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Actual rendered grid evidence unavailable; check native engine, display and pixel oracle'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
