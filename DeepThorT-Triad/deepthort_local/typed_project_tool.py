"""Common exact-source review and non-overwriting publication for typed project tools."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from .action_guards import snapshot_file
from .source_security import exclusions,excluded,linked
from .structured_source import strict_json
from .disk_gate import require_storage

MAX_SPEC=250000
MAX_INPUT=16*1024*1024
MAX_OUTPUT=16*1024*1024

def path_for(root,relative,exclude,suffixes,*,exists):
    if not isinstance(relative,str) or not 1<=len(relative)<=300 or Path(relative).suffix.casefold() not in suffixes:
        raise ValueError('Unsupported project-relative file type')
    parts=relative.split('/')
    if any(not x or x in ('.','..') or ':' in x or '\\' in x or any(ord(c)<32 for c in x) or x.endswith((' ','.')) for x in parts) or excluded(relative,set(exclude)):
        raise ValueError('Protected or unsafe project path')
    path=root
    for part in parts:
        path=path/part
        if path.exists() or path.is_symlink():
            if linked(path):raise ValueError('Linked project path refused')
    if path.resolve(strict=False)!=path or not path.parent.is_dir():
        raise ValueError('Use an existing project folder')
    if exists and not path.is_file():raise ValueError('Input file missing')
    if not exists and (path.exists() or path.is_symlink()):raise ValueError('Output already exists')
    return path

def read_bound(path,limit):
    with path.open('rb') as f:raw=f.read(limit+1)
    if not raw or len(raw)>limit:raise ValueError('Input empty or exceeds bound')
    return raw

def exact(path,guard,limit):
    raw=read_bound(path,limit)
    if hashlib.sha256(raw).hexdigest()!=guard['expected']:raise ValueError('Reviewed bytes changed')
    return raw

def inspect_spec(raw,checked):
    try:return checked(strict_json(raw.decode('utf-8-sig')))
    except (UnicodeError,RecursionError,TypeError,KeyError) as exc:raise ValueError('Invalid typed specification') from exc

def review(root,source,output,exclude,*,schema,checked,output_suffix,extra=None):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude)
    src=path_for(root,source,exclude,{'.json'},exists=True)
    dst=path_for(root,output,exclude,{output_suffix},exists=False)
    guard=snapshot_file(src)
    spec=inspect_spec(exact(src,guard,MAX_SPEC),checked)
    guards=[guard]
    if extra:
        other=path_for(root,spec[extra[0]],exclude,({extra[1]} if isinstance(extra[1],str) else extra[1]),exists=True)
        if other.stat().st_size>MAX_INPUT:raise ValueError('Input exceeds byte bound')
        guards.append(snapshot_file(other))
    return {'schema':schema,'root':str(root),'source':source,'output':output,'exclude':exclude,
            'guards':guards,'expires_at':int(time.time())+1800},spec

def validate(root,plan,*,schema,checked,output_suffix,extra=None):
    root=Path(root).resolve(strict=True)
    if (not isinstance(plan,dict) or set(plan)!={'schema','root','source','output','exclude','guards','expires_at'}
        or plan['schema']!=schema or plan['root']!=str(root)
        or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800
        or exclusions(plan['exclude'])!=plan['exclude'] or not isinstance(plan['guards'],list)
        or len(plan['guards'])!=(2 if extra else 1)):
        raise ValueError('Invalid or expired project tool approval')
    src=path_for(root,plan['source'],plan['exclude'],{'.json'},exists=True)
    dst=path_for(root,plan['output'],plan['exclude'],{output_suffix},exists=False)
    if snapshot_file(src)!=plan['guards'][0]:raise ValueError('Reviewed specification changed')
    spec=inspect_spec(exact(src,plan['guards'][0],MAX_SPEC),checked)
    other=None
    if extra:
        other=path_for(root,spec[extra[0]],plan['exclude'],({extra[1]} if isinstance(extra[1],str) else extra[1]),exists=True)
        if other.stat().st_size>MAX_INPUT or snapshot_file(other)!=plan['guards'][1]:
            raise ValueError('Reviewed input changed')
    return spec,dst,other

def publish(payload,dst,revalidate):
    if not isinstance(payload,bytes) or not payload or len(payload)>MAX_OUTPUT:
        raise ValueError('Output exceeds byte bound')
    require_storage(dst.parent)
    fd,tmp=tempfile.mkstemp(prefix='.janus-typed-output-',suffix='.tmp',dir=dst.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(payload);f.flush();os.fsync(f.fileno())
        revalidate()
        os.link(tmp,dst)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return hashlib.sha256(payload).hexdigest()
