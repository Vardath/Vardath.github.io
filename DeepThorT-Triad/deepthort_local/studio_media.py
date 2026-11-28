"""Explicit bounded media inspection; no new engine, writes, scanning or automatic playback."""
from __future__ import annotations
import io
import os
import stat
import wave
from pathlib import Path
from .workspace import safe_target, WorkspaceError

IMAGE_TYPES={'.png':('PNG',),'.jpg':('JPEG',),'.jpeg':('JPEG',),'.webp':('WEBP',),
             '.gif':('GIF',),'.bmp':('BMP',),'.tif':('TIFF',),'.tiff':('TIFF',)}
AUDIO_TYPES={'.wav','.mp3','.ogg','.flac','.m4a'}
VIDEO_TYPES={'.mp4','.webm','.avi','.mov','.mkv'}
MEDIA_TYPES=set(IMAGE_TYPES)|AUDIO_TYPES|VIDEO_TYPES
MAX_IMAGE_BYTES=16*1024*1024
MAX_PIXELS=12_000_000
HEADER_BYTES=65536


def identity(st):
    return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)


def media_target(root,relative):
    path=safe_target(root,relative,must_exist=True)
    if path.suffix.casefold() not in MEDIA_TYPES:
        raise WorkspaceError('Not a supported Studio media format')
    if not stat.S_ISREG(path.stat().st_mode):
        raise WorkspaceError('Not a regular media file')
    return path


def read_prefix(root,relative,limit=HEADER_BYTES):
    target=media_target(root,relative)
    before=target.stat()
    with target.open('rb') as stream:
        opened=os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or identity(opened)!=identity(before):
            raise WorkspaceError('Media file changed before inspection')
        data=stream.read(limit)
        after=os.fstat(stream.fileno())
    if identity(after)!=identity(before) or identity(media_target(root,relative).stat())!=identity(before):
        raise WorkspaceError('Media file changed during inspection')
    return target,before,data


def signature(suffix,data):
    if suffix=='.wav':return data[:4]==b'RIFF' and data[8:12]==b'WAVE'
    if suffix=='.avi':return data[:4]==b'RIFF' and data[8:12]==b'AVI '
    if suffix=='.flac':return data.startswith(b'fLaC')
    if suffix=='.ogg':return data.startswith(b'OggS')
    if suffix=='.mp3':return data.startswith(b'ID3') or len(data)>=2 and data[0]==255 and data[1]&224==224
    if suffix in ('.mp4','.mov','.m4a'):return data[4:8]==b'ftyp'
    if suffix in ('.webm','.mkv'):return data.startswith(b'\x1a\x45\xdf\xa3')
    return False


def inspect_media(root,relative):
    target,st,header=read_prefix(root,relative)
    suffix=target.suffix.casefold()
    result={'size':st.st_size,'identity':identity(st),'thumbnail':None,'playable':False,
            'lines':[relative,f'Size: {st.st_size:,} bytes','Observed file; no authorship or verification claim.']}
    if suffix in IMAGE_TYPES:
        if st.st_size>MAX_IMAGE_BYTES:
            result['lines'].append('Image exceeds 16 MiB preview limit. No image decoding.')
            return result
        try:
            from PIL import Image
        except ImportError:
            result['lines'].append('Image preview requires the existing optional Pillow dependency.')
            return result
        _,full_stat,data=read_prefix(root,relative,MAX_IMAGE_BYTES+1)
        if identity(full_stat)!=identity(st) or len(data)!=st.st_size or len(data)>MAX_IMAGE_BYTES:
            raise WorkspaceError('Image changed or exceeds preview limit')
        with Image.open(io.BytesIO(data),formats=list(IMAGE_TYPES[suffix])) as image:
            w,h=image.size
            result['lines'].append(f'{image.format} · {w} × {h} pixels')
            if w*h>MAX_PIXELS:
                result['lines'].append('Image exceeds 12 megapixel decode limit.')
            else:
                image.thumbnail((720,360))
                result['thumbnail']=image.convert('RGB').copy()
                result['lines'].append('Bounded first-frame preview only.')
        return result
    result['playable']=signature(suffix,header)
    result['lines'].append('Recognized container header; not full media validation.' if result['playable']
                           else 'Unsupported or unrecognized media header; playback disabled.')
    if suffix=='.wav' and result['playable']:
        try:
            with wave.open(io.BytesIO(header),'rb') as audio:
                frames,rate=audio.getnframes(),audio.getframerate()
                result['lines'].append(f'PCM WAV · {audio.getnchannels()} channels · {rate} Hz · {audio.getsampwidth()*8} bit · {frames/rate:.2f} s (declared header)')
        except (wave.Error,EOFError,ZeroDivisionError):
            result['lines'].append('PCM metadata unavailable in bounded header.')
    else:
        result['lines'].append('Duration/codec not measured; no external probe launched.')
    return result


def playback_target(root,relative,expected_identity):
    """Revalidate exact observed regular file and recognized audio/video header."""
    target,st,data=read_prefix(root,relative)
    if identity(st)!=expected_identity or not signature(target.suffix.casefold(),data):
        raise WorkspaceError('Media changed or format is not eligible for playback; inspect again')
    return target
