"""Assemble an independent ship-component draft from inspected vanilla geometry."""
from __future__ import annotations
import copy
from collections import defaultdict
import hashlib
import io
import itertools
import json
import math
from pathlib import Path, PurePosixPath
import re
import xml.etree.ElementTree as ET
import zipfile

from .agent_plan import extension_id
from .x4_geometry import GeometryError, _catalog_key, _entries, _obj_geometry, _read, fitted_mesh, inspect_fit, mesh_positions
from .x4_sources import PE_MACRO

AXES='xyz'
MAX_GEOMETRY_BYTES=40_000_000


def position(connection):
    node=connection.find('offset/position')
    values=tuple(float(node.get(k,'0')) if node is not None else 0.0 for k in AXES)
    if not all(map(math.isfinite,values)):raise GeometryError('Nonfinite component offset')
    return values


def protected(component):
    anchors=[]
    for c in component.findall('connections/connection'):
        name=c.get('name','')
        match=re.match(r'con_(cockpit|dock|engine|weapon|turret|elevator)',name)
        if match:anchors.append((name,match[1],position(c)))
    missing={'cockpit','dock','engine','weapon','turret','elevator'}-{a[1] for a in anchors}
    if missing:raise GeometryError('Missing protected connection groups: '+', '.join(sorted(missing)))
    return anchors


def placements(hull,origin,rock,anchors,contact=None):
    """Screen upper/rear candidates against static boxes and nominal axis-aligned approach rays."""
    mid=[origin[i]+(hull['min'][i]+hull['max'][i])/2 for i in range(3)]
    span=hull['dimensions']
    result=[]
    for rear in (.12,.16,.20,.24,.30,.36):
        for lift in (.32,.48,.64,.75):
            center=(mid[0],mid[1]+lift*span[1],mid[2]-rear*span[2])
            offset=[center[i]-(rock['min'][i]+rock['max'][i])/2 for i in range(3)]
            lo=[a+b for a,b in zip(offset,rock['min'])]
            hi=[a+b for a,b in zip(offset,rock['max'])]
            gaps=[]
            for name,kind,p in anchors:
                delta=[max(lo[i]-p[i],p[i]-hi[i],0) for i in range(3)]
                if kind in ('engine','weapon','cockpit','dock'):
                    axis=1 if kind=='dock' else 2
                    ahead=hi[axis]>=p[axis] if kind in ('weapon','cockpit') else lo[axis]<=p[axis]
                    if ahead:delta[axis]=0
                gaps.append((math.hypot(*delta),name))
            overlap=[min(hi[i],origin[i]+hull['max'][i])-max(lo[i],origin[i]+hull['min'][i]) for i in range(3)]
            clearance,nearest=min(gaps)
            if clearance>=2 and min(overlap)>2:
                proof=contact(offset) if contact is not None else None
                if contact is not None and proof is None:continue
                result.append(dict(offset=offset,min_gap=clearance,nearest=nearest,box_overlap=overlap,
                                   crossing_triangles=proof))
                break
    return result


def _xml(root):
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)


def _triangles(raw,shift):
    points=[]
    faces=[]
    for line in _obj_geometry(raw).splitlines():
        tag,*coords=line.split()
        if tag==b'v':points.append(tuple(float(v)+d for v,d in zip(coords,shift)))
        elif tag==b'f':faces.append(tuple(points[int(i)-1] for i in coords))
    return faces


def _sub(a,b):
    return tuple(x-y for x,y in zip(a,b))


def _dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def _cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])


def _cuts(a,b,tri):
    # Interior segment/triangle crossing. Box overlap and tangency alone are insufficient.
    v,w,x=tri
    edge=_sub(b,a)
    e,f=_sub(w,v),_sub(x,v)
    p=_cross(edge,f)
    det=_dot(e,p)
    if abs(det)<1e-8:return False
    t=_sub(a,v)
    u=_dot(t,p)/det
    if not 0<u<1:return False
    q=_cross(t,e)
    return 0<_dot(edge,q)/det<1-u and 0<_dot(f,q)/det<1


