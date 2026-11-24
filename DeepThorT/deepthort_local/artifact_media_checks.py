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


def wav(data):
    if len(data)<12 or data[:4]!=b'RIFF' or data[8:12]!=b'WAVE' or struct.unpack_from('<I',data,4)[0]+8!=len(data):
        raise ValueError('Invalid RIFF/WAVE container')
    pos=12;fmt=None;payload=None
    while pos<len(data):
        if pos+8>len(data):raise ValueError('Truncated WAVE chunk')
        kind,size=struct.unpack_from('<4sI',data,pos)
        start=pos+8;end=start+size
        if end+(size&1)>len(data):raise ValueError('Truncated WAVE payload')
        if kind==b'fmt ':
            if fmt or size<16:raise ValueError('Invalid WAVE format')
            fmt=struct.unpack_from('<HHIIHH',data,start)
        elif kind==b'data':
            if payload is not None:raise ValueError('Duplicate WAVE data')
            payload=size
        pos=end+(size&1)
    if not fmt or not payload:raise ValueError('WAVE format or data missing')
    code,channels,rate,byte_rate,align,bits=fmt
    if code not in (1,3) or not 1<=channels<=32 or not 1<=rate<=768000 or bits not in (8,16,24,32,64):
        raise ValueError('Unsupported WAVE encoding')
    if code==3 and bits not in (32,64):raise ValueError('Invalid WAVE float width')
    if align!=channels*bits//8 or byte_rate!=rate*align or payload%align:
        raise ValueError('Inconsistent WAVE sample layout')
    return f'WAVE PCM container and sample layout ({channels} channels, {rate} Hz; audio not listened to)'


def glb(data):
    import json
    if len(data)<20:raise ValueError('Truncated GLB')
    magic,version,length=struct.unpack_from('<4sII',data)
    if magic!=b'glTF' or version!=2 or length!=len(data):raise ValueError('Invalid GLB header')
    pos=12;document=None;binary=None
    while pos<len(data):
        if pos+8>len(data):raise ValueError('Truncated GLB chunk')
        size,kind=struct.unpack_from('<II',data,pos);pos+=8
        if size%4 or pos+size>len(data):raise ValueError('Invalid GLB chunk extent')
        if document is None:
            if kind!=0x4e4f534a:raise ValueError('First GLB chunk must be JSON')
            from .structured_source import strict_json
            document=strict_json(data[pos:pos+size].decode('utf-8'))
            if not isinstance(document,dict) or not isinstance(document.get('asset'),dict) or document['asset'].get('version')!='2.0':
                raise ValueError('Invalid glTF asset version')
        elif kind==0x004e4942:
            if binary is not None:raise ValueError('Duplicate GLB binary chunk')
            binary=size
        elif kind==0x4e4f534a:raise ValueError('Duplicate GLB JSON')
        pos+=size
    if not document or not isinstance(document.get('meshes'),list) or not document['meshes']:
        raise ValueError('GLB mesh missing')
    buffers=document.get('buffers',[])
    if not isinstance(buffers,list):raise ValueError('Invalid GLB buffers')
    for i,buffer in enumerate(buffers):
        if not isinstance(buffer,dict) or type(buffer.get('byteLength')) is not int or buffer['byteLength']<=0:
            raise ValueError('Invalid GLB buffer length')
        if 'uri' in buffer:raise ValueError('External GLB buffer needs separate verification')
        if i!=0 or binary is None or not buffer['byteLength']<=binary<=buffer['byteLength']+3:
            raise ValueError('GLB buffer length mismatch')
    return 'GLB v2 container, JSON asset and embedded buffer bounds (geometry not rendered)'


def dds(data):
    if len(data)<128 or data[:4]!=b'DDS ' or struct.unpack_from('<I',data,4)[0]!=124:
        raise ValueError('Invalid DDS header')
    height,width=struct.unpack_from('<II',data,12)
    if not 0<width<=16384 or not 0<height<=16384 or width*height>67_108_864:
        raise ValueError('DDS dimensions exceed bound')
    if struct.unpack_from('<I',data,76)[0]!=32:raise ValueError('Invalid DDS pixel format header')
    start=148 if data[84:88]==b'DX10' else 128
    if len(data)<=start:raise ValueError('Missing DDS texture payload')
    return f'DDS headers and dimensions {width}x{height} (pixels not decoded)'


def pe(data):
    if len(data)<64 or data[:2]!=b'MZ':raise ValueError('Invalid Windows executable header')
    offset=struct.unpack_from('<I',data,60)[0]
    if offset<64 or offset+24>len(data) or data[offset:offset+4]!=b'PE\0\0':
        raise ValueError('Missing PE header')
    _,sections,_,_,_,optional,flags=struct.unpack_from('<HHIIIHH',data,offset+4)
    if not 1<=sections<=96 or optional<2 or offset+24+optional+40*sections>len(data):
        raise ValueError('Invalid PE section table')
    if struct.unpack_from('<H',data,offset+24)[0] not in (0x10b,0x20b):
        raise ValueError('Unknown PE optional header')
    for i in range(sections):
        entry=offset+24+optional+i*40
        size,start=struct.unpack_from('<II',data,entry+16)
        if size and (start>len(data) or size>len(data)-start):raise ValueError('PE section exceeds file')
    return 'PE executable header and section bounds (not executed or trusted)'


def media_scope(suffix,data):
    if suffix=='.png':return png(data)
    if suffix=='.obj':return obj(data)
    if suffix=='.wav':return wav(data)
    if suffix=='.glb':return glb(data)
    if suffix=='.dds':return dds(data)
    if suffix in ('.exe','.dll'):return pe(data)
    return None
