"""Declarative, bounded artifact acceptance checks. No model code execution.

Only measurable properties are supported. A pass is not rendering, gameplay,
audibility, installability or general functional acceptance.
"""
from __future__ import annotations
import hashlib
import math
import os
import struct
import zipfile
from pathlib import Path,PurePosixPath
from .workspace import safe_target
from .action_guards import MAX_HASH_BYTES
from .large_artifacts import identity,BoundedReader,MAX_CHUNKS
from .artifact_media_checks import unpack_at
from .artifact_content_checks import PNG_CONTENT,OBJ_EXTENTS,png_content,obj_extents,MAX_PIXELS,MAX_COLORS

RULES={
    '.png':{'width':(1,16384),'height':(1,16384),'min_visible_pixels':(1,MAX_PIXELS),
            'min_distinct_visible_colors':(1,MAX_COLORS)},
    '.dds':{'width':(1,16384),'height':(1,16384)},
    '.obj':{'min_vertices':(1,10000000),'min_faces':(1,10000000),**{name:(0,1e12) for name in OBJ_EXTENTS}},
    '.wav':{'channels':(1,32),'sample_rate':(1,768000),'min_frames':(1,100000000)},
    '.zip':{'required_members':None},'.apk':{'required_members':None},
    '.aab':{'required_members':None},'.jar':{'required_members':None},
}

class AcceptanceMismatch(ValueError):
    """Only a measured discrepancy, never a changed file or parser error."""
    pass

def validate(output,checks):
    if not isinstance(checks,dict) or not checks or len(checks)>8:
        raise ValueError('Expected nonempty bounded artifact acceptance checks')
    allowed=RULES.get(PurePosixPath(output).suffix.casefold(),{})
    for name,value in checks.items():
        if name not in allowed:raise ValueError('Unsupported artifact acceptance criterion: '+name)
        if name=='required_members':
            if not isinstance(value,list) or not 1<=len(value)<=12:raise ValueError('Invalid required archive members')
            for member in value:
                if (not isinstance(member,str) or not 1<=len(member)<=240 or '\\' in member or
                    ':' in member or member.startswith('/') or any(p in ('','.','..') for p in member.split('/')) or
                    any(ord(c)<32 for c in member)):
                    raise ValueError('Unsafe required archive member')
            if len(set(value))!=len(value):raise ValueError('Duplicate required archive member')
        elif name in OBJ_EXTENTS:
            if type(value) not in (int,float) or not 0<=value<=1e12 or not math.isfinite(value):
                raise ValueError('Invalid OBJ extent criterion: '+name)
        elif type(value) is not int or not allowed[name][0]<=value<=allowed[name][1]:
            raise ValueError('Invalid numeric artifact criterion: '+name)
    for axis in 'xyz':
        if checks.get('min_extent_'+axis,0)>checks.get('max_extent_'+axis,1e12):
            raise ValueError('Contradictory OBJ extent criteria')
    return checks

def measure(reader,stream,suffix,checks=None):
    if suffix=='.png':
        width,height=unpack_at('>II',reader,16)
        result={'width':width,'height':height}
        if PNG_CONTENT.intersection(checks or {}):result.update(png_content(reader))
        return result
    if suffix=='.dds':
        height,width=unpack_at('<II',reader,12)
        return {'width':width,'height':height}
    if suffix=='.obj':
        stream.seek(0)
        vertices=faces=0
        while True:
            line=stream.readline(262145)
            if not line:break
            if len(line)>262144:raise ValueError('OBJ acceptance line exceeds bound')
            fields=line.lstrip().split(None,1)
            if fields and fields[0]==b'v':vertices+=1
            elif fields and fields[0]==b'f':faces+=1
        result={'min_vertices':vertices,'min_faces':faces}
        if OBJ_EXTENTS.intersection(checks or {}):result.update(obj_extents(stream))
        return result
    if suffix=='.wav':
        pos=12;fmt=None;payload=None;chunks=0
        while pos<len(reader):
            chunks+=1
            if chunks>MAX_CHUNKS:raise ValueError('Too many WAVE chunks')
            kind,size=unpack_at('<4sI',reader,pos)
            start=pos+8
            if start+size+(size&1)>len(reader):raise ValueError('Truncated WAVE data')
            if kind==b'fmt ':
                if size<16:raise ValueError('Invalid WAVE format')
                fmt=unpack_at('<HHIIHH',reader,start)
            elif kind==b'data':payload=size
            pos=start+size+(size&1)
        if not fmt or not payload or not fmt[4]:raise ValueError('Missing sample layout')
        return {'channels':fmt[1],'sample_rate':fmt[2],'min_frames':payload//fmt[4]}
    with zipfile.ZipFile(stream) as archive:
        rows=archive.infolist()
        if len(rows)>4000:raise ValueError('Too many archive members')
        return {'required_members':{r.filename for r in rows if not r.is_dir()}}

def verify(project,output,checks,structural):
    validate(output,checks)
    path=safe_target(project,output,must_exist=True)
    if structural.get('scope') in (None,'nonempty bytes only'):
        raise ValueError('Acceptance requires structural evidence')
    before=path.stat()
    if not 0<before.st_size<=MAX_HASH_BYTES or before.st_size!=structural['bytes']:
        raise ValueError('Artifact size changed before acceptance')
    original=identity(before)
    with path.open('rb') as stream:
        if identity(os.fstat(stream.fileno()))!=original:raise ValueError('Artifact changed')
        measured=measure(BoundedReader(stream,before.st_size),stream,path.suffix.casefold(),checks)
        stream.seek(0)
        hasher=hashlib.sha256();total=0
        while True:
            block=stream.read(min(1024*1024,MAX_HASH_BYTES-total+1))
            if not block:break
            total+=len(block)
            if total>MAX_HASH_BYTES:raise ValueError('Artifact grew beyond acceptance bound')
            hasher.update(block)
        if identity(os.fstat(stream.fileno()))!=original or total!=before.st_size:
            raise ValueError('Artifact changed during acceptance')
    if path.is_symlink() or identity(path.stat())!=original or hasher.hexdigest()!=structural['sha256']:
        raise ValueError('Acceptance evidence is not the structurally checked artifact')
    observed={}
    for name,wanted in checks.items():
        actual=measured[name]
        if name=='required_members':
            absent=[member for member in wanted if member not in actual]
            if absent:raise AcceptanceMismatch('Artifact acceptance failed: missing archive members '+', '.join(absent)[:200])
            observed[name]=list(wanted)
        else:
            if (actual<wanted if name.startswith('min_') else actual>wanted if name.startswith('max_') else actual!=wanted):
                raise AcceptanceMismatch(f'Artifact acceptance failed: {name} expected {wanted}, observed {actual}')
            observed[name]=actual
    return {'artifact_sha256':structural['sha256'],'checks':checks,'observed':observed,
            'scope':'Specified measurable properties only; functional acceptance not established'}

def stage_acceptance(project,stage,task,receipt):
    if task and task.get('output')==stage['output'] and 'acceptance' in task:
        return verify(project,stage['output'],task['acceptance'],receipt)
    return None
