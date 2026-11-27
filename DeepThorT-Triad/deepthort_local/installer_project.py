"""Reviewed Inno Setup project generation; never compile, install or execute payloads."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,MAX_GUARDS,MAX_HASH_BYTES,validate_guards
SCHEMA='janus-inno-installer-project-v1'
MAX_FILES=MAX_GUARDS-4 # script, specification, absent output, exclusions
MAX_TOTAL=128*1024*1024
MAX_FILE=MAX_HASH_BYTES
RESERVED={'con','prn','aux','nul',*(f'com{i}' for i in range(1,10)),*(f'lpt{i}' for i in range(1,10))}
def component(s):
    if not isinstance(s,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_. -]{0,95}',s) or s.endswith(('.', ' ')) or s.split('.')[0].casefold() in RESERVED:
        raise ValueError('Use a bounded Windows-safe path component')
    return s
def relative(s):
    if not isinstance(s,str) or len(s)>220:raise ValueError('Use bounded project-relative path')
    for c in s.split('/'):component(c)
    return s
def checked(s):
    if not isinstance(s,dict) or set(s)!={'app_name','app_id','version','files','entrypoint'}:raise ValueError('Expected app name, stable ID, version, files and entrypoint')
    component(s['app_name']);component(s['app_id'])
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',s['app_id']):raise ValueError('Use stable simple app ID')
    if not isinstance(s['version'],str) or not re.fullmatch(r'[0-9]{1,4}(?:\.[0-9]{1,4}){1,3}',s['version']):raise ValueError('Use numeric version')
    files=s['files']
    if not isinstance(files,list) or not 1<=len(files)<=MAX_FILES:raise ValueError('Choose 1–6 exact files')
    for p in files:relative(p)
    if len({p.casefold() for p in files})!=len(files):raise ValueError('Duplicate Windows destination')
    entry=s['entrypoint'];relative(entry)
    if entry not in files or not entry.casefold().endswith('.exe'):raise ValueError('Select included executable entrypoint')
    return s

def payloads(root,s,exclude):
    result=[];total=0
    for path in s['files']:
        suffix=Path(path).suffix.casefold()
        if not suffix or suffix=='.iss':raise ValueError('Payload must have explicit non-installer-script extension')
        file=guard.path_for(root,path,exclude,{suffix},exists=True)
        size=file.stat().st_size
        if not 1<=size<=MAX_FILE:raise ValueError('Payload file size exceeds bound')
        total+=size
        if total>MAX_TOTAL:raise ValueError('Total payload exceeds bound')
        record=snapshot_file(file);guard.exact(file,record,MAX_FILE)
        result.append(record)
    return result

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.iss')
    root=Path(root).resolve(strict=True)
    plan['guards'].extend(payloads(root,s,plan['exclude']))
    validate_guards(plan['guards'])
    if len(json.dumps(plan,ensure_ascii=True))>=4096:raise ValueError('Installer approval exceeds queue argument bound; shorten paths or split payload')
    return plan,dict(s,scope='Create an Inno Setup source project only. Selected files become install payload; compile and install separately.',
                     payload_hashes=[x['expected'] for x in plan['guards'][1:]])

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or not 2<=len(plan['guards'])<=MAX_FILES+1:
        raise ValueError('Missing reviewed payloads')
    core=dict(plan,guards=plan['guards'][:1])
    s,dst,_=guard.validate(root,core,schema=SCHEMA,checked=checked,output_suffix='.iss')
    root=Path(root).resolve(strict=True)
    if payloads(root,s,core['exclude'])!=plan['guards'][1:]:raise ValueError('Reviewed payload changed')
    return s,dst,root

def win_path(p):return p.replace('/','\\')
def render(s,root,dst):
    checked(s)
    lines=['; JANUS reviewed installer source. Compile separately with Inno Setup.',
           '[Setup]','AppId=JANUS.'+s['app_id'],'AppName='+s['app_name'],'AppVersion='+s['version'],
           'DefaultDirName={localappdata}\\Programs\\'+s['app_name'],'DefaultGroupName='+s['app_name'],
           'PrivilegesRequired=lowest','OutputDir=.','OutputBaseFilename='+s['app_id']+'-'+s['version']+'-setup',
           'Compression=lzma2','SolidCompression=yes','DisableProgramGroupPage=yes','',
           '[Files]']
    for p in s['files']:
        src=os.path.relpath(root/p,dst.parent).replace('\\','/')
        # The generated relative path can include parent steps; the actual
        # payload was reviewed under the project root. No Inno constants,
        # wildcard, quote, or directive injection through source paths.
        if any(c in src for c in '{}";*?%|\r\n') or any(ord(c)<32 for c in src):
            raise ValueError('Installer relative source path contains unsupported characters')
        parts=p.split('/');dest='{app}'+('\\'+win_path('/'.join(parts[:-1])) if len(parts)>1 else '')
        lines.append('Source: "'+win_path(src)+'"; DestDir: "'+dest+'"; Flags: ignoreversion')
    lines+=['','[Icons]','Name: "{group}\\'+s['app_name']+'"; Filename: "{app}\\'+win_path(s['entrypoint'])+'"','']
    return ('\ufeff'+'\r\n'.join(lines)).encode('utf-8')
def execute(root,plan):
    s,dst,root=validate(root,plan);data=render(s,root,dst)
    digest=guard.publish(data,dst,lambda:validate(root,plan))
    return {'status':'installer_source_generated','output':plan['output'],'sha256':digest,
            'payload_files':len(s['files']),'payload_sha256':[g['expected'] for g in plan['guards'][1:]],
            'compiled':False,'installed':False,'executed':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Installer project unavailable; inspect reviewed payloads and paths'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
