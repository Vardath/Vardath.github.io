"""Low-overhead Windows process CPU and memory sampling for visible activity.

Reports only explicitly tracked processes. Job caps are separate enforcement.
"""
from __future__ import annotations
import ctypes, os, time
from ctypes import wintypes

PROCESS_QUERY_LIMITED_INFORMATION=0x1000
PROCESS_VM_READ=0x0010

class FILETIME(ctypes.Structure):
    _fields_=[('lo',wintypes.DWORD),('hi',wintypes.DWORD)]

class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD),
       ('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),
       ('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),
       ('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),
       ('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t),
       ('PrivateUsage',ctypes.c_size_t)]

def sample_process(pid:int):
    if os.name!='nt' or not pid or pid<=0:return None
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    psapi=ctypes.WinDLL('psapi',use_last_error=True)
    openproc=kernel.OpenProcess;openproc.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];openproc.restype=wintypes.HANDLE
    close=kernel.CloseHandle;close.argtypes=[wintypes.HANDLE];close.restype=wintypes.BOOL
    times=kernel.GetProcessTimes;times.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(FILETIME)]*4)];times.restype=wintypes.BOOL
    memfn=psapi.GetProcessMemoryInfo;memfn.argtypes=[wintypes.HANDLE,ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),wintypes.DWORD];memfn.restype=wintypes.BOOL
    h=openproc(PROCESS_QUERY_LIMITED_INFORMATION|PROCESS_VM_READ,False,pid)
    if not h:return None
    try:
        creation=FILETIME();end=FILETIME();kernel_time=FILETIME();user_time=FILETIME()
        if not times(h,ctypes.byref(creation),ctypes.byref(end),ctypes.byref(kernel_time),ctypes.byref(user_time)):
            return None
        mem=PROCESS_MEMORY_COUNTERS_EX();mem.cb=ctypes.sizeof(mem)
        if not memfn(h,ctypes.byref(mem),mem.cb):return None
        convert=lambda f: ((f.hi<<32)|f.lo)/1e7
        return {'pid':pid,'cpu_seconds':convert(kernel_time)+convert(user_time),
                'working_set_bytes':int(mem.WorkingSetSize),'private_bytes':int(mem.PrivateUsage)}
    finally:close(h)

class Meter:
    def __init__(self):self.previous={}
    def read(self,pids:dict[str,int]) -> list[dict]:
        now=time.monotonic();results=[];fresh={}
        for name,pid in pids.items():
            info=sample_process(pid)
            if not info:continue
            old=self.previous.get(pid)
            pct=0.0
            if old and now>old[0]:
                pct=max(0,(info['cpu_seconds']-old[1])/(now-old[0])/(os.cpu_count() or 1)*100)
            info.update(name=name,system_cpu_percent=pct)
            results.append(info)
            fresh[pid]=(now,info['cpu_seconds'])
        self.previous=fresh
        return results
