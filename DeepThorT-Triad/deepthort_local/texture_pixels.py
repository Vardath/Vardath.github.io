"""Bounded, decoded 8-bit PNG pixels for reviewed texture production."""
from __future__ import annotations
import io
import struct
from .artifact_media_checks import png
MAX_PIXELS=2048*2048
def image_module():
    try:from PIL import Image
    except ImportError as exc:raise ValueError('Install the existing presentation or image tools to provide Pillow') from exc
    return Image
def decode(raw,modes):
    png(raw)
    width,height,depth,color,compression,filter_method,interlace=struct.unpack('>IIBBBBB',raw[16:29])
    if width>2048 or height>2048 or width*height>MAX_PIXELS or depth!=8 or color not in (0,2):
        raise ValueError('Use bounded 8-bit opaque grayscale or RGB PNG')
    Image=image_module()
    with Image.open(io.BytesIO(raw),formats=['PNG']) as im:
        if im.mode not in modes or im.size!=(width,height) or getattr(im,'n_frames',1)!=1 or 'transparency' in im.info:
            raise ValueError('Unsupported or transparent PNG pixel mode')
        im.verify()
    with Image.open(io.BytesIO(raw),formats=['PNG']) as im:
        im.load();data=im.tobytes();mode=im.mode
    if len(data)!=width*height*(1 if mode=='L' else 3):raise ValueError('Pixel length mismatch')
    return width,height,mode,data
def encode(width,height,mode,data):
    Image=image_module()
    if not 1<=width<=2048 or not 1<=height<=2048 or mode not in ('L','RGB') or len(data)!=width*height*(1 if mode=='L' else 3):
        raise ValueError('Invalid output pixel layout')
    stream=io.BytesIO()
    with Image.frombytes(mode,(width,height),data) as im:im.save(stream,format='PNG',compress_level=6)
    raw=stream.getvalue()
    if decode(raw,(mode,))!=(width,height,mode,data):raise ValueError('Decoded PNG differs from generated pixels')
    return raw
