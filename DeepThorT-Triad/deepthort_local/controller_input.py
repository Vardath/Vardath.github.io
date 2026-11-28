"""Reviewed synthetic controller input through native Godot's action pipeline."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.android_game_compilation import resolve_runtime,run_profile
from deepthort_local.action_guards import verify_guards
from deepthort_local.disk_gate import require_storage
SCHEMA='janus-godot-controller-fixture-v1'
BUTTONS={'A':0,'B':1,'X':2,'Y':3,'DPAD_UP':11,'DPAD_DOWN':12,'DPAD_LEFT':13,'DPAD_RIGHT':14}
AXES={'LEFT_X':0,'LEFT_Y':1,'RIGHT_X':2,'RIGHT_Y':3}
MARKER='JANUS_CONTROLLER '

def checked(s):
    if not isinstance(s,dict) or set(s)!={'actions'} or not isinstance(s['actions'],list) or not 1<=len(s['actions'])<=12:
        raise ValueError('Choose 1–12 controller actions')
    for a in s['actions']:
        if not isinstance(a,dict) or a.get('kind') not in ('button','axis'):raise ValueError('Invalid controller action')
        if a['kind']=='button':
            if set(a)!={'kind','button'} or not isinstance(a['button'],str) or a['button'] not in BUTTONS:raise ValueError('Unsupported controller button')
        elif set(a)!={'kind','axis','direction'} or not isinstance(a['axis'],str) or a['axis'] not in AXES or type(a['direction']) is not int or a['direction'] not in (-1,1):
            raise ValueError('Choose named axis and direction -1 or 1')
    return s

def script(s):
    checked(s);parts=['extends SceneTree','','func _initialize():','    call_deferred("run")','','func run():']
    for i,a in enumerate(s['actions']):
        name=f'janus_controller_{i}';kind=a['kind']
        parts += [f'    InputMap.add_action("{name}", 0.2)']
        if kind=='button':
            parts += [f'    var event_{i} = InputEventJoypadButton.new()',f'    event_{i}.button_index = {BUTTONS[a["button"]]}',f'    event_{i}.pressed = true']
        else:
            parts += [f'    var event_{i} = InputEventJoypadMotion.new()',f'    event_{i}.axis = {AXES[a["axis"]]}',f'    event_{i}.axis_value = {a["direction"]}.0']
        parts += [f'    event_{i}.device = 0',f'    InputMap.action_add_event("{name}", event_{i})',
                  f'    Input.parse_input_event(event_{i})','    Input.flush_buffered_events()','    await process_frame',
                  f'    if not Input.is_action_pressed("{name}"):',f'        print("{MARKER}{i} press failed")','        quit(1)','        return']
        parts += [f'    var release_{i} = event_{i}.duplicate()',
                  f'    release_{i}.'+('pressed = false' if kind=='button' else 'axis_value = 0.0'),
                  f'    Input.parse_input_event(release_{i})','    Input.flush_buffered_events()','    await process_frame',
                  f'    if Input.is_action_pressed("{name}"):',f'        print("{MARKER}{i} release failed")','        quit(1)','        return',
                  f'    print("{MARKER}{i} passed")',f'    InputMap.erase_action("{name}")']
    return '\n'.join(parts+['    quit(0)',''])

def assess(s,log):
    checked(s)
    if not isinstance(log,str) or len(log)>1024*1024:raise ValueError('Invalid engine evidence')
    if [x[len(MARKER):] for x in log.splitlines() if x.startswith(MARKER)]!=[f'{i} passed' for i in range(len(s['actions']))] or re.search(r'(?im)^\s*(?:SCRIPT ERROR|ERROR|Parse Error):',log):
        raise ValueError('Controller action oracle did not pass')
    return {'actions_verified':len(s['actions']),'engine_action_press_release_verified':True,
            'physical_controller_used':False,'os_virtual_controller_created':False,'external_game_controlled':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=2:raise ValueError('Missing exact engine guard')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.json')
    if plan['guards'][1]!=resolve_runtime(root):raise ValueError('Reviewed Godot runtime changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    plan['guards'].append(resolve_runtime(root))
    return plan,dict(s,scope='Run fixed host-generated Godot headless controller-event fixture under shared Windows cap; verify action press/release. No physical controller, OS driver, external game, global input or arbitrary project script.')

def execute(root,plan):
    s,dst=validate(root,plan)
    from deepthort_local.triad_job import verify_root_cap
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    verify_root_cap();sampler=WindowsPressureSampler();_,ram=sampler.read()
    if ram is None or ram<15:raise ValueError('Insufficient RAM reserve')
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-controller-',dir=dst.parent) as tmp:
        stage=Path(tmp);(stage/'project.godot').write_text('config_version=5\n[application]\nconfig/name="JANUS Controller Fixture"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n',encoding='utf-8')
        probe=script(s);(stage/'probe.gd').write_text(probe,encoding='utf-8')
        log=stage/'run.log';verify_guards(plan['guards'])
        run_profile([plan['guards'][1]['path'],'--headless','--path',str(stage),'--script','res://probe.gd'],stage,log,60,sampler)
        raw=log.read_bytes();r=assess(s,raw.decode('utf-8',errors='replace'))
        r.update(schema=SCHEMA,script_sha256=hashlib.sha256(probe.encode()).hexdigest(),log_sha256=hashlib.sha256(raw).hexdigest(),shared_root_cap_verified=True)
    digest=guard.publish(json.dumps(r,sort_keys=True,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'native_controller_fixture_verified','output':plan['output'],'sha256':digest,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Native Godot controller input fixture not verified'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
