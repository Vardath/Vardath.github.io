"""Reviewed editable Godot 4 grid-game scaffold with reachable objective validation."""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard

SCHEMA='janus-godot-grid-project-v1'

def checked(s):
    if not isinstance(s,dict) or set(s)!={'title','width','height','cell_size','start','goal','walls','collectibles'}:
        raise ValueError('Expected title, grid, start, goal, walls and collectibles')
    if not isinstance(s['title'],str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._-]{0,79}',s['title']):
        raise ValueError('Choose a bounded simple title')
    w,h,c=(s[k] for k in ('width','height','cell_size'))
    if any(type(v) is not int for v in (w,h,c)) or not 5<=w<=32 or not 5<=h<=24 or c not in (24,32,40) or w*c>1280 or h*c+48>960:
        raise ValueError('Grid outside bounded viewport')
    def point(v):
        if not isinstance(v,list) or len(v)!=2 or any(type(x) is not int for x in v) or not 0<=v[0]<w or not 0<=v[1]<h:
            raise ValueError('Grid point outside level')
        return tuple(v)
    start=point(s['start']);goal=point(s['goal'])
    if not isinstance(s['walls'],list) or len(s['walls'])>w*h or not isinstance(s['collectibles'],list) or not 1<=len(s['collectibles'])<=32:
        raise ValueError('Invalid obstacle or collectible counts')
    walls=[point(v) for v in s['walls']];items=[point(v) for v in s['collectibles']]
    occupied=[start,goal,*walls,*items]
    if len(set(occupied))!=len(occupied):raise ValueError('Grid objects must occupy distinct cells')
    blocked=set(walls);seen={start};q=deque([start])
    while q:
        x,y=q.popleft()
        for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=p[0]<w and 0<=p[1]<h and p not in blocked and p not in seen:
                seen.add(p);q.append(p)
    if not {goal,*items}<=seen:raise ValueError('Goal and every collectible must be reachable')
    return s

def vec(v):return 'Vector2i(%d, %d)'%tuple(v)
def vectors(v):return '['+', '.join(map(vec,v))+']'

def files(s):
    checked(s);w,h,c=(s[k] for k in ('width','height','cell_size'))
    config='''; Generated reviewed Godot 4 grid game.
config_version=5

[application]
config/name="%s"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.0", "GL Compatibility")

[display]
window/size/viewport_width=%d
window/size/viewport_height=%d
window/stretch/mode="canvas_items"

[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
'''%(s['title'],max(w*c,320),h*c+48)
    scene='''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://game.gd" id="1"]

[node name="GridGame" type="Node2D"]
script = ExtResource("1")
'''
    script='''extends Node2D

const GRID = Vector2i(%d, %d)
const CELL = %d
const ORIGIN = Vector2(0, 48)
const START = %s
const GOAL = %s
const WALLS = %s
const ITEMS = %s
var player: Vector2i = START
var remaining: Array = ITEMS.duplicate()
var won := false

func _ready() -> void:
    queue_redraw()

func _move(delta: Vector2i) -> void:
    if won:
        return
    var next_cell := player + delta
    if next_cell.x < 0 or next_cell.y < 0 or next_cell.x >= GRID.x or next_cell.y >= GRID.y or next_cell in WALLS:
        return
    player = next_cell
    remaining.erase(player)
    won = player == GOAL and remaining.is_empty()
    queue_redraw()

func _reset() -> void:
    player = START
    remaining = ITEMS.duplicate()
    won = false
    queue_redraw()

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventKey and event.pressed and not event.echo:
        match event.keycode:
            KEY_UP, KEY_W: _move(Vector2i.UP)
            KEY_DOWN, KEY_S: _move(Vector2i.DOWN)
            KEY_LEFT, KEY_A: _move(Vector2i.LEFT)
            KEY_RIGHT, KEY_D: _move(Vector2i.RIGHT)
            KEY_R: _reset()
    elif event is InputEventScreenTouch and event.pressed:
        _tap(event.position)
    elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
        _tap(event.position)

func _tap(position: Vector2) -> void:
    if won and position.y < ORIGIN.y:
        _reset()
        return
    if position.y < ORIGIN.y:
        return
    var p := Vector2i(floori((position.x - ORIGIN.x) / CELL), floori((position.y - ORIGIN.y) / CELL))
    var delta := p - player
    if absi(delta.x) + absi(delta.y) == 1:
        _move(delta)

func _rect(p: Vector2i) -> Rect2:
    return Rect2(ORIGIN + Vector2(p) * CELL, Vector2(CELL, CELL))

func _draw() -> void:
    draw_rect(Rect2(Vector2.ZERO, get_viewport_rect().size), Color("#17212c"))
    for y in range(GRID.y):
        for x in range(GRID.x):
            var r := _rect(Vector2i(x, y))
            draw_rect(r.grow(-1), Color("#293d50"))
    for p in WALLS:
        draw_rect(_rect(p).grow(-2), Color("#788493"))
    draw_rect(_rect(GOAL).grow(-3), Color("#59b982") if remaining.is_empty() else Color("#a36d4b"))
    for p in remaining:
        draw_circle(_rect(p).get_center(), CELL * 0.22, Color("#f0cc67"))
    draw_circle(_rect(player).get_center(), CELL * 0.32, Color("#66c9ff"))
    var text := "Collected %%d/%%d | R: restart" %% [ITEMS.size() - remaining.size(), ITEMS.size()]
    if won:
        text = "Complete! R or tap header to restart"
    draw_string(ThemeDB.fallback_font, Vector2(8, 30), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
'''%(w,h,c,vec(s['start']),vec(s['goal']),vectors(s['walls']),vectors(s['collectibles']))
    instructions='Open project.godot in Godot 4. Run the main scene. Move with WASD/arrows or tap adjacent squares. Collect every item, then reach the goal. R resets; tap the header to reset after winning. Source scaffold only; engine, export and visual acceptance are separate.\n'
    spec=json.dumps(s,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    return {k:v.encode('utf-8') for k,v in {'project.godot':config,'main.tscn':scene,'game.gd':script,'README.txt':instructions,'level.json':spec}.items()}

def generate(s):
    data=files(s);out=io.BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,raw in sorted(data.items()):
            entry=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(entry,raw)
    payload=out.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or sorted(z.namelist())!=sorted(data) or any(z.read(k)!=v for k,v in data.items()):
            raise ValueError('Project archive verification failed')
    return payload,{'files':{k:hashlib.sha256(v).hexdigest() for k,v in data.items()},
        'all_objectives_reachable':True,'engine_executed':False,'visual_playtest_verified':False,'android_exported':False}

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.zip')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip')
    return plan,dict(s,files=list(files(s)),scope='Editable Godot 4 grid game source archive; no extraction, engine execution or export.')

def execute(root,plan):
    s,dst,_=validate(root,plan);payload,r=generate(s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-godot-grid-project-result-v1','status':'editable_game_source_generated','output':plan['output'],
            'sha256':sha,'source_unchanged':True,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed grid-game specification or output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
