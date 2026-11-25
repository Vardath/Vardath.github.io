"""Windows resource supervisor: 35% system CPU and <=35% physical-RAM-sized job commit cap.

A Windows Job Object encloses the child process AND all its descendants;
launch DeepThorT's ROOT process under it to limit the entire application.
Fails closed: never starts the child if the cap cannot be installed.
Windows 8+ desktop; Windows 10 and 11 intended.

The memory limit applies to aggregate committed bytes for managed processes,
not a direct measurement of physical resident memory. The local model uses
ONNX weights may be memory-mapped, so committed memory alone is NOT a strict physical-RAM limit.
Disk active-time cannot be hard-capped by percentage via the supported Windows
10 Job API; heavy disk tasks must use cooperative scheduling and pause for games.
"""
from __future__ import annotations
import ctypes
import os
import subprocess
from ctypes import wintypes
from typing import Callable, Sequence

CPU_RATE_CONTROL_ENABLE = 0x1
CPU_RATE_CONTROL_HARD_CAP = 0x4
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
JOB_OBJECT_LIMIT_PRIORITY_CLASS = 0x00000020
JobObjectExtendedLimitInformation = 9
JobObjectCpuRateControlInformation = 15
CREATE_SUSPENDED = 0x00000004
CREATE_NO_WINDOW = 0x08000000  # Do not create a console for child Python.exe
IDLE_PRIORITY_CLASS = 0x00000040
INFINITE = 0xFFFFFFFF

class MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_uint64), ("ullAvailPhys", ctypes.c_uint64),
        ("ullTotalPageFile", ctypes.c_uint64), ("ullAvailPageFile", ctypes.c_uint64),
        ("ullTotalVirtual", ctypes.c_uint64), ("ullAvailVirtual", ctypes.c_uint64),
        ("ullAvailExtendedVirtual", ctypes.c_uint64),
    ]


def calculate_ram_limit(total_physical: int, available_physical: int,
                        ram_percent: int = 35, free_reserve_percent: int = 10) -> int:
    """Reject launching if model would jeopardise RAM reserved for foreground games.

    JobObjectMemoryLimit caps committed private bytes (not physical working set).
    This preflight permits a smaller capped job under RAM pressure while
    retaining a game-memory reserve;
    but is not itself a dynamic resident memory watchdog.
    """
    if total_physical <= 0 or not 0 <= available_physical <= total_physical:
        raise ValueError("Invalid physical RAM values")
    if not 1 <= ram_percent <= 35 or not 0 <= free_reserve_percent <= 80:
        raise ValueError("RAM cap must be 1..35% and reserve 0..80%")
    ceiling = total_physical * ram_percent // 100
    reserve = total_physical * free_reserve_percent // 100
    # The Job limit is a ceiling, not an allocation. A running foreground
    # game can use much of RAM: allow a smaller *safe* capped job rather than
    # refusing to launch because its full theoretical 35% is unavailable.
    limit = min(ceiling, max(0, available_physical-reserve))
    minimum = min(2 * 1024**3, total_physical // 10)
    if limit < minimum:
        raise RuntimeError(
            f"Not enough available RAM for gaming-safe launch: retain "
            f"{reserve / 2**30:.2f} GiB game reserve and "
            f"{minimum / 2**30:.2f} GiB minimum model capacity; "
            f"only {available_physical / 2**30:.2f} GiB available. "
            "DeepThorT will not force Windows to page out game memory."
        )
    return limit


class CpuRate(ctypes.Structure):
    _fields_ = [("ControlFlags", wintypes.DWORD), ("CpuRate", wintypes.DWORD)]

class IoCounters(ctypes.Structure):
    _fields_ = [("ReadOperationCount", ctypes.c_uint64),
                ("WriteOperationCount", ctypes.c_uint64),
                ("OtherOperationCount", ctypes.c_uint64),
                ("ReadTransferCount", ctypes.c_uint64),
                ("WriteTransferCount", ctypes.c_uint64),
                ("OtherTransferCount", ctypes.c_uint64)]

class BasicLimitInfo(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD)]

class ExtendedLimitInfo(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", BasicLimitInfo),
                ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t)]

class StartupInfo(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR),
                ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR),
                ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD),
                ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD),
                ("dwXCountChars", wintypes.DWORD), ("dwYCountChars", wintypes.DWORD),
                ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
                ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
                ("hStdInput", wintypes.HANDLE), ("hStdOutput", wintypes.HANDLE),
                ("hStdError", wintypes.HANDLE)]

class ProcessInfo(ctypes.Structure):
    _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
                ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]


