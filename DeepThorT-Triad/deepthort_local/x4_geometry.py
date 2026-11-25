"""Inspect vanilla main-part geometry and uniformly resize a supported native visual XMF."""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import struct
import tempfile
import xml.etree.ElementTree as ET
import zlib


class GeometryError(ValueError):
    pass


def export_mesh(target,data):
    """Expose a finished, checked draft as a new file with no partial overwrite."""
    mesh_positions(data)
    if target.suffix.lower()=='.obj':
        data=_obj_geometry(data)
    elif target.suffix.lower()!='.xmf':
        raise GeometryError('Choose an .xmf or .obj filename')
    export_new_file(target,data)


def export_new_file(target,data):
    with tempfile.NamedTemporaryFile(dir=target.parent,delete=False) as f:
        temp=Path(f.name)
    try:
        temp.write_bytes(data)
        os.link(temp,target)
    finally:
        temp.unlink(missing_ok=True)


def _obj_geometry(data):
    """Export the validated visual mesh positions and triangle indices in native axes."""
    offset,count,stride,materials=struct.unpack_from('<HBBB',data,6)
    start=offset+count*stride+136*materials
    vertices=[]
    faces=[]
    for i in range(count):
        kind,_,at,_,_,fmt,n,qty,width=struct.unpack_from('<9I',data,offset+i*stride)
        if qty*width>16_000_000:raise GeometryError('OBJ channel exceeds export budget')
        decoder=zlib.decompressobj()
        raw=decoder.decompress(data[start+at:start+at+n],qty*width+1)
        if not decoder.eof or decoder.unused_data or len(raw)!=qty*width:
            raise GeometryError('Incomplete OBJ source channel')
        if kind==0:
            for pos in range(0,len(raw),width):
                vertices.append('v %.9g %.9g %.9g' % struct.unpack_from('<3f',raw,pos))
        elif (kind,fmt,width) in ((30,30,2),(30,31,4)) and qty%3==0:
            for triangle in struct.iter_unpack('<3H' if width==2 else '<3I',raw):
                if max(triangle)>=struct.unpack_from('<I',data,14)[0]:
                    raise GeometryError('Face index outside the position stream')
                faces.append('f %d %d %d' % tuple(j+1 for j in triangle))
        else:raise GeometryError('Unsupported OBJ index channel')
    if not faces:raise GeometryError('No triangle faces to export')
    return ('\n'.join(vertices+faces)+'\n').encode('ascii')


def mesh_positions(data, scale=None):
    """Measure the float32 position channel. Preserve material, topology and other vertex attributes."""
    if len(data)<64 or data[:6]!=b'XUMF\x03\x00':
        raise GeometryError('Expected a version 3 XUMF mesh')
    offset,count,stride,materials=struct.unpack_from('<HBBB',data,6)
    vertices=struct.unpack_from('<I',data,14)[0]
    start=offset+count*stride+136*materials
    if offset!=64 or stride!=188 or not 1<=count<=16 or start>len(data) or not 1<=vertices<=200_000:
        raise GeometryError('Unsupported XMF header')
    chunks=[]
    for i in range(count):
        header=offset+i*stride
        kind,_,at,_,_,fmt,length,quantity,width=struct.unpack_from('<9I',data,header)
        if not length or start+at+length>len(data):
            raise GeometryError('Invalid XMF chunk range')
        chunks.append((at,length,header,kind,fmt,quantity,width))
    ordered=sorted(chunks)
    if any(a[0]+a[1]>b[0] for a,b in zip(ordered,ordered[1:])):
        raise GeometryError('Overlapping XMF chunks')
    streams=[c for c in chunks if c[3]==0]
    if len(streams)!=1 or any(c[3] not in (0,30) for c in chunks):
        raise GeometryError('Unsupported XMF vertex layout')
    at,length,header,_,fmt,quantity,width=streams[0]
    if (fmt not in (2,32) or not 12<=width<=64 or quantity!=vertices
            or (fmt==32 and width<28)):
        raise GeometryError('Unsupported XMF position channel')
    begin=start+at
    decoder=zlib.decompressobj()
    try:
        raw=bytearray(decoder.decompress(data[begin:begin+length],quantity*width+1))
    except zlib.error as exc:
        raise GeometryError('Invalid compressed XMF vertex stream') from exc
    if len(raw)!=quantity*width or not decoder.eof or decoder.unused_data:
        raise GeometryError('Invalid XMF vertex payload')
    if scale is not None and (not math.isfinite(scale) or scale<=0):
        raise GeometryError('Scale must be finite and positive')
    low=[math.inf]*3
    high=[-math.inf]*3
    for pos in range(0,len(raw),width):
        point=struct.unpack_from('<3f',raw,pos)
        if not all(map(math.isfinite,point)):
            raise GeometryError('Invalid mesh coordinate')
        for axis,value in enumerate(point):
            low[axis]=min(low[axis],value)
            high[axis]=max(high[axis],value)
        if scale is not None:
            struct.pack_into('<3f',raw,pos,*(v*scale for v in point))
    dims=[b-a for a,b in zip(low,high)]
    if min(dims)<=0:
        raise GeometryError('Main-part mesh has zero thickness')
    measure={'vertices':quantity,'min':low,'max':high,'dimensions':dims}
    if scale is None:
        return measure,None
    packed=zlib.compress(raw)
    result=bytearray(data[:begin]+packed+data[begin+length:])
    struct.pack_into('<I',result,header+24,len(packed))
    for other,_,h,*_ in chunks:
        if other>at:
            struct.pack_into('<I',result,h+8,other+len(packed)-length)
    return measure,bytes(result)