def contact_checker(hull,rock,cell):
    def cells(tri):
        return itertools.product(*(range(math.floor(min(axis)/cell),math.floor(max(axis)/cell)+1)
                                   for axis in zip(*tri)))
    grid=defaultdict(list)
    entries=0
    for i,tri in enumerate(hull):
        for key in cells(tri):
            entries+=1
            if entries>1_000_000:raise GeometryError('Hull exceeds triangle index budget')
            grid[key].append(i)
    def check(offset):
        pairs=0
        for j,local in enumerate(rock):
            tri=[tuple(x+y for x,y in zip(v,offset)) for v in local]
            for i in sorted({i for key in cells(tri) for i in grid.get(key,())}):
                pairs+=1
                if pairs>500_000:raise GeometryError('Placement exceeds triangle comparison budget')
                other=hull[i]
                if any(_cuts(tri[k],tri[k-1],other) or _cuts(other[k],other[k-1],tri) for k in range(3)):
                    return [i,j]
        return None
    return check


def preview_obj(parts):
    """Place the two main visual surfaces in a single ship-space OBJ for inspection."""
    out=io.BytesIO()
    preceding=0
    for name,raw,offset in parts:
        out.write(('o '+name+'\n').encode('ascii'))
        vertices=0
        for line in _obj_geometry(raw).splitlines():
            tag,*values=line.split()
            if tag==b'v':
                point=tuple(float(v)+d for v,d in zip(values,offset))
                out.write(('v %.9g %.9g %.9g\n'%point).encode('ascii'))
                vertices+=1
            elif tag==b'f':
                face=tuple(int(v)+preceding for v in values)
                out.write(('f %d %d %d\n'%face).encode('ascii'))
        preceding+=vertices
    return out.getvalue()

