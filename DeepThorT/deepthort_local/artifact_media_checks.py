"""Bounded structural checks for common game assets; never claim visual quality."""
from __future__ import annotations
import math
import struct
import zlib

PNG_SIGNATURE=b'\x89PNG\r\n\x1a\n'


def png(data):
    if not data.startswith(PNG_SIGNATURE):raise ValueError('Invalid PNG signature')
    pos=8
    chunks=0
    idat=False
    ended=False
    width=height=0
    while pos<len(data):
        if pos+12>len(data):raise ValueError('Truncated PNG chunk')
        length,kind=struct.unpack_from('>I4s',data,pos)
        end=pos+12+length
        if end>len(data):raise ValueError('Truncated PNG chunk body')
        payload=data[pos+8:end-4]
        crc=struct.unpack_from('>I',data,end-4)[0]
        if zlib.crc32(kind+payload)&0xffffffff!=crc:raise ValueError('PNG CRC mismatch')
        chunks+=1
        if chunks>20000:raise ValueError('Too many PNG chunks')
        if chunks==1:
            if kind!=b'IHDR' or length!=13:raise ValueError('PNG needs first IHDR')
            width,height,depth,color,compression,filter_method,interlace=struct.unpack('>IIBBBBB',payload)
            allowed={0:{1,2,4,8,16},2:{8,16},3:{1,2,4,8},4:{8,16},6:{8,16}}
            if not 0<width<=16384 or not 0<height<=16384 or width*height>67_108_864:
                raise ValueError('PNG dimensions exceed validation bound')
            if depth not in allowed.get(color,set()) or compression or filter_method or interlace not in (0,1):
                raise ValueError('Invalid PNG image header')
        elif kind==b'IHDR':raise ValueError('Duplicate PNG header')
        if kind==b'IDAT' and length:idat=True
        if kind==b'IEND':
            if length or not idat or end!=len(data):raise ValueError('Invalid PNG end')
            ended=True
            break
        pos=end
    if not ended:raise ValueError('PNG missing end marker')
    return f'PNG chunk CRC and dimensions {width}x{height} (pixels not decoded)'


def obj(data):
    counts={'v':0,'vt':0,'vn':0}
    maxima=dict(counts)
    faces=0
    for raw in data.decode('utf-8-sig').splitlines():
        line=raw.split('#',1)[0].split()
        if not line:continue
        kind,*values=line
        if kind in counts:
            minimum={'v':3,'vt':1,'vn':3}[kind]
            if not minimum<=len(values)<=8 or not all(math.isfinite(float(x)) for x in values):
                raise ValueError('Invalid OBJ numeric geometry')
            counts[kind]+=1
        elif kind=='f':
            if not 3<=len(values)<=10000:raise ValueError('Invalid OBJ face size')
            for value in values:
                refs=value.split('/')
                if not 1<=len(refs)<=3 or not refs[0]:raise ValueError('Invalid OBJ face reference')
                for name,ref in zip(('v','vt','vn'),refs):
                    if not ref:continue
                    index=int(ref)
                    if not index or (index<0 and -index>counts[name]):raise ValueError('Invalid OBJ relative index')
                    maxima[name]=max(maxima[name],index)
            faces+=1
    if not counts['v'] or not faces or any(maxima[k]>counts[k] for k in counts):
        raise ValueError('OBJ has missing geometry or out-of-range references')
    return f'OBJ numeric vertices and face indices ({counts["v"]} vertices, {faces} faces)'


def media_scope(suffix,data):
    if suffix=='.png':return png(data)
    if suffix=='.obj':return obj(data)
    return None
