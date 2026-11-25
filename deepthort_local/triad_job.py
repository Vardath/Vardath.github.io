"""Verify inherited Windows cap and enclose all three resident model children."""
import ctypes
from ctypes import wintypes
from contextlib import contextmanager
import os
import subprocess
from pathlib import Path
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
def in_job(k,process,job):
    member=wintypes.BOOL()
    check(fn(k,'IsProcessInJob',[wintypes.HANDLE,wintypes.HANDLE,ctypes.POINTER(wintypes.BOOL)],wintypes.BOOL)(
        process,job,ctypes.byref(member)),'Process job membership')
    return bool(member.value)

def verify_root_cap():
    k=kernel()
    import re
    name=os.environ.get('DEEPTHORT_TRIAD_ROOT_JOB','')
    if not re.fullmatch(r'Local\\DeepThorT-Triad-[0-9a-f]{48}',name):
        raise RuntimeError('Named shared Triad Job Object missing; restart with START TRIAD.cmd')
    H=wintypes.HANDLE
    open_job=fn(k,'OpenJobObjectW',[wintypes.DWORD,wintypes.BOOL,wintypes.LPCWSTR],H)
    close=fn(k,'CloseHandle',[H],wintypes.BOOL)
    job=open_job(0x0004,False,name)  # JOB_OBJECT_QUERY only
    check(job,'Open shared root Job Object')
    try:
        current=fn(k,'GetCurrentProcess',[],H)()
        if not in_job(k,current,job):raise RuntimeError('Process is outside the shared Triad job')
        query=fn(k,'QueryInformationJobObject',[H,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p],wintypes.BOOL)
        limits=ExtendedLimitInfo();cpu=CpuRate();mem=MemoryStatus();mem.dwLength=ctypes.sizeof(mem)
        check(fn(k,'GlobalMemoryStatusEx',[ctypes.POINTER(MemoryStatus)],wintypes.BOOL)(ctypes.byref(mem)),'Memory inspection')
        check(query(job,JobObjectExtendedLimitInformation,ctypes.byref(limits),ctypes.sizeof(limits),None),'Inherited job limits')
        check(query(job,JobObjectCpuRateControlInformation,ctypes.byref(cpu),ctypes.sizeof(cpu),None),'Inherited CPU cap')
        required=CPU_RATE_CONTROL_ENABLE|CPU_RATE_CONTROL_HARD_CAP
        if ((cpu.ControlFlags&required)!=required or not 1<=cpu.CpuRate<=3500
                or not limits.BasicLimitInformation.LimitFlags&JOB_OBJECT_LIMIT_JOB_MEMORY
                or not 0<limits.JobMemoryLimit<=mem.ullTotalPhys*35//100
                or not limits.BasicLimitInformation.LimitFlags&JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE):
            raise RuntimeError('Inherited job is not the required CPU/commit cap')
        return int(limits.JobMemoryLimit),int(mem.ullAvailPhys),int(mem.ullTotalPhys)
    finally:close(job)
