"""Fail-closed Windows Job-Object supervisor for the desktop application.

Invoked from the GUI-subsystem DeepThorT.exe. Never opens a terminal.
"""
from __future__ import annotations
import ctypes
import os
import sys
import traceback
from pathlib import Path
from deepthort_local.win_cpu_cap import run_capped,MAX_CPU_PERCENT,MAX_RAM_PERCENT
from deepthort_local.flight_recorder import record, install_crash_hooks
from deepthort_local.resource_policy import AutomaticResources, HIGH_RESERVE
from deepthort_local.disk_gate import DiskGate

if __name__ == '__main__':
    base = Path(__file__).resolve().parent
    install_crash_hooks(base / 'state', 'launcher')
    record(base / 'state','launcher','launcher_started',cpu_cap=MAX_CPU_PERCENT,ram_cap=MAX_RAM_PERCENT)
    policy=AutomaticResources()
    games=DiskGate(game_names_path=base/'game_executables.txt',game_flag=base/'state'/'game-active.flag')
    def choose(available,total):
        return policy.choose(games.gaming(),available,total)
    def event(message):
        record(base/'state','launcher','resource_profile',detail=message)
    try:
        result = run_capped([sys.executable, str(base / 'desktop_app.py')],
                            cwd=str(base), percent=MAX_CPU_PERCENT, ram_percent=MAX_RAM_PERCENT,
                            free_reserve_percent=HIGH_RESERVE,cpu_policy=choose,policy_event=event)
    except BaseException:
        details = traceback.format_exc()
        record(base/'state','launcher','launcher_exception',level='ERROR',stack=details[-12000:])
        try:
            target = base / 'state' / 'launch-error.txt'
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(details,encoding='utf-8')
        except OSError:
            pass
        if os.name=='nt':
            try:
                ctypes.windll.user32.MessageBoxW(0,
                    'DeepThorT could not start within the automatic 50–85% CPU / up to 80% RAM-sized commit limits.\n\n'
                    + details[-1250:] + '\n\nDetails: state\\launch-error.txt',
                    'DeepThorT - Startup Error',0x10)
            except Exception:
                pass
        sys.exit(1)
    if result != 0 and os.name == 'nt':
        try:
            ctypes.windll.user32.MessageBoxW(0,
                'DeepThorT desktop exited during startup.\n\n'
                'Check state\\launch-error.txt for any recorded details.\n'
                'The resource caps were not bypassed.',
                'DeepThorT - Desktop stopped', 0x10)
        except Exception:
            pass
    sys.exit(result)
