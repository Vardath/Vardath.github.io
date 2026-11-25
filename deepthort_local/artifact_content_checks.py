"""Bounded, read-only pixel and raw mesh measurements.

PNG: 8-bit noninterlaced grayscale/RGB/gray-alpha/RGBA, no palette,
color-key transparency or animation. OBJ: Cartesian positions, no scene
transforms, material, collision, manifoldness or rendering claims.
"""
from __future__ import annotations
import math
import zlib
from .artifact_media_checks import unpack_at
from .large_artifacts import MAX_CHUNKS

MAX_PIXELS=1_048_576
MAX_COLORS=256
PNG_CONTENT={'min_visible_pixels','min_distinct_visible_colors'}
OBJ_EXTENTS={prefix+'extent_'+axis for prefix in ('min_','max_') for axis in 'xyz'}

def paeth(a,b,c):
    p=a+b-c
    pa,pb,pc=abs(p-a),abs(p-b),abs(p-c)
    return a if pa<=pb and pa<=pc else b if pb<=pc else c

def png_content(reader):
    width,height,depth,color,compression,filter_method,interlace=unpack_at('>IIBBBBB',reader,16)
    bpp={0:1,2:3,4:2,6:4}.get(color)
    if not bpp or depth!=8 or interlace or compression or filter_method:
        raise ValueError('PNG content check supports only 8-bit noninterlaced grayscale/RGB/alpha')
    if not 0<width*height<=MAX_PIXELS:
        raise ValueError('PNG content exceeds bounded pixel budget')
    stride=width*bpp
    limit=height*(stride+1)
    decoder=zlib.decompressobj()
    decoded=bytearray()
    pos=8;chunks=0;idat=False;finished_idat=False
    while pos<len(reader):
        chunks+=1
        if chunks>MAX_CHUNKS:raise ValueError('Too many PNG chunks')
        size,kind=unpack_at('>I4s',reader,pos)
        end=pos+12+size
        if end>len(reader):raise ValueError('Truncated PNG chunk')
        if kind in (b'tRNS',b'acTL',b'fdAT',b'fcTL'):
            raise ValueError('Color-key transparency or animated PNG not supported by content check')
        if kind==b'IDAT':
            if finished_idat:raise ValueError('Nonconsecutive PNG image data')
            idat=True
            for start in range(pos+8,end-4,65536):
                data=reader[start:min(start+65536,end-4)]
                try:decoded.extend(decoder.decompress(data,limit-len(decoded)+1))
                except zlib.error as error:raise ValueError('Invalid PNG compressed image data') from error
                if len(decoded)>limit or decoder.unconsumed_tail or decoder.unused_data:
                    raise ValueError('PNG decompressed data exceeds expected image layout')
        elif idat:finished_idat=True
        pos=end
    if not decoder.eof or len(decoded)!=limit:
        raise ValueError('PNG compressed image does not match expected scanlines')
    prev=bytearray(stride)
    visible=0
    colors=set()
    offset=0
    for _ in range(height):
        method=decoded[offset];offset+=1
        row=decoded[offset:offset+stride];offset+=stride
        if method not in (0,1,2,3,4):raise ValueError('Invalid PNG scanline filter')
        if method:
            for i in range(stride):
                a=row[i-bpp] if i>=bpp else 0
                b=prev[i]
                c=prev[i-bpp] if i>=bpp else 0
                predictor=a if method==1 else b if method==2 else (a+b)//2 if method==3 else paeth(a,b,c)
                row[i]=(row[i]+predictor)&255
        for i in range(0,stride,bpp):
            if color in (4,6) and row[i+bpp-1]==0:continue
            visible+=1
            if len(colors)<MAX_COLORS:
                # Ignore alpha when counting distinct visible color samples.
                colors.add(bytes(row[i:i+(1 if color in (0,4) else 3)]))
        prev=row
    return {'min_visible_pixels':visible,'min_distinct_visible_colors':len(colors)}

def obj_extents(stream):
    stream.seek(0)
    low=[math.inf]*3;high=[-math.inf]*3;count=0
    while True:
        line=stream.readline(262145)
        if not line:break
        if len(line)>262144:raise ValueError('OBJ acceptance line exceeds bound')
        if count==0:line=line.removeprefix(b'\xef\xbb\xbf')
        fields=line.split(b'#',1)[0].split()
        if not fields or fields[0]!=b'v':continue
        if len(fields)!=4:
            raise ValueError('Extent check requires unambiguous Cartesian OBJ vertices')
        for axis,value in enumerate(fields[1:]):
            coord=float(value)
            if not math.isfinite(coord):raise ValueError('Nonfinite OBJ position')
            low[axis]=min(low[axis],coord);high[axis]=max(high[axis],coord)
        count+=1
    if not count:raise ValueError('OBJ has no measured positions')
    result={}
    for i,axis in enumerate('xyz'):
        extent=high[i]-low[i]
        if not math.isfinite(extent):raise ValueError('Nonfinite OBJ extent')
        result['min_extent_'+axis]=extent
        result['max_extent_'+axis]=extent
    return result
