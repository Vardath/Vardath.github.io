"""Reviewed native Unreal Editor Python commandlet integration fixture."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.android_emulator import real_file
from deepthort_local.android_game_compilation import run_profile
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-unreal-editor-probe-v1'
MARKER='JANUS_UE_EDITOR_PROBE '
SCRIPT='''import unreal
import json
from pathlib import Path
version = unreal.SystemLibrary.get_engine_version()
project = unreal.Paths.get_project_file_path()
data = {"engine_version": str(version), "project_file": str(project)}
Path(__file__).with_name("result.json").write_text(json.dumps(data), encoding="utf-8")
unreal.log("JANUS_UE_EDITOR_PROBE " + str(version))
'''

def checked(s):
    if not isinstance(s,dict) or set(s)!={'project_name'} or not isinstance(s['project_name'],str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,39}',s['project_name']):
        raise ValueError('Expected a simple Unreal project_name')
    return s

def descriptor(s):
    checked(s)
    return {'FileVersion':3,'Category':'','Description':'JANUS temporary editor integration probe',
            'Plugins':[{'Name':'PythonScriptPlugin','Enabled':True}]}

def resolve_runtime(root):
    value=os.environ.get('UNREAL_EDITOR_CMD')
    if not value:raise ValueError('Set UNREAL_EDITOR_CMD to trusted installed UnrealEditor-Cmd.exe')
    exe=real_file(value)
    if exe.name.casefold()!='unrealeditor-cmd.exe' or exe.is_relative_to(Path(root).resolve()):
        raise ValueError('Use separately installed Unreal Engine 5 commandlet')
    return snapshot_file(exe,kind='stat')

def command(exe,project,script):
    return [exe,str(project),'-run=pythonscript','-script='+str(script),
            '-unattended','-nullrhi','-nosound','-nosplash','-stdout','-FullStdOutLogOutput']

def assess(s,result,log):
    checked(s)
    if not isinstance(result,dict) or set(result)!={'engine_version','project_file'}:raise ValueError('Invalid native probe result')
    version=result['engine_version'];project=result['project_file']
    if not isinstance(version,str) or not re.fullmatch(r'5\.\d+\.\d+(?:[-+A-Za-z0-9._/]{0,180})',version):
        raise ValueError('Expected Unreal Engine 5 version')
    if not isinstance(project,str) or Path(project.replace('\\','/')).name!=s['project_name']+'.uproject':
        raise ValueError('Native project identity mismatch')
    lines=[line.split(MARKER,1)[1].strip() for line in log.splitlines() if MARKER in line]
    if lines!=[version] or re.search(r'(?im)^.*(?:LogPython:\s*Error:|Fatal error:|Traceback \(most recent call last\))',log):
        raise ValueError('Missing or failed native Python commandlet evidence')
    return {'engine_version':version,'native_editor_python_verified':True,
            'project_name':s['project_name'],'gameplay_verified':False,'build_verified':False,'asset_import_verified':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=2:
        raise ValueError('Missing exact Unreal runtime guard')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.json')
    if plan['guards'][1]!=resolve_runtime(root):raise ValueError('Reviewed Unreal runtime changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    plan['guards'].append(resolve_runtime(root))
    return plan,dict(s,command_profile=command(plan['guards'][1]['path'],'<temporary project>','<fixed probe script>'),
        scope='Launch installed Unreal Engine 5 Python commandlet against generated temporary project under Windows cap. No external project code, cooking, packaging or asset changes. Engine may write host caches and use network; not a sandbox.')

def execute(root,plan):
    s,dst=validate(root,plan)
    from deepthort_local.triad_job import verify_root_cap
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    verify_root_cap();sampler=WindowsPressureSampler();_,ram=sampler.read()
    if ram is None or ram<20:raise ValueError('Insufficient foreground RAM reserve for Unreal')
    require_storage(dst.parent,install=True)
    with tempfile.TemporaryDirectory(prefix='.janus-ue-probe-',dir=dst.parent) as tmp:
        stage=Path(tmp);project=stage/(s['project_name']+'.uproject');script=stage/'probe.py'
        project.write_text(json.dumps(descriptor(s)),encoding='utf-8');script.write_text(SCRIPT,encoding='utf-8')
        log=stage/'editor.log';verify_guards(plan['guards'])
        run_profile(command(plan['guards'][1]['path'],project,script),stage,log,240,sampler)
        raw=guard.read_bound(stage/'result.json',8192);logs=guard.read_bound(log,4*1024*1024)
        observed=json.loads(raw.decode('utf-8'))
        result=assess(s,observed,logs.decode('utf-8',errors='replace'))
        actual=Path(observed['project_file'])
        if not actual.is_absolute():actual=stage/actual
        if actual.resolve()!=project.resolve():raise ValueError('Native editor reported different project path')
        result.update(log_sha256=hashlib.sha256(logs).hexdigest(),shared_root_cap_verified=True)
    payload=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'native_unreal_editor_probe_passed','output':plan['output'],'sha256':digest,**result}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Native Unreal commandlet evidence unavailable; check trusted installation, plugin and resource limits'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
