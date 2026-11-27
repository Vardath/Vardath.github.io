"""Finite, owner-approved local Windows default-microphone capture into PCM WAV."""
import ctypes as c
from ctypes import wintypes as w
import io
import os
import time
import wave
from pathlib import Path
from . import typed_project_tool as guard
from .source_security import exclusions
RATE=16000
MAX_SECONDS=30
WHDR_DONE=1
DWORD_PTR=c.c_size_t

class Format(c.Structure):
    _pack_=1
    _fields_=[('wFormatTag',w.WORD),('nChannels',w.WORD),('nSamplesPerSec',w.DWORD),('nAvgBytesPerSec',w.DWORD),('nBlockAlign',w.WORD),('wBitsPerSample',w.WORD),('cbSize',w.WORD)]
class Header(c.Structure):
    _fields_=[('lpData',c.c_void_p),('dwBufferLength',w.DWORD),('dwBytesRecorded',w.DWORD),('dwUser',DWORD_PTR),('dwFlags',w.DWORD),('dwLoops',w.DWORD),('lpNext',c.c_void_p),('reserved',DWORD_PTR)]

def duration(seconds):
    if type(seconds) is not int or not 1<=seconds<=MAX_SECONDS:raise ValueError('Choose 1–30 seconds')
    return seconds
def stopped(cancelled):
    if cancelled and cancelled():raise ValueError('Microphone capture cancelled')
def wav_bytes(pcm,seconds):
    duration(seconds)
    if not isinstance(pcm,bytes) or len(pcm)!=RATE*2*seconds:raise ValueError('Incomplete PCM recording')
    out=io.BytesIO()
    with wave.open(out,'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE);f.writeframes(pcm)
    return out.getvalue()

def native_capture(seconds,cancelled=None):
    duration(seconds);stopped(cancelled)
    if os.name!='nt':raise RuntimeError('Windows microphone backend required')
    from .triad_job import verify_root_cap
    verify_root_cap()
    lib=c.WinDLL('winmm',use_last_error=True);handle=w.HANDLE()
    def fn(name,args):
        f=getattr(lib,name);f.argtypes=args;f.restype=w.UINT;return f
    open_=fn('waveInOpen',[c.POINTER(w.HANDLE),w.UINT,c.POINTER(Format),DWORD_PTR,DWORD_PTR,w.DWORD])
    prepare=fn('waveInPrepareHeader',[w.HANDLE,c.POINTER(Header),w.UINT])
    add=fn('waveInAddBuffer',[w.HANDLE,c.POINTER(Header),w.UINT])
    unprepare=fn('waveInUnprepareHeader',[w.HANDLE,c.POINTER(Header),w.UINT])
    start=fn('waveInStart',[w.HANDLE]);reset=fn('waveInReset',[w.HANDLE]);close=fn('waveInClose',[w.HANDLE])
    def check(code):
        if code:raise RuntimeError('Windows microphone operation failed (MMRESULT '+str(code)+')')
    size=RATE*2*seconds;buf=c.create_string_buffer(size);fmt=Format(1,1,RATE,RATE*2,2,16,0)
    header=Header();header.lpData=c.addressof(buf);header.dwBufferLength=size
    check(open_(c.byref(handle),0xffffffff,c.byref(fmt),0,0,0))
    prepared=False
    try:
        stopped(cancelled);check(prepare(handle,c.byref(header),c.sizeof(header)));prepared=True
        check(add(handle,c.byref(header),c.sizeof(header)));stopped(cancelled);check(start(handle))
        end=time.monotonic()+seconds+3
        while not header.dwFlags&WHDR_DONE:
            stopped(cancelled)
            if time.monotonic()>=end:raise TimeoutError('Microphone did not complete')
            time.sleep(.04)
        stopped(cancelled)
        if header.dwBytesRecorded!=size:raise ValueError('Microphone returned incomplete audio')
        return bytes(buf.raw)
    finally:
        # Reset returns queued buffers before releasing their backing storage.
        reset_code=reset(handle)
        unprepare_code=unprepare(handle,c.byref(header),c.sizeof(header)) if prepared else 0
        close_code=close(handle)
        if reset_code or unprepare_code or close_code:
            # Keep driver-referenced buffers alive if a malfunction prevents
            # safe release; no further recording in this process.
            _failed_handles.append((handle,header,buf,fmt))
            raise RuntimeError('Microphone driver cleanup failed; restart JANUS before recording again')
_failed_handles=[]

def capture(seconds,cancelled=None,*,approved=False,backend=native_capture):
    if approved is not True:raise PermissionError('Explicit microphone capture approval required')
    if _failed_handles:raise RuntimeError('Restart JANUS before recording again')
    duration(seconds);stopped(cancelled)
    data=backend(seconds,cancelled);stopped(cancelled)
    return wav_bytes(data,seconds)

def save(root,relative,excluded,payload,seconds,*,approved=False):
    if approved is not True:raise PermissionError('Explicit audio save approval required')
    root=Path(root).resolve(strict=True);excluded=exclusions(excluded);duration(seconds)
    if not isinstance(payload,bytes) or len(payload)!=44+RATE*2*seconds:raise ValueError('Unexpected bounded recording')
    with wave.open(io.BytesIO(payload),'rb') as f:
        if (f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getnframes(),f.getcomptype())!=(1,2,RATE,RATE*seconds,'NONE'):
            raise ValueError('Unexpected PCM format')
    def target():return guard.path_for(root,relative,excluded,{'.wav'},exists=False)
    digest=guard.publish(payload,target(),target)
    return {'status':'recording_saved','output':relative,'sha256':digest,'seconds':seconds,'sample_rate':RATE,'channels':1,'transcribed':False}