def make_draft(game,ship_path,rock,ship,package,variant,chosen=None):
    if (not re.fullmatch(r'[a-z0-9_][a-z0-9_-]*',package) or
            not re.fullmatch(r'[a-z][a-z0-9_]*_macro',variant) or
            package.replace('-','_') not in variant):
        raise GeometryError('Independent extension and macro identifiers required')
    directory=str(PurePosixPath(ship_path).parent)
    table=_entries(_catalog_key(game),(directory+'/').encode())
    doc=ET.fromstring(_read(table,ship_path))
    component=doc.find('component')
    old_dir=component.find('source').get('geometry').replace('\\','/').lower()
    main=next((c for c in component.findall('connections/connection') if c.find("parts/part[@name='part_main']") is not None),None)
    if main is None or any(n.tag!='position' for n in main.findall('offset/*')):
        raise GeometryError('Unsupported ship hull transform')
    asteroid=ET.fromstring(_read(table,rock['component']))
    parts=[c for c in asteroid.findall('component/connections/connection') if c.find("parts/part[@name='part_main']") is not None]
    if len(parts)!=1 or any(n.tag!='position' for n in parts[0].findall('offset/*')):
        raise GeometryError('Unsupported asteroid main part')
    part=copy.deepcopy(parts[0].find("parts/part[@name='part_main']"))
    part_name='part_'+package.replace('-','_')+'_rock'
    if any(p.get('name')==part_name for p in component.findall('.//part')):raise GeometryError('Part name collision')
    part.set('name',part_name)
    src=str(PurePosixPath(rock['mesh']).parent)
    lods=[lod.get('index','') for lod in part.findall('lods/lod')]
    if not lods or any(not re.fullmatch(r'[0-9]',n) for n in lods):raise GeometryError('Unsupported LOD set')
    fitted={}
    bounds=[]
    for suffix in ['lod'+n for n in lods]+['collision']:
        _,blob=mesh_positions(_read(table,f'{src}/part_main-{suffix}.xmf'),rock['scale'])
        info,_=mesh_positions(blob)
        fitted[part_name+'-'+suffix+'.xmf']=blob
        bounds.append(info)
    box={key:[func(m[key][i] for m in bounds) for i in range(3)] for key,func in [('min',min),('max',max)]}
    anchors=protected(component)
    hull_triangles=_triangles(_read(table,ship['mesh']),position(main))
    rock_triangles=_triangles(fitted[part_name+'-lod0.xmf'],(0,0,0))
    contact=contact_checker(hull_triangles,rock_triangles,max(ship['dimensions'])/24)
    options=placements(ship,position(main),box,anchors,contact)
    if not options:raise GeometryError('No candidate passed the protected-connection checks')
    if chosen is None:return options
    if chosen not in options:raise GeometryError('Selected placement no longer resolves')
    base=variant.removesuffix('_macro')
    registry=_entries(_catalog_key(game),b'index/')
    for kind,new_name in [('components',base),('macros',variant)]:
        native=ET.fromstring(_read(registry,'index/'+kind+'.xml'))
        if native.tag!='index' or any(e.get('name','').lower()==new_name for e in native.findall('entry')):
            raise GeometryError('Could not reserve independent '+kind+' identity')
    dest=f'{directory}/{base}_data'
    for node in part.findall('size/*'):
        for k in AXES:
            if k in node.attrib:node.set(k,str(float(node.get(k))*rock['scale']))
    component.set('name',base)
    component.find('source').set('geometry',f'extensions/{package}/{dest}'.replace('/','\\'))
    con=ET.SubElement(component.find('connections'),'connection',name='ConnectionFor'+part_name,tags='part ')
    ET.SubElement(ET.SubElement(con,'offset'),'position',dict(zip(AXES,map(str,chosen['offset']))))
    ET.SubElement(con,'parts').append(part)
    macro=ET.fromstring(_read(table,f'{directory}/macros/{PE_MACRO}.xml'))
    definition=macro.find('macro')
    if definition.get('name')!=PE_MACRO or definition.find('component').get('ref')!=PurePosixPath(ship_path).stem:
        raise GeometryError('Vanilla ship macro/component mismatch')
    definition.set('name',variant)
    definition.find('component').set('ref',base)
    paths={f'{directory}/{base}.xml':_xml(doc),f'{directory}/macros/{variant}.xml':_xml(macro)}
    for kind,asset in [('components',f'{directory}/{base}'),('macros',f'{directory}/macros/{variant}')]:
        delta=ET.Element('diff')
        ET.SubElement(ET.SubElement(delta,'add',sel='/index'),'entry',name=PurePosixPath(asset).name,
                      value=f'extensions/{package}/{asset}'.replace('/','\\'))
        paths[f'index/{kind}.xml']=_xml(delta)
    original_files=[p for p in table if p.startswith(old_dir+'/')]
    if (not original_files or PurePosixPath(ship['mesh']).as_posix() not in original_files or
            sum(table[p][2] for p in original_files)>MAX_GEOMETRY_BYTES):
        raise GeometryError('Ship geometry outside attachment budget')
    evidence=dict(ship_component=ship_path,rock=rock['component'],placement=chosen,
                  protected_connections=[dict(name=n,kind=k,position=p) for n,k,p in anchors],
                  fitted_meshes={k:hashlib.sha256(v).hexdigest() for k,v in fitted.items()},
                  vanilla_geometry_files=len(original_files),lods=lods,uniform_scale=rock['scale'],
                  scope='Static main hull and rock boxes, connection points and nominal approach rays. Turret arcs, physics and gameplay untested.')
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
        for p in original_files:
            name=p[len(old_dir)+1:]
            if not re.fullmatch(r'[a-z0-9_-]+\.[a-z0-9]+',name) or name in fitted:
                raise GeometryError('Unexpected ship geometry member')
            archive.writestr(f'{package}/{dest}/{name}',_read(table,p))
        for p,b in paths.items():archive.writestr(f'{package}/{p}',b)
        for p,b in fitted.items():archive.writestr(f'{package}/{dest}/{p}',b)
        archive.writestr('Preview_MainHull_and_Rock.obj',preview_obj([
            ('PE_main_hull',_read(table,ship['mesh']),position(main)),
            (part_name,fitted[part_name+'-lod0.xmf'],chosen['offset'])]))
        archive.writestr('Attachment_measurements.json',json.dumps(evidence,indent=2))
    return output.getvalue()


