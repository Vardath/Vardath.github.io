"""Cooperative background file-transfer throttle for DeepThorT's work engine.

IMPORTANT: this is NOT a disk busy-time cap and does not constrain unrelated
I/O done by the ONNX runtime, Git, build tools, paging, or other child processes.
Use this for explicitly controlled bulk reads/copies/writes; the work engine
must pause other disk-heavy jobs when a game is detected.
"""
from __future__ import annotations
import ctypes
from ctypes import wintypes
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Callable


def configured_game_names(path: str | Path) -> frozenset[str]:
    p = Path(path)
    if not p.exists():
        return frozenset()
    return frozenset(line.strip().casefold() for line in p.read_text(encoding='utf-8').splitlines()
                     if line.strip() and not line.lstrip().startswith('#'))


def _windows_process_names() -> frozenset[str]:
    """Enumerate executable names through native Win32 APIs.

    Never start tasklist.exe, PowerShell, cmd.exe or any other child process.
    The old tasklist polling spawned a *visible console window* every few
    seconds from the GUI-subsystem DeepThorT.exe and stole keyboard focus.
    """
    if os.name != 'nt':
        return frozenset()

    # Win32 PROCESSENTRY32W layout; ULONG_PTR is pointer-sized on x86/x64.
    class ProcessEntry32W(ctypes.Structure):
        _fields_ = (
            ('dwSize', wintypes.DWORD),
            ('cntUsage', wintypes.DWORD),
            ('th32ProcessID', wintypes.DWORD),
            ('th32DefaultHeapID', ctypes.c_size_t),
            ('th32ModuleID', wintypes.DWORD),
            ('cntThreads', wintypes.DWORD),
            ('th32ParentProcessID', wintypes.DWORD),
            ('pcPriClassBase', wintypes.LONG),
            ('dwFlags', wintypes.DWORD),
            ('szExeFile', wintypes.WCHAR * 260),
        )

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    snapshot = kernel32.CreateToolhelp32Snapshot
    snapshot.argtypes = (wintypes.DWORD, wintypes.DWORD)
    snapshot.restype = wintypes.HANDLE
    first = kernel32.Process32FirstW
    first.argtypes = (wintypes.HANDLE, ctypes.POINTER(ProcessEntry32W))
    first.restype = wintypes.BOOL
    next_entry = kernel32.Process32NextW
    next_entry.argtypes = (wintypes.HANDLE, ctypes.POINTER(ProcessEntry32W))
    next_entry.restype = wintypes.BOOL
    close = kernel32.CloseHandle
    close.argtypes = (wintypes.HANDLE,)
    close.restype = wintypes.BOOL

    from .resource_policy import game_library_path
    open_process=kernel32.OpenProcess
    open_process.argtypes=(wintypes.DWORD,wintypes.BOOL,wintypes.DWORD)
    open_process.restype=wintypes.HANDLE
    query_path=kernel32.QueryFullProcessImageNameW
    query_path.argtypes=(wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD))
    query_path.restype=wintypes.BOOL
    # TH32CS_SNAPPROCESS = 0x00000002. Does not request elevated privileges.
    handle = snapshot(0x00000002, 0)
    if not handle or handle == ctypes.c_void_p(-1).value:
        raise OSError(ctypes.get_last_error(), 'Could not inspect running programs')
    try:
        entry = ProcessEntry32W()
        entry.dwSize = ctypes.sizeof(entry)
        if not first(handle, ctypes.byref(entry)):
            raise OSError(ctypes.get_last_error(), 'Could not enumerate processes')
        names = set()
        inspected=0
        library_game=False
        while True:
            if entry.szExeFile:
                names.add(entry.szExeFile.casefold())
                if not library_game and inspected<512 and entry.th32ProcessID>4:
                    inspected+=1
                    proc=open_process(0x1000,False,entry.th32ProcessID)
                    if proc:
                        try:
                            buf=ctypes.create_unicode_buffer(32768)
                            size=wintypes.DWORD(len(buf))
                            if query_path(proc,0,buf,ctypes.byref(size)) and game_library_path(buf.value):
                                library_game=True
                        finally:close(proc)
            if not next_entry(handle, ctypes.byref(entry)):
                if ctypes.get_last_error()!=18:raise OSError(ctypes.get_last_error(),'Incomplete process snapshot')
                break
        if library_game:names.add(':known-game-library:')
        return frozenset(names)
    finally:
        close(handle)


