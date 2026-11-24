"""Fixed Godot 4 project scene integration profile and bounded input snapshot.

Unlike an editor-load test this asks the engine to instantiate the declared
scene and process frames. It executes project code, not a sandbox.
"""
from __future__ import annotations
import os
import re
import json
from pathlib import Path
from .quiet_playtest import plan_godot_scene
from .workspace import safe_target
from .action_guards import snapshot_file
from .tool_workflows import digest

SCRIPT=Path(__file__).resolve().parent/'asset_probes'/'project_scene_probe.gd'
FRAMES=12
MAX_FILES=256
MAX_TOTAL=128_000_000
MARKER='DEEPTHORT_SCENE_PROBE '
SKIP={'.godot','.git','.venv','__pycache__','node_modules'}

def command(project,exe):
    p=plan_godot_scene(project,exe)
    if not p.main_scene.startswith('res://') or not p.main_scene.lower().endswith('.tscn'):
        raise ValueError('Scene integration requires a declared local text scene')
    safe_target(p.project,p.main_scene[6:],must_exist=True)
    if not SCRIPT.is_file():raise ValueError('Bundled scene probe missing')
    return [p.argv[0],'--headless','--path',p.project,'--script',str(SCRIPT),
            '--quit-after','360','--',p.main_scene]

def is_profile(argv):
    return (isinstance(argv,list) and len(argv)==10 and argv[1:3]==['--headless','--path']
            and argv[4:9]==['--script',str(SCRIPT),'--quit-after','360','--'])

def recognized(argv,project):
    try:return is_profile(argv) and argv==command(project,argv[0])
    except (ValueError,OSError,TypeError):return False

def inputs(project,argv):
    root=Path(project).resolve(strict=True)
    if not recognized(argv,root):raise ValueError('Not the fixed scene integration profile')
    files={};total=0
    for parent,dirs,names in os.walk(root,followlinks=False):
        dirs[:]=sorted(d for d in dirs if d not in SKIP)
        for d in dirs:
            if (Path(parent)/d).is_symlink():raise ValueError('Linked project directory not covered by scene probe')
        for name in sorted(names):
            if name.startswith('.'):continue
            path=Path(parent)/name
            relative=path.relative_to(root).as_posix()
            target=safe_target(root,relative,must_exist=True)
            total+=target.stat().st_size
            if len(files)>=MAX_FILES or total>MAX_TOTAL:raise ValueError('Scene integration input scope exceeds bound')
            files[relative]=snapshot_file(target)['expected']
    return {'files':files,'exe':snapshot_file(argv[0],kind='stat'),
            'script':snapshot_file(SCRIPT),'argv':argv}

def current(project,record):
    try:return isinstance(record,dict) and inputs(project,record['argv'])==record
    except (ValueError,OSError,KeyError,TypeError):return False

def assess(argv,lines):
    matches=[line[len(MARKER):] for line in lines.splitlines() if line.startswith(MARKER)]
    if len(matches)!=1:raise ValueError('No unique scene instantiation result')
    result=json.loads(matches[0])
    if (not isinstance(result,dict) or set(result)!={'scene','nodes','frames'}
        or result['scene']!=argv[-1] or type(result['nodes']) is not int or not 1<=result['nodes']<=100000
        or type(result['frames']) is not int or result['frames']!=FRAMES):
        raise ValueError('Scene probe did not establish expected scene and frame count')
    return result

def engine_errors(lines):
    return bool(re.search(r'(?im)^(?:\s*(?:SCRIPT ERROR|ERROR|Parse Error|Failed loading resource|Failed to load resource):)',lines))