@contextmanager
def child_server(command,cwd,log_path):
    verify_root_cap()
    import msvcrt
    log_path=Path(log_path)
    log_path.parent.mkdir(parents=True,exist_ok=True)
    k=kernel();H=wintypes.HANDLE;D=wintypes.DWORD;P=ctypes.c_void_p
    create_job=fn(k,'CreateJobObjectW',[P,wintypes.LPCWSTR],H)
    set_job=fn(k,'SetInformationJobObject',[H,ctypes.c_int,P,D],wintypes.BOOL)
    create=fn(k,'CreateProcessW',[wintypes.LPCWSTR,wintypes.LPWSTR,P,P,wintypes.BOOL,D,P,wintypes.LPCWSTR,ctypes.POINTER(StartupInfo),ctypes.POINTER(ProcessInfo)],wintypes.BOOL)
    assign=fn(k,'AssignProcessToJobObject',[H,H],wintypes.BOOL)
    resume=fn(k,'ResumeThread',[H],D)
    wait=fn(k,'WaitForSingleObject',[H,D],D)
    kill=fn(k,'TerminateProcess',[H,wintypes.UINT],wintypes.BOOL)
    exit_code=fn(k,'GetExitCodeProcess',[H,ctypes.POINTER(D)],wintypes.BOOL)
    close=fn(k,'CloseHandle',[H],wintypes.BOOL)
    job=create_job(None,None);check(job,'Create nested cleanup job')
    proc=ProcessInfo();launched=False
    try:
        limits=ExtendedLimitInfo()
        limits.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        check(set_job(job,JobObjectExtendedLimitInformation,ctypes.byref(limits),ctypes.sizeof(limits)),'Set cleanup policy')
        si=StartupInfo();si.cb=ctypes.sizeof(si)
        cmd=ctypes.create_unicode_buffer(subprocess.list2cmdline(command))
        # CREATE_NO_WINDOW must not leave C/C++ stdout and stderr invalid.
        # Inherit only the explicitly prepared file handles (Python sockets
        # and the cleanup job are non-inheritable). Reset inheritability
        # before resuming the process.
        with log_path.open('wb',buffering=0) as output,open(os.devnull,'rb',buffering=0) as input_file:
            out=msvcrt.get_osfhandle(output.fileno())
            inp=msvcrt.get_osfhandle(input_file.fileno())
            si.dwFlags=0x100  # STARTF_USESTDHANDLES
            si.hStdInput=inp;si.hStdOutput=out;si.hStdError=out
            try:
                os.set_handle_inheritable(out,True)
                os.set_handle_inheritable(inp,True)
                check(create(command[0],cmd,None,None,True,CREATE_SUSPENDED|CREATE_NO_WINDOW|IDLE_PRIORITY_CLASS,
                             None,str(cwd),ctypes.byref(si),ctypes.byref(proc)),'Create suspended model')
                launched=True
            finally:
                os.set_handle_inheritable(out,False)
                os.set_handle_inheritable(inp,False)
        check(assign(job,proc.hProcess),'Assign model to nested cleanup job')
        if resume(proc.hThread)==0xFFFFFFFF:raise OSError('Model resume failed')
        def alive():
            result=wait(proc.hProcess,0)
            if result not in (0,258):raise OSError(ctypes.get_last_error(),'Native wait failed')
            return result==258
        def code():
            result=D()
            check(exit_code(proc.hProcess,ctypes.byref(result)),'Native exit-code query')
            return int(result.value)
        def failure():
            value=code()
            hints={0xc0000135:'missing DLL or Visual C++ runtime',
                   0xc0000139:'DLL entry point missing',
                   0xc000007b:'invalid executable or DLL architecture',
                   0xc000001d:'unsupported CPU instruction',
                   0xc0000005:'native access violation',
                   0xc0000017:'Windows could not allocate memory',
                   0xc000012d:'Windows commit limit reached'}
            # Only a bounded startup tail, with authentication key redacted.
            with log_path.open('rb') as stream:
                stream.seek(max(0,log_path.stat().st_size-4096))
                tail=stream.read().decode('utf-8',errors='replace').strip()
            if '--api-key' in command:tail=tail.replace(command[command.index('--api-key')+1],'[redacted]')
            if len(command[-1])==64 and all(c in '0123456789abcdef' for c in command[-1]):tail=tail.replace(command[-1],'[redacted]')
            return f'exit 0x{value:08X} ({hints.get(value,"see native log")}); {log_path.name}\n{tail or "(no native output)"}'
        def member(pid):
            if type(pid) is not int or pid<=0:return False
            # Windows venv python.exe may be a redirector. Verify the real
            # serving interpreter is inside this exact child cleanup job.
            handle=fn(k,'OpenProcess',[D,wintypes.BOOL,D],H)(0x0400,False,pid)
            if not handle:return False
            try:return in_job(k,handle,job)
            finally:close(handle)
        alive.code=code
        alive.failure=failure
        alive.member=member
        yield int(proc.dwProcessId),alive
    finally:
        if launched:
            kill(proc.hProcess,1);wait(proc.hProcess,15000)
            close(proc.hThread);close(proc.hProcess)
        close(job)