def games_running(game_names: frozenset[str]) -> bool:
    """Detect configured games without spawning a console or stealing focus.

    On Windows API failure, fail safe: pause background disk operations until
    a subsequent check succeeds rather than assuming no game is running.
    """
    if os.name != 'nt':
        return False
    try:
        names=_windows_process_names()
        return ':known-game-library:' in names or not names.isdisjoint(game_names)
    except (OSError, AttributeError, ValueError):
        return True


# Preserve the existing state reserve. The larger install reserve was
# previously used by the desktop installer; neither is a disk throughput cap.
STATE_RESERVE_BYTES=150_000_000
INSTALL_RESERVE_BYTES=1024**3

def storage_pressure(state,project=None,*,install=False,app_root=None,temp=None,usage=None):
    """Measure actual target filesystem free space; do not walk or delete files.

    No arbitrary path is substituted for a missing project. A failed measurement
    is unknown, not evidence of sufficient capacity.
    """
    probe=usage or shutil.disk_usage
    reserve=INSTALL_RESERVE_BYTES if install else STATE_RESERVE_BYTES
    targets={'state':state,'temporary':temp if temp is not None else tempfile.gettempdir()}
    if project is not None and str(project) not in ('','(general)'):targets['project']=project
    if app_root is not None:targets['application']=app_root
    rows={}
    for label,value in targets.items():
        try:
            path=Path(value).resolve(strict=True)
            if not path.is_dir():raise OSError('Target not a directory')
            free=probe(path).free
            if type(free) is not int or free<0:raise ValueError('Invalid capacity')
            rows[label]={'free_bytes':free,'status':'low' if free<reserve else 'ready'}
        except (OSError,ValueError,TypeError,RuntimeError):
            rows[label]={'free_bytes':None,'status':'unknown'}
    blocked=[label for label,row in rows.items() if row['status']!='ready']
    return {'ready':not blocked,'reserve_bytes':reserve,'targets':rows,'blocked':blocked,
            'cleanup_performed':False,'io_cap_enforced':False}

def require_storage(state,project=None,**kwargs):
    report=storage_pressure(state,project,**kwargs)
    if not report['ready']:
        detail=', '.join(label+' ('+report['targets'][label]['status']+')' for label in report['blocked'])
        raise ValueError('Storage pressure: '+detail+'; reserve '+str(report['reserve_bytes'])+' bytes. Free space or restore access; no automatic deletion.')
    return report

class DiskGate:
    def __init__(self, bytes_per_second: int = 1_048_576,
                 game_names_path: str | Path = 'game_executables.txt',
                 game_flag: str | Path = 'state/game-active.flag',
                 game_probe: Callable[[], bool] | None = None):
        if not 1 <= bytes_per_second <= 10 * 1024 * 1024:
            raise ValueError('Background disk work limit must be 1..10 MiB/s')
        self.bytes_per_second = bytes_per_second
        self.game_flag = Path(game_flag)
        self.game_names_path = Path(game_names_path)
        self.game_probe = game_probe
        self._next_check = 0.0
        self._last_result = False
        self._next_transfer = time.monotonic()

    def gaming(self) -> bool:
        if self.game_flag.is_file():
            return True
        now = time.monotonic()
        if now >= self._next_check:
            try:
                self._last_result = (self.game_probe() if self.game_probe is not None else
                                     games_running(configured_game_names(self.game_names_path)))
            except (OSError,ValueError,RuntimeError,TypeError):self._last_result=True
            self._next_check = now + 5.0
        return self._last_result

    def wait_for_non_game(self) -> None:
        while self.gaming():
            time.sleep(2.0)

    def pace(self, total_io_bytes: int) -> None:
        """Throttle self-controlled bulk I/O (read + write bytes), not disk busy time."""
        if total_io_bytes < 0:
            raise ValueError('I/O byte count must not be negative')
        self.wait_for_non_game()
        now = time.monotonic()
        self._next_transfer = max(now, self._next_transfer) + total_io_bytes / self.bytes_per_second
        remaining = self._next_transfer - now
        if remaining > 0:
            time.sleep(remaining)

    def copy_file(self, source: str | Path, destination: str | Path,
                  chunk_size: int = 64 * 1024) -> None:
        if not 1 <= chunk_size <= 64 * 1024:
            raise ValueError('Chunk size must be <= 64 KiB')
        self.wait_for_non_game()
        with open(source, 'rb') as src, open(destination, 'wb') as dst:
            while True:
                self.wait_for_non_game()
                chunk = src.read(chunk_size)
                if not chunk:
                    return
                self.pace(len(chunk) * 2)  # Account for both read + write
                dst.write(chunk)
