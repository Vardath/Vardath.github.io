"""Reviewed Godot Android debug export of a bounded, trusted project archive."""
from __future__ import annotations
import argparse
import configparser
import hashlib
import io
import json
import os
from pathlib import Path,PurePosixPath
import re
import stat
import sys
import tempfile
import time
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.android_emulator import real_file
from deepthort_local.engine_environment import godot_executable
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-godot-android-debug-export-v1'
MAX_ARCHIVE=16*1024*1024
MAX_SOURCE=32*1024*1024
MAX_APK=256*1024*1024
MAX_LOG=4*1024*1024
SUFFIXES={'.gd','.tscn','.tres','.png','.jpg','.jpeg','.webp','.wav','.ogg','.mp3','.json','.txt','.svg','.ttf','.otf','.glb','.gltf','.bin','.shader','.gdshader'}
RESERVED={'con','prn','aux','nul',*(f'com{i}' for i in range(1,10)),*(f'lpt{i}' for i in range(1,10))}

def checked(s):
    if not isinstance(s,dict) or set(s)!={'archive','preset'} or not isinstance(s['archive'],str) or not isinstance(s['preset'],str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 _-]{0,39}',s['preset']):
        raise ValueError('Choose a trusted Godot source ZIP and a named Android debug preset')
    return s

def archive_files(raw,preset):
    if not 1<=len(raw)<=MAX_ARCHIVE:raise ValueError('Source archive exceeds bound')
    entries={};seen=set();total=0;prefixes={}
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            infos=z.infolist()
            if not 1<=len(infos)<=128:raise ValueError('Source archive entry bound')
            for i in infos:
                n=i.filename;parts=n.split('/')
                if (i.is_dir() or i.flag_bits&1 or stat.S_IFMT(i.external_attr>>16) not in (0,stat.S_IFREG)
                    or any(not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_. -]{0,79}',p) or p.endswith((' ','.')) or p.split('.')[0].lower() in RESERVED for p in parts)
                    or len(n)>220 or n.casefold() in seen):
                    raise ValueError('Unsafe, linked, duplicate or unsupported archive path')
                if n not in ('project.godot','export_presets.cfg') and PurePosixPath(n).suffix.lower() not in SUFFIXES:
                    raise ValueError('Unsupported project archive member')
                for k in range(1,len(parts)+1):
                    p='/'.join(parts[:k]);old=prefixes.setdefault(p.casefold(),p)
                    if old!=p:raise ValueError('Case-ambiguous archive path')
                seen.add(n.casefold());total+=i.file_size
                if total>MAX_SOURCE:raise ValueError('Expanded source exceeds bound')
                entries[n]=z.read(i)
    except (zipfile.BadZipFile,RuntimeError,NotImplementedError) as exc:
        raise ValueError('Invalid project ZIP') from exc
    if not {'project.godot','export_presets.cfg'}<=entries.keys():
        raise ValueError('Source ZIP must contain root project.godot and export_presets.cfg')
    for n in seen:
        if any('/'.join(n.split('/')[:k]) in seen for k in range(1,len(n.split('/')))):
            raise ValueError('Archive file/directory collision')
    try:
        cfg=configparser.ConfigParser(interpolation=None,delimiters=('=',),strict=True)
        cfg.read_string(entries['export_presets.cfg'].decode('utf-8-sig'))
        matches=[section for section in cfg.sections() if re.fullmatch(r'preset\.\d+',section) and cfg[section].get('name')==json.dumps(preset)]
        if len(matches)!=1 or cfg[matches[0]].get('platform')!='"Android"':
            raise ValueError('No unique Android export preset')
        opt=cfg[matches[0]+'.options']
        if opt.get('gradle_build/use_gradle_build')!='false':
            raise ValueError('Only explicit non-Gradle Android template export supported')
        for section in cfg.sections():
            for key,value in cfg[section].items():
                if ('keystore' in key or 'password' in key or 'encryption_key' in key or 'custom_template' in key) and value not in ('','""','false'):
                    raise ValueError('External signing credentials or custom templates refused')
        if cfg[matches[0]].get('export_filter')!='"all_resources"':
            raise ValueError('Use an all-resources export preset')
    except (configparser.Error,KeyError,UnicodeError) as exc:
        raise ValueError('Unsupported Android preset format') from exc
    return entries

def resolve_runtime(root):
    exe=godot_executable()
    if not exe:raise ValueError('Installed Godot executable required')
    p=real_file(exe)
    if p.suffix.casefold()!='.exe' or p.is_relative_to(Path(root).resolve()):
        raise ValueError('Use a separately installed Windows Godot executable')
    return snapshot_file(p,kind='stat')

