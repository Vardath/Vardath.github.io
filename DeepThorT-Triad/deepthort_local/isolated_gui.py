"""Windows-only, background *visual-process smoke test* on another Win32 desktop.

This is NOT a VM, security sandbox, automated gameplay test or graphics proof.
An explicitly user-approved project-local .exe is started on a separate desktop
(not switched into view). DeepThorT NEVER sends input to either desktop.
The child must inherit the verified current shared Windows Job Object;
a nested kill-on-close job prevents a launched process tree lingering after test.
A foreign GUI engine can fail to render on a non-input desktop; that failure is
reported, not disguised as a successful visual test. No third-party installs.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import threading
import time

from .quiet_playtest import is_capped_windows_process, QuietPressureGuard, WindowsPressureSampler
from .source_security import linked

MAX_RUN_SECONDS = 45
MAX_WINDOWS = 12
MAX_HISTORY = 30


class IsolatedGuiError(ValueError):
    pass


@dataclass(frozen=True)
class IsolatedGuiPlan:
    project: str
    executable: str
    executable_sha256: str
    run_seconds: int = 25
    kind: str = 'isolated_gui_smoke'


def plan_isolated_gui(project: str | Path, executable: str | Path, *, seconds: int = 25) -> IsolatedGuiPlan:
    """Approve one existing project-local Windows binary; no arbitrary command arguments.

    The project is still untrusted native code with the user's own permissions;
    separate desktops prevent foreground input takeover, NOT filesystem access.
    """
    if not isinstance(seconds, int) or isinstance(seconds, bool) or not 1 <= seconds <= MAX_RUN_SECONDS:
        raise IsolatedGuiError('Invalid background GUI test duration')
    try:
        root = Path(project)
        target = Path(executable)
        if not root.is_dir() or not target.is_file() or any(linked(x) for x in (target,*target.parents,root,*root.parents) if x.exists()):
            raise IsolatedGuiError('Use a real project folder and existing executable (not symlinks)')
        root = root.resolve(strict=True)
        target = target.resolve(strict=True)
        if target.suffix.lower() != '.exe' or not target.is_relative_to(root):
            raise IsolatedGuiError('Only .exe programs within the selected project are allowed')
        rel = target.relative_to(root)
        current = root
        for component in rel.parts:
            current = current / component
            if linked(current):
                raise IsolatedGuiError('Symlinks in executable path are not accepted')
        if target.stat().st_size < 1 or target.stat().st_size > 512 * 1024 * 1024:
            raise IsolatedGuiError('Executable size outside safe inspection bounds')
        h = hashlib.sha256()
        with target.open('rb') as src:
            for part in iter(lambda: src.read(1024 * 1024), b''):
                h.update(part)
        return IsolatedGuiPlan(str(root), str(target), h.hexdigest(), seconds)
    except (OSError, RuntimeError) as exc:
        raise IsolatedGuiError('Cannot inspect project executable: ' + str(exc)[:180]) from exc


def assert_plan_unchanged(plan: IsolatedGuiPlan) -> None:
    again = plan_isolated_gui(plan.project, plan.executable, seconds=plan.run_seconds)
    if again != plan:
        raise IsolatedGuiError('Executable or project changed since test approval; refusing launch')


class IsolatedGuiStore:
    """Durable, bounded receipts. Never auto-replay uncertain launches after a crash."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.lock = threading.RLock()

    def _read(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if (not isinstance(data, dict) or data.get('schema') != 'deepthort-isolated-gui-v45'
                    or not isinstance(data.get('history'), list) or 'active' not in data
                    or (data['active'] is not None and not isinstance(data['active'], dict))):
                raise IsolatedGuiError('GUI test audit schema mismatch')
            return data
        except FileNotFoundError:
            return {'schema': 'deepthort-isolated-gui-v45', 'active': None, 'history': []}
        except (OSError, ValueError, TypeError) as exc:
            raise IsolatedGuiError('Unreadable GUI test audit: refusing launch') from exc

    def _write(self, data: dict) -> None:
        if self.path.is_symlink():
            raise IsolatedGuiError('Refusing to write to symlinked GUI audit')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix('.tmp')
        if temp.is_symlink():
            raise IsolatedGuiError('Refusing symlinked GUI audit staging file')
        temp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')
        os.replace(temp, self.path)

    def interrupt_stale(self):
        with self.lock:
            data = self._read()
            if not data['active']:
                return None
            row = data['active']
            row.update(status='interrupted_unknown', finished_at=datetime.now(timezone.utc).isoformat())
            data['history'].append(row)
            data['history'] = data['history'][-MAX_HISTORY:]
            data['active'] = None
            self._write(data)
            return row

    def begin(self, plan: IsolatedGuiPlan):
        with self.lock:
            data = self._read()
            if data['active']:
                raise IsolatedGuiError('Another isolated GUI test has an unresolved receipt')
            row = {'kind': plan.kind, 'project': plan.project,
                   'executable_name': Path(plan.executable).name,
                   'executable_sha256': plan.executable_sha256,
                   'status': 'running', 'started_at': datetime.now(timezone.utc).isoformat(),
                   'max_seconds': plan.run_seconds}
            data['active'] = row
            self._write(data)
            return dict(row)

    def finish(self, result: dict):
        with self.lock:
            data = self._read()
            if not data['active']:
                return None
            row = data['active']
            status = str(result.get('status', 'failed'))
            allowed = ('window_observed', 'no_window', 'exited_nonzero', 'launch_failed',
                       'cancelled', 'preempted', 'interrupted_unknown', 'window_hung')
            raw_windows = result.get('windows', [])
            valid_windows = []
            if isinstance(raw_windows, list):
                for item in raw_windows[:MAX_WINDOWS]:
                    if not isinstance(item, dict):
                        continue
                    coords = item.get('bounds', [])
                    coords = ([int(x) for x in coords] if isinstance(coords, list)
                              and len(coords) == 4 and all(isinstance(x, int) for x in coords) else [])
                    valid_windows.append({'title': str(item.get('title', ''))[:180],
                                          'bounds': coords, 'hung': bool(item.get('hung'))})
            row.update(status=status if status in allowed else 'launch_failed',
                       detail=str(result.get('detail', ''))[:300],
                       process_id=result.get('pid') if isinstance(result.get('pid'), int) else None,
                       exit_code=result.get('exit_code') if isinstance(result.get('exit_code'), int) else None,
                       # Titles and geometry of THE project child only, never other desktops.
                       windows=valid_windows,
                       finished_at=datetime.now(timezone.utc).isoformat())
            data['history'].append(row)
            data['history'] = data['history'][-MAX_HISTORY:]
            data['active'] = None
            self._write(data)
            return dict(row)

    def snapshot(self):
        with self.lock:
            return self._read()


class NativeWin32Desktop:
    """Only executed after the Windows capped-launcher and explicit-click gates.

    The child inherits DeepThorT's existing job. A nested job kills the whole
    test subtree on exit. We never call SwitchDesktop, SendInput, PostMessage,
    SetForegroundWindow, ShowWindow, or inject into any running process.
    """
    def __init__(self):
        if os.name != 'nt':
            raise IsolatedGuiError('Background graphical desktop requires Windows')
        self.k = ctypes.WinDLL('kernel32', use_last_error=True)
        self.u = ctypes.WinDLL('user32', use_last_error=True)
        from .win_cpu_cap import StartupInfo, ProcessInfo, ExtendedLimitInfo
        self.StartupInfo = StartupInfo
        self.ProcessInfo = ProcessInfo
        self.ExtendedLimitInfo = ExtendedLimitInfo

    @staticmethod
    def _fn(lib, name, types, ret):
        fn = getattr(lib, name)
        fn.argtypes = types
        fn.restype = ret
        return fn

    @staticmethod
    def _check(ok, label):
        if not ok:
            raise OSError(ctypes.get_last_error(), label)

    def _windows(self, desktop, pid: int) -> list[dict]:
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, ctypes.c_ssize_t)
        get_pid = self._fn(self.u, 'GetWindowThreadProcessId',
                           [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)], wintypes.DWORD)
        visible = self._fn(self.u, 'IsWindowVisible', [wintypes.HWND], wintypes.BOOL)
        get_title = self._fn(self.u, 'GetWindowTextW',
                             [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int], ctypes.c_int)
        get_rect = self._fn(self.u, 'GetWindowRect',
                            [wintypes.HWND, ctypes.POINTER(wintypes.RECT)], wintypes.BOOL)
        hung = self._fn(self.u, 'IsHungAppWindow', [wintypes.HWND], wintypes.BOOL)
        collected = []

        @callback_type
        def visitor(hwnd, unused):
            owner = wintypes.DWORD()
            get_pid(hwnd, ctypes.byref(owner))
            if owner.value != pid or not visible(hwnd) or len(collected) >= MAX_WINDOWS:
                return True
            title = ctypes.create_unicode_buffer(200)
            get_title(hwnd, title, len(title))
            rect = wintypes.RECT()
            bounds = []
            if get_rect(hwnd, ctypes.byref(rect)):
                bounds = [rect.left, rect.top, rect.right, rect.bottom]
            collected.append({'title': title.value[:180], 'bounds': bounds,
                              'hung': bool(hung(hwnd))})
            return True

        enum = self._fn(self.u, 'EnumDesktopWindows',
                        [wintypes.HANDLE, callback_type, ctypes.c_ssize_t], wintypes.BOOL)
        self._check(enum(desktop, visitor, 0), 'EnumDesktopWindows')
        return collected

    def run(self, plan: IsolatedGuiPlan, stop: threading.Event, *,
            foreground_game=None, pressure=None) -> dict:
        if not is_capped_windows_process():
            raise IsolatedGuiError('Capped DeepThorT.exe is required; refusing uncapped GUI launch')
        from .triad_job import verify_root_cap
        verify_root_cap()
        assert_plan_unchanged(plan)
        if stop.is_set():
            return {'status': 'cancelled', 'detail': 'Stopped before launch', 'windows': []}
        h = wintypes.HANDLE
        d = wintypes.DWORD
        cv = ctypes.c_void_p
        desktop = None
        testjob = None
        proc = self.ProcessInfo()
        created = False
        windows = []
        pid = None
        code = None
        reason = ''
        status = 'launch_failed'
        close = self._fn(self.k, 'CloseHandle', [h], wintypes.BOOL)
        close_desktop = self._fn(self.u, 'CloseDesktop', [h], wintypes.BOOL)
        try:
            create_desktop = self._fn(self.u, 'CreateDesktopW',
                [wintypes.LPCWSTR, wintypes.LPCWSTR, cv, d, d, cv], h)
            name = f'DeepThorT_v45_{os.getpid()}_{secrets.token_hex(7)}'
            # Rights for drawing/enumeration, but not DESKTOP_SWITCHDESKTOP.
            desktop = create_desktop(name, None, None, 0, 0x00CF, None)
            self._check(desktop, 'CreateDesktopW')
            create_job = self._fn(self.k, 'CreateJobObjectW', [cv, wintypes.LPCWSTR], h)
            testjob = create_job(None, None)
            self._check(testjob, 'CreateJobObjectW')
            set_job = self._fn(self.k, 'SetInformationJobObject', [h, ctypes.c_int, cv, d], wintypes.BOOL)
            limits = self.ExtendedLimitInfo()
            limits.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE
            self._check(set_job(testjob, 9, ctypes.byref(limits), ctypes.sizeof(limits)),
                        'Set nested test job kill-on-close')
            if stop.is_set():
                return {'status':'cancelled','detail':'Stopped before native launch','windows':[]}
            create_process = self._fn(self.k, 'CreateProcessW',
                [wintypes.LPCWSTR, wintypes.LPWSTR, cv, cv, wintypes.BOOL, d, cv,
                 wintypes.LPCWSTR, ctypes.POINTER(self.StartupInfo), ctypes.POINTER(self.ProcessInfo)],
                wintypes.BOOL)
            si = self.StartupInfo()
            si.cb = ctypes.sizeof(si)
            si.lpDesktop = name
            cmdline = ctypes.create_unicode_buffer(subprocess.list2cmdline([plan.executable]))
            flags = 0x00000004 | 0x00000040  # CREATE_SUSPENDED | IDLE_PRIORITY_CLASS
            self._check(create_process(str(plan.executable), cmdline, None, None, False,
                    flags, None, str(Path(plan.executable).parent), ctypes.byref(si), ctypes.byref(proc)),
                    'CreateProcessW on isolated desktop')
            created = True
            pid = int(proc.dwProcessId)
            assign = self._fn(self.k, 'AssignProcessToJobObject', [h, h], wintypes.BOOL)
            self._check(assign(testjob, proc.hProcess), 'AssignProcessToJobObject nested cleanup')
            in_job = self._fn(self.k, 'IsProcessInJob',
                              [h, h, ctypes.POINTER(wintypes.BOOL)], wintypes.BOOL)
            member = wintypes.BOOL()
            root_job=self._fn(self.k,'OpenJobObjectW',[d,wintypes.BOOL,wintypes.LPCWSTR],h)(0x0004,False,os.environ['DEEPTHORT_TRIAD_ROOT_JOB'])
            self._check(root_job,'Open exact inherited shared job')
            try:
                for scope in (root_job,testjob):
                    self._check(in_job(proc.hProcess,scope,ctypes.byref(member)),'IsProcessInJob exact scope')
                    self._check(member.value,'Child outside approved job scope')
            finally:close(root_job)
            resume = self._fn(self.k, 'ResumeThread', [h], d)
            self._check(resume(proc.hThread) != 0xffffffff, 'ResumeThread')
            wait = self._fn(self.k, 'WaitForSingleObject', [h, d], d)
            exitcode = self._fn(self.k, 'GetExitCodeProcess',
                                 [h, ctypes.POINTER(d)], wintypes.BOOL)
            sampler = WindowsPressureSampler()
            guard = QuietPressureGuard()
            began = time.monotonic()
            last_check = 0.0
            status = 'no_window'
            while time.monotonic() - began < plan.run_seconds:
                if stop.is_set():
                    status, reason = 'cancelled', 'Stopped by user'
                    break
                if wait(proc.hProcess, 250) == 0:
                    out = d()
                    if exitcode(proc.hProcess, ctypes.byref(out)):
                        code = int(out.value)
                    if code not in (None, 0):
                        status = 'exited_nonzero'
                        reason = 'Executable exited with a nonzero status'
                    break
                now = time.monotonic()
                if now - last_check >= 1.0:
                    last_check = now
                    windows = self._windows(desktop, pid) or windows
                    if any(x['hung'] for x in windows):
                        status, reason = 'window_hung', 'A visible project window became unresponsive'
                        break
                    if windows:
                        status = 'window_observed'
                    game = bool(foreground_game()) if foreground_game else False
                    cpu, ram = sampler.read() if pressure is None else pressure()
                    preempt = guard.should_preempt(game_active=game,
                            cpu_busy_percent=cpu, ram_available_percent=ram)
                    if preempt:
                        status, reason = 'preempted', preempt
                        break
            if status == 'no_window' and not reason:
                reason = 'No visible project-owned window was observed on the isolated desktop'
            if status == 'window_observed' and not reason:
                reason = 'Visible window metadata recorded; no visual rendering or input acceptance proven'
            return {'status': status, 'detail': reason, 'pid': pid,
                    'exit_code': code, 'windows': windows,'shared_root_cap_verified':True,
                    'separate_desktop':True,'foreground_switched':False}
        finally:
            # Terminate even when nested-job assignment failed while suspended.
            # Closing the nested job additionally kills any child descendants.
            if created:
                try:
                    terminate = self._fn(self.k, 'TerminateProcess',
                                         [h, wintypes.UINT], wintypes.BOOL)
                    terminate(proc.hProcess, 1)
                    self._fn(self.k,'WaitForSingleObject',[h,d],d)(proc.hProcess,15000)
                except (OSError, AttributeError):
                    pass
            if testjob:
                close(testjob)
            if created:
                close(proc.hThread)
                close(proc.hProcess)
            if desktop:
                close_desktop(desktop)


def run_isolated_gui(plan: IsolatedGuiPlan, stop: threading.Event,
                     *, foreground_game=None, backend=None) -> dict:
    if stop.is_set():
        return {'status': 'cancelled', 'detail': 'Stopped before launch', 'windows': []}
    if backend is None:
        backend = NativeWin32Desktop()
    return backend.run(plan, stop, foreground_game=foreground_game)