def run_capped(command: Sequence[str], cwd: str | None = None,
               percent: int = 35, ram_percent: int = 35, free_reserve_percent: int = 10,
               observe: Callable[[int, int, bool], None] | None = None) -> int:
    if os.name != "nt":
        raise RuntimeError("The 35% hard-cap supervisor requires Windows; refusing uncapped launch")
    if not 1 <= percent <= 35:
        raise ValueError("This gaming-safe launcher cannot exceed 35% CPU")
    if not 1 <= ram_percent <= 35:
        raise ValueError("This gaming-safe launcher cannot exceed 35% RAM")
    if not command or not all(isinstance(x, str) and x for x in command):
        raise ValueError("Nonempty argument vector required")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    HANDLE = wintypes.HANDLE
    DWORD = wintypes.DWORD
    LPVOID = ctypes.c_void_p

    def fn(name, argtypes, restype):
        func = getattr(kernel, name)
        func.argtypes, func.restype = argtypes, restype
        return func

    global_mem_status = fn("GlobalMemoryStatusEx", [ctypes.POINTER(MemoryStatus)], wintypes.BOOL)
    mem = MemoryStatus()
    mem.dwLength = ctypes.sizeof(mem)
    if not global_mem_status(ctypes.byref(mem)):
        raise OSError(ctypes.get_last_error(), "GlobalMemoryStatusEx failed; refusing uncapped launch")
    ram_cap_bytes = calculate_ram_limit(mem.ullTotalPhys, mem.ullAvailPhys, ram_percent, free_reserve_percent)
    create_job = fn("CreateJobObjectW", [LPVOID, wintypes.LPCWSTR], HANDLE)
    set_job = fn("SetInformationJobObject", [HANDLE, ctypes.c_int, LPVOID, DWORD], wintypes.BOOL)
    create_process = fn("CreateProcessW", [wintypes.LPCWSTR, wintypes.LPWSTR,
                          LPVOID, LPVOID, wintypes.BOOL, DWORD, LPVOID,
                          wintypes.LPCWSTR, ctypes.POINTER(StartupInfo), ctypes.POINTER(ProcessInfo)], wintypes.BOOL)
    assign = fn("AssignProcessToJobObject", [HANDLE, HANDLE], wintypes.BOOL)
    resume = fn("ResumeThread", [HANDLE], DWORD)
    wait = fn("WaitForSingleObject", [HANDLE, DWORD], DWORD)
    exit_code = fn("GetExitCodeProcess", [HANDLE, ctypes.POINTER(DWORD)], wintypes.BOOL)
    terminate = fn("TerminateProcess", [HANDLE, wintypes.UINT], wintypes.BOOL)
    terminate_job = fn("TerminateJobObject", [HANDLE, wintypes.UINT], wintypes.BOOL)
    close = fn("CloseHandle", [HANDLE], wintypes.BOOL)

    def check(ok, action):
        if not ok:
            raise OSError(ctypes.get_last_error(), f"{action} failed. Child will not run without CPU cap")

    job = create_job(None, None)
    check(job, "CreateJobObjectW")
    process = ProcessInfo()
    launched = False
    try:
        limits = ExtendedLimitInfo()
        limits.BasicLimitInformation.LimitFlags = (JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE |
                                                  JOB_OBJECT_LIMIT_JOB_MEMORY |
                                                  JOB_OBJECT_LIMIT_PRIORITY_CLASS)
        limits.BasicLimitInformation.PriorityClass = IDLE_PRIORITY_CLASS
        limits.JobMemoryLimit = ram_cap_bytes
        check(set_job(job, JobObjectExtendedLimitInformation, ctypes.byref(limits), ctypes.sizeof(limits)), "Set job-wide RAM cap, idle priority and kill-on-close")
        cap = CpuRate(CPU_RATE_CONTROL_ENABLE | CPU_RATE_CONTROL_HARD_CAP, percent * 100)
        check(set_job(job, JobObjectCpuRateControlInformation, ctypes.byref(cap), ctypes.sizeof(cap)), "Set hard 35% CPU cap")
        si = StartupInfo()
        si.cb = ctypes.sizeof(si)
        cmdline = ctypes.create_unicode_buffer(subprocess.list2cmdline(list(command)))
        check(create_process(None, cmdline, None, None, False,
                             CREATE_SUSPENDED | IDLE_PRIORITY_CLASS | CREATE_NO_WINDOW,
                             None, cwd, ctypes.byref(si), ctypes.byref(process)), "Create suspended child")
        launched = True
        try:
            check(assign(job, process.hProcess), "Assign child to capped Job Object")
            if observe:
                observe(job, ram_cap_bytes, False)
            if resume(process.hThread) == 0xFFFFFFFF:
                raise OSError(ctypes.get_last_error(), "ResumeThread failed")
            code = wait(process.hProcess, 5000 if observe else INFINITE)
            while observe and code == 258:  # WAIT_TIMEOUT
                observe(job, ram_cap_bytes, False)
                code = wait(process.hProcess, 5000)
            if code != 0:
                raise OSError(ctypes.get_last_error(), "WaitForSingleObject failed")
            if observe:
                observe(job, ram_cap_bytes, True)
            out = DWORD()
            check(exit_code(process.hProcess, ctypes.byref(out)), "GetExitCodeProcess")
            return int(out.value)
        except BaseException:
            terminate_job(job, 1)
            terminate(process.hProcess, 1)
            raise
    finally:
        if launched:
            close(process.hThread)
            close(process.hProcess)
        close(job)  # Kill-on-close guarantees no escaped descendants.
