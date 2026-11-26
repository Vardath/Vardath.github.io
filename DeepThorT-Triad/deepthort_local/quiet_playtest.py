"""Quiet *headless* scene-simulation supervisor, deliberately not visual playtesting.

Windows: process inherits the parent DeepThorT.exe's single CPU/memory Job Object.
No extra 50% allocation is created. Never spawn a GUI game as a hidden process;
CREATE_NO_WINDOW is not sufficient to hide a GUI application. A headless Godot
build has a dummy display/audio backend and cannot verify rendering, collision
appearance, player input, docking or actual gameplay quality.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

PLAYTEST_FRAMES = 360
PLAYTEST_SECONDS = 120
MAX_HISTORY = 30

class QuietPlaytestError(ValueError):
    pass


def is_capped_windows_process(*, os_name: str | None = None, probe=None) -> bool:
    """Fail-closed guard: Windows parent must already be in a limiting job.

    Job membership alone does NOT prove that the right 50% CPU limits are set;
    QueryInformationJobObject checks the job's active hard CPU cap. This guard
    does not run under the uncapped development/test flag.
    """
    if (os.name if os_name is None else os_name) != 'nt':
        return False
    if os.environ.get('DEEPTHORT_UNCAPPED_TEST'):
        return False
    if probe is not None:
        return bool(probe())
    try:
        from .triad_job import verify_root_cap
        verify_root_cap()
        return True
    except (OSError,RuntimeError,AttributeError,ValueError,TypeError):
        return False


def quiet_creationflags(*, os_name: str | None = None) -> int:
    """No console, idle priority. Only use with genuine headless tool arguments."""
    if (os.name if os_name is None else os_name) != 'nt':
        return 0
    return getattr(subprocess,'CREATE_NO_WINDOW',0x08000000) | getattr(subprocess,'IDLE_PRIORITY_CLASS',0x00000040)


@dataclass(frozen=True)
class QuietScenePlan:
    project: str
    argv: tuple[str,...]
    main_scene: str
    seconds: int = PLAYTEST_SECONDS
    kind: str = 'godot_headless_scene'

    def display(self):
        return f'Godot scene simulation ({PLAYTEST_FRAMES} frames; limit {self.seconds}s): {self.main_scene}'


def plan_godot_scene(project: str | Path, executable: str | Path,
                     *, frames: int = PLAYTEST_FRAMES) -> QuietScenePlan:
    """Fixed Godot CLI; never accept a model/diagnostic supplied command.

    Only run projects with a declared main scene, not a randomly selected scene.
    Explicit user action is required; this may execute scripts from that project
    with the user's rights, and is not a sandbox.
    """
    if not 1 <= frames <= PLAYTEST_FRAMES:
        raise QuietPlaytestError('Invalid headless frame budget')
    root=Path(project)
    try:
        if root.is_symlink() or not root.is_dir():
            raise QuietPlaytestError('Project must be a real directory')
        root=root.resolve(strict=True)
        config=root/'project.godot'
        if config.is_symlink() or not config.is_file() or config.stat().st_size>2_000_000:
            raise QuietPlaytestError('No regular Godot project configuration')
        source=config.read_text(encoding='utf-8-sig')
        in_section=False
        scene=''
        for raw in source.splitlines():
            line=raw.strip()
            if line.startswith('[') and line.endswith(']'):
                in_section=line=='[application]'
            elif in_section:
                m=re.fullmatch(r'run/main_scene\s*=\s*"([^"\r\n]+)"\s*(?:;.*)?',line)
                if m:
                    scene=m.group(1)
                    break
        if not scene or not (scene.startswith('res://') or scene.startswith('uid://')):
            raise QuietPlaytestError('A main scene must be explicitly declared in project.godot')
        if scene.startswith('res://'):
            relative=scene[6:]
            candidate=root/relative
            if (not relative or '..' in Path(relative).parts or candidate.is_symlink() or
                not candidate.is_file() or not candidate.resolve(strict=True).is_relative_to(root)):
                raise QuietPlaytestError('Declared main scene is missing, outside project, or a symlink')
        exe=Path(executable)
        name=exe.name.casefold()
        if not (name in ('godot.exe','godot_console.exe','godot') or
                re.fullmatch(r'godot_v[0-9][a-z0-9._-]*\.exe',name)):
            raise QuietPlaytestError('Use a recognised Godot executable, not an arbitrary program')
        if exe.is_symlink() or not exe.is_file():
            raise QuietPlaytestError('Godot executable must be an existing regular file')
        exe=exe.resolve(strict=True)
    except (OSError,UnicodeError) as exc:
        raise QuietPlaytestError(str(exc)) from exc
    argv=(str(exe),'--headless','--path',str(root),'--quit-after',str(frames))
    return QuietScenePlan(str(root),argv,scene)


class QuietTestStore:
    """Atomic, bounded audit. Stale running attempts never replay automatically."""
    def __init__(self,path: str | Path):
        self.path=Path(path)
        self._lock=threading.RLock()

    def _read(self):
        try:
            data=json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data,dict) or data.get('schema')!='deepthort-quiet-v44' or not isinstance(data.get('history'),list):
                raise QuietPlaytestError('Quiet test audit has an unexpected schema')
            return data
        except FileNotFoundError:
            return {'schema':'deepthort-quiet-v44','active':None,'history':[]}
        except (OSError,ValueError) as exc:
            raise QuietPlaytestError('Quiet test audit is unreadable; refusing a new launch') from exc

    def _write(self, data):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        p=self.path.with_suffix('.tmp')
        p.write_text(json.dumps(data,indent=2,sort_keys=True),encoding='utf-8')
        os.replace(p,self.path)

    def interrupt_stale(self):
        with self._lock:
            data=self._read()
            if data['active']:
                row=data['active']
                row.update(status='interrupted_unknown',finished_at=datetime.now(timezone.utc).isoformat())
                data['history'].append(row)
                data['history']=data['history'][-MAX_HISTORY:]
                data['active']=None
                self._write(data)
                return row
        return None

    def begin(self,plan:QuietScenePlan):
        with self._lock:
            data=self._read()
            if data['active']:
                raise QuietPlaytestError('Another quiet test is in progress or needs interruption review')
            receipt={'kind':plan.kind,'project':plan.project,'main_scene':plan.main_scene,
                     'argv_sha256':hashlib.sha256(json.dumps(plan.argv).encode()).hexdigest(),
                     'status':'running','started_at':datetime.now(timezone.utc).isoformat(),
                     'timeout_seconds':plan.seconds}
            data['active']=receipt
            self._write(data)
            return dict(receipt)

    def finish(self,exit_code:int|None, *, lines:Sequence[str]=(), stopped:bool=False,error:str='',preempted:str=''):
        with self._lock:
            data=self._read()
            if not data['active']:
                return None
            row=data['active']
            row.update(status=('preempted' if preempted else 'stopped' if stopped else 'launch_failed' if error else
                               'headless_smoke_passed' if exit_code==0 else 'headless_smoke_failed'),
                       exit_code=exit_code,finished_at=datetime.now(timezone.utc).isoformat(),
                       detail=str(preempted or error)[:300],lines=[str(x)[:350] for x in list(lines)[-40:]])
            data['history'].append(row)
            data['history']=data['history'][-MAX_HISTORY:]
            data['active']=None
            self._write(data)
            return dict(row)

    def snapshot(self):
        with self._lock:
            return self._read()


class QuietPressureGuard:
    """Yield to foreground games on actual sustained CPU or RAM pressure.

    A quiet scene can run while another game is detected. This guard does not
    claim a GPU cap or freeze/suspend arbitrary foreign GUI game processes.
    """
    def __init__(self):
        self.busy_samples=0

    def should_preempt(self, *, game_active:bool, cpu_busy_percent:float|None,
                       ram_available_percent:float|None) -> str:
        if ram_available_percent is not None and ram_available_percent < 10:
            return 'RAM reserve below 10%; stopping background scene for foreground priority'
        if not game_active:
            self.busy_samples=0
            return ''
        if ram_available_percent is None:
            return 'Cannot verify foreground memory availability; stopping quiet test'
        if cpu_busy_percent is None:
            return ''  # First CPU sample is a warmup; RAM is independently available.
        if cpu_busy_percent >= 90:
            self.busy_samples+=1
        else:
            self.busy_samples=0
        if self.busy_samples>=3:
            return 'System CPU stayed above 90% during another game; stopping quiet test'
        return ''


class WindowsPressureSampler:
    """Native read-only system snapshot; no subprocesses, privileges or dependencies."""
    def __init__(self):
        self.previous=None

    def read(self):
        if os.name!='nt':
            return (None,None)
        try:
            from ctypes import wintypes
            from .win_cpu_cap import MemoryStatus
            kernel=ctypes.WinDLL('kernel32',use_last_error=True)
            memory=MemoryStatus();memory.dwLength=ctypes.sizeof(memory)
            memfn=kernel.GlobalMemoryStatusEx
            memfn.argtypes=[ctypes.POINTER(MemoryStatus)]
            memfn.restype=wintypes.BOOL
            if not memfn(ctypes.byref(memory)) or memory.ullTotalPhys<=0:
                return (None,None)
            class FT(ctypes.Structure):
                _fields_=[('low',wintypes.DWORD),('high',wintypes.DWORD)]
            gettimes=kernel.GetSystemTimes
            gettimes.argtypes=[ctypes.POINTER(FT)]*3
            gettimes.restype=wintypes.BOOL
            idle=FT();kernel_t=FT();user=FT()
            if not gettimes(ctypes.byref(idle),ctypes.byref(kernel_t),ctypes.byref(user)):
                return (None,100*memory.ullAvailPhys/memory.ullTotalPhys)
            combine=lambda x:(x.high<<32)|x.low
            current=(combine(idle),combine(kernel_t)+combine(user))
            prev=self.previous
            self.previous=current
            busy=None
            if prev:
                di=current[0]-prev[0];dt=current[1]-prev[1]
                if dt>0 and di>=0:
                    busy=max(0.0,min(100.0,(1-di/dt)*100))
            return (busy,100*memory.ullAvailPhys/memory.ullTotalPhys)
        except (OSError,AttributeError,ValueError,TypeError):
            return (None,None)
