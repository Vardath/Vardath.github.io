"""Verify inherited Windows cap and enclose all three resident model children."""
import ctypes
from ctypes import wintypes
from contextlib import contextmanager
import os
import subprocess
from .win_cpu_cap import (MemoryStatus,CpuRate,ExtendedLimitInfo,StartupInfo,ProcessInfo,
    CPU_RATE_CONTROL_ENABLE,CPU_RATE_CONTROL_HARD_CAP,JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    JOB_OBJECT_LIMIT_JOB_MEMORY,JobObjectExtendedLimitInformation,JobObjectCpuRateControlInformation,
    CREATE_SUSPENDED,CREATE_NO_WINDOW,IDLE_PRIORITY_CLASS)

def kernel():
    if os.name!='nt':raise RuntimeError('Windows hard cap required')
    return ctypes.WinDLL('kernel32',use_last_error=True)
def fn(k,name,args,result):
    f=getattr(k,name);f.argtypes=args;f.restype=result;return f
def check(ok,label):
    if not ok:raise OSError(ctypes.get_last_error(),label+' failed; no uncapped launch')
def verify_root_cap():
    k=kernel()
    query=fn(k,'QueryInformationJobObject',[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p],wintypes.BOOL)
    limits=ExtendedLimitInfo();cpu=CpuRate();mem=MemoryStatus();mem.dwLength=ctypes.sizeof(mem)
    check(fn(k,'GlobalMemoryStatusEx',[ctypes.POINTER(MemoryStatus)],wintypes.BOOL)(ctypes.byref(mem)),'Memory inspection')
    check(query(None,JobObjectExtendedLimitInformation,ctypes.byref(limits),ctypes.sizeof(limits),None),'Inherited job limits')
    check(query(None,JobObjectCpuRateControlInformation,ctypes.byref(cpu),ctypes.sizeof(cpu),None),'Inherited CPU cap')
    required=CPU_RATE_CONTROL_ENABLE|CPU_RATE_CONTROL_HARD_CAP
    if ((cpu.ControlFlags&required)!=required or not 1<=cpu.CpuRate<=3000
            or not limits.BasicLimitInformation.LimitFlags&JOB_OBJECT_LIMIT_JOB_MEMORY
            or not 0<limits.JobMemoryLimit<=mem.ullTotalPhys*30//100
            or not limits.BasicLimitInformation.LimitFlags&JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE):
        raise RuntimeError('Inherited job is not the required CPU/commit cap')
    return int(limits.JobMemoryLimit),int(mem.ullAvailPhys),int(mem.ullTotalPhys)
@contextmanager
def child_server(command,cwd):
    verify_root_cap()
    k=kernel();H=wintypes.HANDLE;D=wintypes.DWORD;P=ctypes.c_void_p
    create_job=fn(k,'CreateJobObjectW',[P,wintypes.LPCWSTR],H)
    set_job=fn(k,'SetInformationJobObject',[H,ctypes.c_int,P,D],wintypes.BOOL)
    create=fn(k,'CreateProcessW',[wintypes.LPCWSTR,wintypes.LPWSTR,P,P,wintypes.BOOL,D,P,wintypes.LPCWSTR,ctypes.POINTER(StartupInfo),ctypes.POINTER(ProcessInfo)],wintypes.BOOL)
    assign=fn(k,'AssignProcessToJobObject',[H,H],wintypes.BOOL)
    resume=fn(k,'ResumeThread',[H],D)
    wait=fn(k,'WaitForSingleObject',[H,D],D)
    kill=fn(k,'TerminateProcess',[H,wintypes.UINT],wintypes.BOOL)
    close=fn(k,'CloseHandle',[H],wintypes.BOOL)
    job=create_job(None,None);check(job,'Create nested cleanup job')
    proc=ProcessInfo();launched=False
    try:
        limits=ExtendedLimitInfo()
        limits.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        check(set_job(job,JobObjectExtendedLimitInformation,ctypes.byref(limits),ctypes.sizeof(limits)),'Set cleanup policy')
        si=StartupInfo();si.cb=ctypes.sizeof(si)
        cmd=ctypes.create_unicode_buffer(subprocess.list2cmdline(command))
        check(create(command[0],cmd,None,None,False,CREATE_SUSPENDED|CREATE_NO_WINDOW|IDLE_PRIORITY_CLASS,
                     None,str(cwd),ctypes.byref(si),ctypes.byref(proc)),'Create suspended model')
        launched=True
        check(assign(job,proc.hProcess),'Assign model to nested cleanup job')
        if resume(proc.hThread)==0xFFFFFFFF:raise OSError('Model resume failed')
        yield int(proc.dwProcessId),lambda:wait(proc.hProcess,0)==258
    finally:
        if launched:
            kill(proc.hProcess,1);wait(proc.hProcess,15000)
            close(proc.hThread);close(proc.hProcess)
        close(job)
