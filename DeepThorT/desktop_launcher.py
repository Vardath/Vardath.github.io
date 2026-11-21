"""Fail-closed Windows Job-Object supervisor for the desktop application.

Invoked from the GUI-subsystem DeepThorT.exe. Never opens a terminal.
"""
from __future__ import annotations
import ctypes
import os
import sys
import traceback
from pathlib import Path
from deepthort_local.win_cpu_cap import run_capped
from deepthort_local.flight_recorder import record, install_crash_hooks

if __name__ == '__main__':
    base = Path(__file__).resolve().parent
    install_crash_hooks(base / 'state', 'launcher')
    record(base / 'state','launcher','launcher_started',cpu_cap=20,ram_cap=20)
    try:
        result = run_capped([sys.executable, str(base / 'desktop_app.py')],
                            cwd=str(base), percent=20, ram_percent=20)
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
                    'DeepThorT could not start within the configured 20% CPU / RAM limits.\n\n'
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
