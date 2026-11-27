"""Strict bounded static triangular OBJ geometry, with optional complete UVs."""
from __future__ import annotations
import math
MAX_VERTICES=20000
MAX_FACES=20000
MAX_UVS=MAX_FACES*3
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):return math.sqrt(dot(a,a))
def triangle(vertices,face):
    a,b,c=(vertices[i] for i in face)
    ab,ac,bc=sub(b,a),sub(c,a),sub(c,b)
    scale=max(norm(ab),norm(ac),norm(bc))
    area2=norm(cross(ab,ac))
    if scale<=0 or area2<=1e-10*scale*scale:raise ValueError('Degenerate or excessively thin triangle')
    return ab,ac,area2
def numeric(values,n,limit):
    if len(values)!=n or any(len(v)>40 for v in values):raise ValueError('Unexpected geometry field count')
    out=tuple(float(v) for v in values)
    if any(not math.isfinite(v) or abs(v)>limit for v in out):raise ValueError('Geometry coordinate outside bound')
    return out
def index(text,count):
    if len(text)>12 or not text:raise ValueError('Invalid OBJ index')
    v=int(text)
    i=v-1 if v>0 else count+v
    if not v or not 0<=i<count:raise ValueError('OBJ reference must resolve to an existing entry')
    return i
def parse(raw,*,allow_uv=False):
    if not raw or len(raw)>16*1024*1024:raise ValueError('OBJ outside byte bound')
    vertices=[];faces=[];uvs=[];uvfaces=[]
    for raw_line in raw.decode('utf-8-sig').splitlines():
        if len(raw_line)>512:raise ValueError('OBJ line outside bound')
        line=raw_line.split('#',1)[0].split()
        if not line:continue
        kind,*values=line
        if kind=='v':
            if len(vertices)>=MAX_VERTICES:raise ValueError('Vertex bound exceeded')
            vertices.append(numeric(values,3,1e6))
        elif kind=='vt' and allow_uv:
            if len(uvs)>=MAX_UVS:raise ValueError('UV bound exceeded')
            uvs.append(numeric(values,2,1e6))
        elif kind=='f':
            if len(faces)>=MAX_FACES or len(values)!=3:raise ValueError('Use bounded triangulated OBJ geometry')
            parts=[x.split('/') for x in values]
            if all(len(x)==1 for x in parts):face=tuple(index(x[0],len(vertices)) for x in parts);uvface=None
            elif allow_uv and all(len(x)==2 for x in parts):
                face=tuple(index(x[0],len(vertices)) for x in parts);uvface=tuple(index(x[1],len(uvs)) for x in parts)
            else:raise ValueError('Unsupported or incomplete OBJ face attributes')
            triangle(vertices,face);faces.append(face);uvfaces.append(uvface)
        else:raise ValueError('Only v/f and explicitly allowed vt statements are supported; attributes are not silently discarded')
    if not vertices or not faces:raise ValueError('Mesh needs vertices and triangles')
    if uvs and any(x is None for x in uvfaces):raise ValueError('UV coverage must be complete')
    if not uvs and any(x is not None for x in uvfaces):raise ValueError('Missing UV coordinates')
    return vertices,faces,uvs,uvfaces
def encode(vertices,faces,uvs=(),uvfaces=()):
    lines=['# JANUS static triangle geometry']
    def num(v):return format(v,'.17g')
    lines.extend('v '+' '.join(num(x) for x in v) for v in vertices)
    lines.extend('vt '+' '.join(num(x) for x in uv) for uv in uvs)
    if uvs:
        if len(uvfaces)!=len(faces):raise ValueError('Incomplete UV coverage')
        lines.extend('f '+' '.join(str(v+1)+'/'+str(t+1) for v,t in zip(f,uvf)) for f,uvf in zip(faces,uvfaces))
    else:lines.extend('f '+' '.join(str(i+1) for i in f) for f in faces)
    raw=('\n'.join(lines)+'\n').encode('ascii')
    decoded=parse(raw,allow_uv=bool(uvs))
    if decoded!=(list(vertices),list(faces),list(uvs),list(uvfaces) if uvs else [None]*len(faces)):
        raise ValueError('OBJ geometry roundtrip mismatch')
    return raw