def _catalog_key(game):
    catalogs=sorted(Path(game).glob('[0-9][0-9].cat'))
    if not catalogs:
        raise GeometryError('Vanilla catalogs unavailable')
    return tuple((p,p.stat().st_mtime_ns,p.stat().st_size,p.with_suffix('.dat').stat().st_mtime_ns,
                  p.with_suffix('.dat').stat().st_size) for p in catalogs)


@lru_cache(maxsize=2)
def _entries(key,ship_dir):
    if sum(row[2] for row in key)>96_000_000:
        raise GeometryError('Catalog index exceeds geometry inspection budget')
    entries={}
    for cat,_,_,_,dat_size in key:
        offset=0
        with cat.open('rb') as stream:
            for line in stream:
                path,size,_,checksum=line.rstrip().rsplit(b' ',3)
                size=int(size)
                if size<0 or offset+size>dat_size:
                    raise GeometryError('Invalid vanilla catalog extent')
                if path.lower().startswith((b'assets/environments/asteroids/',ship_dir)):
                    entries[path.decode('utf8').lower()]=(cat.with_suffix('.dat'),offset,size,checksum)
                offset+=size
    return entries


def _read(entries,path):
    if path not in entries:
        raise GeometryError('Catalog asset unavailable: '+path)
    dat,offset,size,checksum=entries[path]
    if not 0<size<=12_000_000:
        raise GeometryError('Catalog asset exceeds geometry budget')
    with dat.open('rb') as f:
        f.seek(offset)
        data=f.read(size)
    if len(data)!=size or hashlib.md5(data,usedforsecurity=False).hexdigest().encode()!=checksum:
        raise GeometryError('Vanilla catalog checksum mismatch')
    return data


def _main_part(entries,path):
    data=_read(entries,path)
    if len(data)>2_500_000 or b'<!DOCTYPE' in data.upper():
        raise GeometryError('Unsupported component XML')
    try:
        component=ET.fromstring(data).find('component')
    except ET.ParseError as exc:
        raise GeometryError('Malformed component XML') from exc
    if component is None or component.get('name','').casefold()!=PurePosixPath(path).stem:
        raise GeometryError('Component identity mismatch')
    directory=component.find('source')
    if directory is None or component.find(".//parts/part[@name='part_main']/lods/lod[@index='0']") is None:
        raise GeometryError('No independently identifiable part_main LOD0')
    mesh=directory.get('geometry','').replace('\\','/').lower()+'/part_main-lod0.xmf'
    if PurePosixPath(mesh).parent.parent!=PurePosixPath(path).parent:
        raise GeometryError('Geometry source outside component asset directory')
    raw=_read(entries,mesh)
    info,_=mesh_positions(raw)
    return dict(info,component=path,mesh=mesh,sha256=hashlib.sha256(raw).hexdigest(),kind=component.get('class'))


def inspect_fit(game, ship_component):
    path=PurePosixPath(ship_component.lower())
    table=_entries(_catalog_key(game),(str(path.parent)+'/').encode())
    ship=_main_part(table,str(path))
    if not (ship['kind'] or '').startswith('ship_'):
        raise GeometryError('Reference component is not a ship')
    # Compare several actual ore meshes; eligibility and measurements come from the game.
    names=sorted(p for p in table if re.fullmatch(r'assets/environments/asteroids/env_ast_ore_m_\d+\.xml',p))
    candidates=[]
    for p in names[:6]:
        try:
            rock=_main_part(table,p)
        except (ValueError,ET.ParseError,zlib.error):
            continue
        if rock['kind']!='asteroid':
            continue
        dims=rock['dimensions']
        rock['roundness']=min(dims)/max(dims)
        rock['scale']=min(s/a for s,a in zip(ship['dimensions'],dims))
        candidates.append(rock)
    if not candidates:
        raise GeometryError('No supported vanilla ore main-part meshes found')
    candidates.sort(key=lambda r:(-r['roundness'],r['mesh']))
    return {'ship':ship,'candidates':candidates,'scope':'Local LOD0 main-part vertices in native axes. Placement and collision clearance untested.'}