def commands(exe,stage,apk,preset):
    return [[exe,'--headless','--path',str(stage),'--editor','--import'],
            [exe,'--headless','--path',str(stage),'--export-debug',preset,str(apk)]]

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=3:
        raise ValueError('Missing source or runtime guards')
    s,dst,src=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix='.apk',extra=('archive','.zip'))
    if plan['guards'][2]!=resolve_runtime(root):raise ValueError('Reviewed Godot runtime changed')
    return s,dst,archive_files(guard.exact(src,plan['guards'][1],MAX_ARCHIVE),s['preset'])

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.apk',extra=('archive','.zip'))
    plan['guards'].append(resolve_runtime(root))
    _,_,entries=validate(root,plan)
    return plan,{'archive':s['archive'],'preset':s['preset'],'source_members':sorted(entries),
        'command_profiles':commands(plan['guards'][2]['path'],'<private staged project>','<new staged APK>',s['preset']),
        'scope':'Execute trusted Godot import/debug export under Windows shared cap. Requires installed Android templates/SDK and debug settings. Project code may execute with user rights; not an OS sandbox. Godot may write host cache/settings or use networking. No automatic install, release signing, device installation or playtest.'}

def run_profile(argv,stage,log,seconds,sampler):
    from deepthort_local.triad_job import child_server
    with child_server(argv,stage,log) as (pid,alive):
        if not alive.member(pid):raise ValueError('Godot outside cleanup job')
        deadline=time.monotonic()+seconds
        while alive():
            cpu,ram=sampler.read()
            if ram is None or ram<10 or (cpu is not None and cpu>=90) or log.stat().st_size>MAX_LOG or time.monotonic()>=deadline:
                raise ValueError('Godot stopped on resource/log/time bound')
            require_storage(stage)
            time.sleep(.5)
        if alive.code()!=0:raise ValueError('Godot returned nonzero exit status')
    if log.stat().st_size>MAX_LOG:raise ValueError('Godot log exceeds bound')

def inspect_apk(path):
    if not path.is_file() or path.is_symlink() or not 1<=path.stat().st_size<=MAX_APK:
        raise ValueError('Missing or oversized APK')
    with zipfile.ZipFile(path) as z:
        infos=z.infolist();names={i.filename for i in infos}
        if len(infos)>8192 or len(names)!=len(infos) or sum(i.file_size for i in infos)>512*1024*1024 or not {'AndroidManifest.xml','classes.dex'}<=names:
            raise ValueError('Invalid APK archive structure')
        if z.getinfo('AndroidManifest.xml').file_size>4*1024*1024 or z.getinfo('classes.dex').file_size<8:
            raise ValueError('Invalid APK manifest or dex size')
        with z.open('AndroidManifest.xml') as f:
            if f.read(4)!=b'\x03\x00\x08\x00':raise ValueError('Expected binary Android manifest')
        with z.open('classes.dex') as f:
            if not re.fullmatch(rb'dex\n[0-9]{3}\x00',f.read(8)):raise ValueError('Expected DEX header')
        if z.testzip() is not None:raise ValueError('APK CRC failure')
    return {'bytes':path.stat().st_size,'entries':len(infos),'apk_structure_verified':True,'signature_verified':False,'device_execution_verified':False}

def execute(root,plan):
    s,dst,entries=validate(root,plan)
    from deepthort_local.triad_job import verify_root_cap
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    verify_root_cap();sampler=WindowsPressureSampler();_,ram=sampler.read()
    if ram is None or ram<15:raise ValueError('Insufficient host RAM reserve')
    require_storage(dst.parent,install=True)
    with tempfile.TemporaryDirectory(prefix='.janus-android-export-',dir=dst.parent) as tmp:
        stage=Path(tmp)/'project';stage.mkdir();apk=Path(tmp)/'output.apk'
        for name,data in entries.items():
            path=stage.joinpath(*name.split('/'));path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        verify_guards(plan['guards'])
        for i,argv in enumerate(commands(plan['guards'][2]['path'],stage,apk,s['preset'])):
            run_profile(argv,stage,Path(tmp)/f'godot-{i}.log',300,sampler)
        result=inspect_apk(apk)
        digest=hashlib.sha256()
        with apk.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
        validate(root,plan);require_storage(dst.parent)
        os.link(apk,dst)
    return {'schema':'janus-android-debug-export-result-v1','status':'android_debug_apk_exported',
            'output':plan['output'],'sha256':digest.hexdigest(),'source_unchanged':True,'shared_root_cap_verified':True,**result}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Reviewed Godot Android debug export blocked; inspect installed templates, SDK/settings, source preset and host headroom'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
