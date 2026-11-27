"""Reviewed management of stopped local Docker containers; no workload execution."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.android_emulator import real_file
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-stopped-container-v1'
HOST='npipe:////./pipe/docker_engine'
LABEL='org.janus.project'
MAX_LOG=65536
ID=re.compile(r'[0-9a-f]{64}')
IMAGE=re.compile(r'sha256:[0-9a-f]{64}')

def checked(s):
    if not isinstance(s,dict) or s.get('operation') not in ('create','inspect','remove'):
        raise ValueError('Choose create, inspect or remove')
    op=s['operation']
    if set(s)!=({'operation','name','image'} if op=='create' else {'operation','name','container_id'}):
        raise ValueError('Invalid stopped-container specification')
    if not isinstance(s['name'],str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,23}',s['name']):
        raise ValueError('Choose a simple lowercase container name')
    value=s['image'] if op=='create' else s['container_id']
    if not isinstance(value,str) or not (IMAGE if op=='create' else ID).fullmatch(value):
        raise ValueError('Use exact full local image or container identity')
    return s

def project_key(root):
    return hashlib.sha256(os.path.normcase(str(Path(root).resolve(strict=True))).encode('utf-8')).hexdigest()

def name_for(root,s):
    return 'janus-'+project_key(root)[:12]+'-'+s['name']

def runtime(root):
    found=shutil.which('docker.exe')
    if not found:raise ValueError('Separately installed Docker CLI required')
    exe=real_file(found)
    if exe.name.casefold()!='docker.exe' or exe.is_relative_to(Path(root).resolve()):
        raise ValueError('Project-local or unexpected Docker executable')
    return snapshot_file(exe,kind='stat')

def base(exe):return [exe,'--host',HOST]

def create_command(root,s,exe):
    checked(s)
    if s['operation']!='create':raise ValueError('Not a create request')
    return base(exe)+['container','create','--pull=never','--name',name_for(root,s),
        '--label',LABEL+'='+project_key(root),'--network','none','--read-only',
        '--cap-drop','ALL','--security-opt','no-new-privileges','--memory','128m',
        '--cpus','0.25','--pids-limit','32','--no-healthcheck',s['image']]

def inspect_command(exe,ident):
    return base(exe)+['container','inspect','--format',
        '{{json .Id}}|{{json .Name}}|{{json (index .Config.Labels "org.janus.project")}}|{{json .State.Status}}|{{json .Image}}',ident]

def parse_container(root,s,raw,ident):
    # The format includes only fixed fields, not the image environment or secrets.
    try:actual,name,label,state,image=[json.loads(v) for v in raw.strip().split('|')]
    except (ValueError,TypeError) as exc:raise ValueError('Invalid container inspection') from exc
    if actual!=ident or name!='/'+name_for(root,s) or label!=project_key(root) or state not in ('created','exited') or not isinstance(image,str) or not IMAGE.fullmatch(image):
        raise ValueError('Container ownership, identity or stopped state not established')
    return {'container_id':actual,'name':name[1:],'state':state,'image':image}

def perform(root,s,exe,run):
    checked(s);op=s['operation']
    if op=='create':
        raw=run(base(exe)+['image','inspect','--format','{{json .Id}}|{{json .Config.Volumes}}',s['image']])
        try:ident,volumes=[json.loads(v) for v in raw.strip().split('|')]
        except (ValueError,TypeError) as exc:raise ValueError('Invalid local image inspection') from exc
        if ident!=s['image'] or volumes not in (None,{}):
            raise ValueError('Image identity mismatch or implicit image volumes')
        ident=run(create_command(root,s,exe)).strip()
        if not ID.fullmatch(ident):raise ValueError('Create may have changed daemon state; inspect before retry')
        row=parse_container(root,s,run(inspect_command(exe,ident)),ident)
        if row['state']!='created' or row['image']!=s['image']:
            raise ValueError('Created container does not match reviewed image/state')
        status='stopped_container_created'
    else:
        ident=s['container_id'];row=parse_container(root,s,run(inspect_command(exe,ident)),ident)
        status='stopped_container_inspected'
        if op=='remove':
            # Never force, remove volumes, prune, or select by a mutable name.
            result=run(base(exe)+['container','rm',ident]).strip()
            if result not in (ident,row['name']):raise ValueError('Removal outcome uncertain; inspect before retry')
            status='stopped_container_removed'
    return {'status':status,**row,'container_started':False,'daemon_shared_cap_verified':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=2:
        raise ValueError('Missing Docker runtime guard')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.json')
    if plan['guards'][1]!=runtime(root):raise ValueError('Docker CLI changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    plan['guards'].append(runtime(root));exe=plan['guards'][1]['path']
    commands=([base(exe)+['image','inspect','--format','{{json .Id}}|{{json .Config.Volumes}}',s['image']],create_command(root,s,exe),inspect_command(exe,'<created ID>')]
        if s['operation']=='create' else [inspect_command(exe,s['container_id'])]+([base(exe)+['container','rm',s['container_id']]] if s['operation']=='remove' else []))
    return plan,dict(s,commands=commands,local_endpoint=HOST,scope='Existing local Docker daemon, stopped containers only. Create/remove change daemon metadata outside the application job. No pull, start, execution, mounts, ports, forced deletion or pruning. Runtime limits configured for created container, not verified shared daemon limits. If interrupted inspect daemon state before retry.')

def execute(root,plan):
    s,dst=validate(root,plan)
    from deepthort_local.triad_job import verify_root_cap
    verify_root_cap();require_storage(dst.parent)
    env=os.environ.copy()
    for key in ('DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH'):
        env.pop(key,None)
    with tempfile.TemporaryDirectory(prefix='.janus-container-',dir=dst.parent) as tmp:
        env['DOCKER_CONFIG']=tmp
        def run(argv):
            verify_guards(plan['guards']);require_storage(dst.parent)
            log=Path(tmp)/'cli.log'
            with log.open('wb') as out:
                p=subprocess.Popen(argv,cwd=tmp,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                deadline=time.monotonic()+30
                try:
                    while p.poll() is None:
                        if time.monotonic()>=deadline or log.stat().st_size>MAX_LOG:
                            raise ValueError('Docker command interrupted; inspect daemon state')
                        time.sleep(.2)
                finally:
                    if p.poll() is None:p.kill();p.wait(timeout=5)
            if p.returncode or log.stat().st_size>MAX_LOG:raise ValueError('Docker CLI failed; inspect daemon state')
            return log.read_text(encoding='utf-8')
        result=perform(root,s,plan['guards'][1]['path'],run)
    payload=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode('utf-8')
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'output':plan['output'],'sha256':sha,**result}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Stopped container operation failed or was interrupted; daemon metadata may have changed. Inspect before retry.'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