def fitted_mesh(game,fit,choice):
    """Produce a native visual workpiece, re-reading and checking the inspected source bytes."""
    source=next((r for r in fit['candidates'] if r['component']==choice),None)
    if source is None:
        raise GeometryError('Select an inspected asteroid')
    ship=fit['ship']
    table=_entries(_catalog_key(game),(str(PurePosixPath(ship['component']).parent)+'/').encode())
    current_ship=_main_part(table,ship['component'])
    rock=_main_part(table,source['component'])
    if current_ship['sha256']!=ship['sha256'] or rock['sha256']!=source['sha256']:
        raise GeometryError('Source geometry changed; inspect again')
    factor=min(a/b for a,b in zip(current_ship['dimensions'],rock['dimensions']))
    _,output=mesh_positions(_read(table,rock['mesh']),factor)
    measured,_=mesh_positions(output)
    if not all(math.isclose(a*factor,b,rel_tol=1e-5) for a,b in zip(rock['dimensions'],measured['dimensions'])):
        raise GeometryError('Resized mesh failed dimensional verification')
    return output,dict(measured,uniform_scale=factor,source=rock['mesh'],sha256=hashlib.sha256(output).hexdigest())


def stage_geometry(client,index,request_id,session,original,project,report,cancelled=None,stage=None,*,operation_memory=None):
    """Persist a model-selected visual intermediate with its measurements outside the game project."""
    fit=inspect_fit(report['game_dir'],report['pe_component_file'])
    key=hashlib.sha256(json.dumps([original,fit],sort_keys=True).encode()).hexdigest()
    scope=(str(Path(project).resolve()),request_id,key)
    sql='SELECT note,name FROM mesh_drafts WHERE project=? AND request_id=? AND fingerprint=?'
    with index._db() as db:
        prior=db.execute(sql,scope).fetchone()
    if prior and prior[1]:return prior[0],0
    if cancelled and cancelled():
        raise GeometryError('Geometry selection cancelled')
    options={PurePosixPath(c['component']).stem:c for c in fit['candidates']}
    prompt=('Choose the roundest measured natural ore asteroid for this ship. '
            'Each number is the shortest divided by the longest LOD0 dimension. Higher means rounder. '
            'The selected mesh will be scaled uniformly to fit the main hull. '
            'Reply with the exact identifier only.\n'+'\n'.join(
            f"{name} {c['roundness']:.5f}" for name,c in options.items()))
    if stage:stage('Measured vanilla ship and asteroid vertices. Asking local model to select a visual mesh.')
    if prior:
        if prior[0].startswith('Second attempt:'):return prior[0],0
        prompt+=' Use just one name from the list, without explaining your choice.'
    exchange=f'{session}-geometry-{key[:16]}'+('-retry' if prior else '')
    if operation_memory:
        from .indexed_memory import append
        prompt=append(prompt,operation_memory,phase='indexed_geometry_selection',
                      identity=exchange,focus='Round natural ore asteroid mesh selection; scaled ship geometry and measured fit',
                      cancelled=cancelled)
    lookup=getattr(client,'completed_exchange',None)
    reply=lookup(exchange,prompt) if callable(lookup) else None
    if reply is None:reply=client.chat(exchange,prompt,max_tokens=48)
    name=reply.strip().strip('`')
    if name in options:
        data,measurement=fitted_mesh(report['game_dir'],fit,options[name]['component'])
        note=(f"Native visual mesh: {name}, {measurement['vertices']} vertices, "
              f"scale {measurement['uniform_scale']:.8f}, fitted XYZ "
              + ' x '.join(f'{d:.3f}' for d in measurement['dimensions'])
              + '. Draft LOD0 only. Plan ship component placement, lower LODs and collision.')
    else:
        data=b''
        note='Geometry selection unresolved. Local model did not return one inspected identifier.'
        if prior:note='Second attempt: '+note
    if cancelled and cancelled():raise GeometryError('Geometry selection cancelled')
    with index._db() as db:
        db.execute("INSERT INTO mesh_drafts VALUES (?,?,?,?,?,?,?) ON CONFLICT(project,request_id,fingerprint) "
                   "DO UPDATE SET note=excluded.note,digest=excluded.digest,name=excluded.name,mesh=excluded.mesh "
                   "WHERE mesh_drafts.name=''",
                   (*scope,note,hashlib.sha256(data).hexdigest(),name if data else '',data))
        note=db.execute(sql,scope).fetchone()[0]
    if stage:stage(note)
    return note,1
