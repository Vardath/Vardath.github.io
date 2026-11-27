"""Reviewed IDE handoff using VS Code's portable workspace and native CLI probe."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.android_emulator import real_file
from deepthort_local.android_game_compilation import run_profile
from deepthort_local.disk_gate import require_storage
from deepthort_local.language_server import analyze,MAX_SOURCE

SCHEMA='janus-vscode-handoff-v1'
EXTRA=('document','.py')
VERSION=re.compile(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'document'} or not isinstance(s['document'],str):
        raise ValueError('Choose exact project-relative Python document')
    return s

def runtime(root):
    value=os.environ.get('VSCODE_CLI_EXE')
    if not value:raise ValueError('Set VSCODE_CLI_EXE to installed VS Code bin/code.exe or Code.exe')
    exe=real_file(value)
    if exe.name.casefold()!='code.exe' or exe.is_relative_to(Path(root).resolve()):
        raise ValueError('Choose separately installed VS Code CLI executable')
    return snapshot_file(exe,kind='stat')

def command(exe,stage):
    return [exe,'--version','--user-data-dir',str(stage/'profile'),
            '--extensions-dir',str(stage/'extensions'),'--disable-extensions']

def assess(log):
    rows=[x.strip() for x in log.splitlines() if x.strip()]
    if len(rows)!=3 or not VERSION.fullmatch(rows[0]) or not re.fullmatch(r'[0-9a-fA-F]{40}',rows[1]) or rows[2] not in ('x64','arm64','ia32'):
        raise ValueError('Expected exact native VS Code version, commit and architecture')
    return {'version':rows[0],'commit':rows[1].lower(),'architecture':rows[2]}

def workspace(s):
    checked(s)
    # Relative to the extracted workspace file: the bundle is intended for
    # extraction directly into the reviewed project root, not automatic opening.
    return {'folders':[{'path':'.'}],'settings':{'task.allowAutomaticTasks':'off',
            'extensions.ignoreRecommendations':True,'security.workspace.trust.enabled':True},
            'extensions':{'recommendations':[]}}

def bundle(s,analysis,version):
    receipt={'schema':SCHEMA,'document':s['document'],'source_sha256':analysis['source_sha256'],
             'editor':version,'diagnostics':analysis['diagnostics'],'symbols':analysis['symbols'],
             'native_cli_verified':True,'editor_ui_opened':False,'project_code_executed':False,
             'ide_extension_installed':False}
    entries={'JANUS.code-workspace':(json.dumps(workspace(s),indent=2)+'\n').encode(),
             'janus-ide-receipt.json':(json.dumps(receipt,indent=2)+'\n').encode()}
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,raw in entries.items():z.writestr(name,raw)
    payload=buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or sorted(z.namelist())!=sorted(entries) or any(z.read(k)!=v for k,v in entries.items()):
            raise ValueError('IDE handoff verification failed')
    return payload,receipt

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=3:
        raise ValueError('Missing exact IDE runtime guard')
    s,dst,doc=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
    if doc.stat().st_size>MAX_SOURCE or plan['guards'][2]!=runtime(root):raise ValueError('Source exceeds bound or IDE runtime changed')
    return s,dst,doc

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
    plan['guards'].append(runtime(root));validate(root,plan)
    return plan,dict(s,scope='Run fixed installed VS Code CLI version probe with temporary profile and disabled extensions; use bundled local Python LSP for exact source diagnostics and symbols. Produce new portable workspace ZIP, not open an IDE, modify settings, install extensions or run project code.')

def execute(root,plan):
    s,dst,doc=validate(root,plan)
    from deepthort_local.triad_job import verify_root_cap
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    verify_root_cap();sampler=WindowsPressureSampler();_,ram=sampler.read()
    if ram is None or ram<15:raise ValueError('Insufficient RAM reserve')
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-ide-',dir=dst.parent) as tmp:
        stage=Path(tmp);log=stage/'cli.log';verify_guards(plan['guards'])
        run_profile(command(plan['guards'][2]['path'],stage),stage,log,30,sampler)
        version=assess(guard.read_bound(log,65536).decode('utf-8-sig'))
    result=analyze(guard.exact(doc,plan['guards'][1],MAX_SOURCE))
    payload,receipt=bundle(s,result,version)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'native_ide_cli_and_handoff_verified','output':plan['output'],'sha256':digest,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed IDE CLI or source analysis unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
