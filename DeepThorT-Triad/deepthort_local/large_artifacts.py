"""Stream selected large binary artifacts through the existing structural checks.

The maximum is the existing content-hash guard ceiling, so a verified output
can be used as the next stage's pinned input. No whole-file bytes allocation.
"""
from __future__ import annotations
import hashlib
import os
from .action_guards import MAX_HASH_BYTES
from . import artifact_media_checks as media

BLOCK=1024*1024
MAX_METADATA=2*BLOCK
MAX_CHUNKS=20000
ARCHIVES={'.zip','.apk','.aab','.jar'}
MEDIA={'.png','.wav','.glb','.dds','.exe','.dll'}

def identity(st):
    return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)

class BoundedReader:
    def __init__(self,stream,size):
        self.stream=stream
        self.size=size
    def __len__(self):return self.size
    def __getitem__(self,key):
        if not isinstance(key,slice) or key.step not in (None,1):
            raise ValueError('Only contiguous artifact slices are supported')
        start,end,_=key.indices(self.size)
        length=max(0,end-start)
        if length>MAX_METADATA:raise ValueError('Artifact metadata read exceeds bound')
        self.stream.seek(start)
        data=self.stream.read(length)
        if len(data)!=length:raise ValueError('Artifact changed during structural check')
        return data

def verify_large_artifact(path,archive_scope):
    suffix=path.suffix.casefold()
    if suffix not in ARCHIVES|MEDIA:
        raise ValueError('Large artifact has no supported bounded structural verifier')
    before=path.stat()
    if not 0<before.st_size<=MAX_HASH_BYTES:
        raise ValueError('Artifact exceeds approved hash-check limit')
    original=identity(before)
    with path.open('rb') as stream:
        def check():
            if identity(os.fstat(stream.fileno()))!=original:
                raise ValueError('Artifact changed during verification')
        check()
        if suffix in ARCHIVES:
            scope=archive_scope(stream,suffix)
        else:
            reader=BoundedReader(stream,before.st_size)
            if suffix=='.wav':scope=media.wav(reader,max_chunks=MAX_CHUNKS)
            elif suffix=='.glb':scope=media.glb(reader,max_json=MAX_METADATA,max_chunks=MAX_CHUNKS)
            else:scope=media.media_scope(suffix,reader)
        check()
        stream.seek(0)
        digest=hashlib.sha256()
        total=0
        while True:
            data=stream.read(min(BLOCK,MAX_HASH_BYTES-total+1))
            if not data:break
            total+=len(data)
            if total>MAX_HASH_BYTES:raise ValueError('Artifact exceeds approved hash-check limit')
            digest.update(data)
        check()
        if total!=before.st_size:raise ValueError('Artifact changed during hashing')
    if path.is_symlink() or identity(path.stat())!=original:
        raise ValueError('Artifact changed during verification')
    return {'sha256':digest.hexdigest(),'bytes':total,'scope':scope}