def stage_attachment(client,index,ident,session,original,project,report,cancelled=None,stage=None):
    project=str(Path(project).resolve())
    mesh=index.latest_mesh(project,ident)
    if not mesh or mesh[0]!=ident:return '',0
    package=extension_id(original)
    if not re.fullmatch(r'[a-z0-9_][a-z0-9_-]*',package):return '',0
    steps=index.merged_steps(ident,original)
    variants=[PurePosixPath(s['path']).stem for s in steps if '/macros/' in s['path'] and
              package.replace('-','_') in PurePosixPath(s['path']).stem and
              re.fullmatch(r'[a-z][a-z0-9_]*_macro',PurePosixPath(s['path']).stem)]
    if len(variants)!=1:return '',0
    game=report['game_dir']
    fit=inspect_fit(game,report['pe_component_file'])
    rock=next((c for c in fit['candidates'] if PurePosixPath(c['component']).stem==mesh[1]),None)
    if not rock:raise GeometryError('Selected source missing')
    _,measured=fitted_mesh(game,fit,rock['component'])
    if measured['sha256']!=mesh[3]:raise GeometryError('Saved mesh and current source differ')
    args=(game,fit['ship']['component'],rock,fit['ship'],package,variants[0])
    candidates=make_draft(*args)
    fingerprint=hashlib.sha256(repr((mesh[3],variants[0],_catalog_key(game),candidates)).encode()).hexdigest()
    scope=(project,ident,fingerprint)
    if cancelled and cancelled():raise GeometryError('Placement cancelled')
    with index._db() as db:
        db.execute('BEGIN IMMEDIATE')
        saved=db.execute('SELECT note FROM attachment_drafts WHERE project=? AND request_id=? AND fingerprint=?',scope).fetchone()
        if saved:return saved[0],0
        db.execute('INSERT OR IGNORE INTO attachment_attempts VALUES (?,?,?,0)',scope)
        attempt=db.execute('SELECT attempts FROM attachment_attempts WHERE project=? AND request_id=? AND fingerprint=?',scope).fetchone()[0]
        if attempt>=2:return 'Attachment selection exhausted two bounded attempts; review required.',0
        db.execute('UPDATE attachment_attempts SET attempts=attempts+1 WHERE project=? AND request_id=? AND fingerprint=?',scope)
    options={str(i):p for i,p in enumerate(candidates,1)}
    prompt=('Choose an upper-rear rock attachment on the inspected ship. Prefer more separation from protected connections. '
            'Reply with the option number only.\n'+'\n'.join(f"{i}. XYZ {tuple(round(v,2) for v in p['offset'])}, clearance {p['min_gap']:.2f}" for i,p in options.items()))
    if cancelled and cancelled():raise GeometryError('Placement cancelled')
    if attempt:prompt+='\nReturn only one digit from the displayed choices.'
    exchange=session+'-attach-'+fingerprint[:12]+('-retry' if attempt else '')
    lookup=getattr(client,'completed_exchange',None)
    reply=lookup(exchange,prompt) if callable(lookup) else None
    if reply is None:reply=client.chat(exchange,prompt,max_tokens=16)
    choice=reply.strip().rstrip('.')
    if choice not in options:return 'No valid placement selected.',1
    blob=make_draft(*args,chosen=options[choice])
    if cancelled and cancelled():raise GeometryError('Placement cancelled')
    component_path=str(PurePosixPath(fit['ship']['component']).with_name(variants[0].removesuffix('_macro')+'.xml'))
    note=(f"Independent component draft: {component_path} and index/components.xml bind the fitted rock "
          f"to {variants[0]} with {options[choice]['min_gap']:.2f} units static clearance. "
          "Use these generated files in the component roadmap.")
    with index._db() as db:
        db.execute('INSERT OR IGNORE INTO attachment_drafts VALUES (?,?,?,?,?,?)',
                   (*scope,note,hashlib.sha256(blob).hexdigest(),blob))
        note=db.execute('SELECT note FROM attachment_drafts WHERE project=? AND request_id=? AND fingerprint=?',scope).fetchone()[0]
    if stage:stage(note)
    return note,1
