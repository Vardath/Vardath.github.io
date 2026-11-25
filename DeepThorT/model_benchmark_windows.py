"""Run one offline benchmark under the existing shared Windows Job Object."""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
from shutil import which
import subprocess
import sys
import time

from deepthort_local.disk_gate import configured_game_names, games_running
from deepthort_local.win_cpu_cap import run_capped, ExtendedLimitInfo, CpuRate

ROOT = Path(__file__).resolve().parent


class Accounting(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int64) for name in
                ('user', 'kernel', 'period_user', 'period_kernel')] + [
                (name, wintypes.DWORD) for name in
                ('faults', 'process_count', 'active', 'terminated')]


def production_check():
    names = configured_game_names(ROOT / 'game_executables.txt') | {'deepthort.exe'}
    if games_running(names):
        raise RuntimeError('Game or DeepThorT active, or process inventory unavailable')
    output = subprocess.check_output(['netstat', '-ano', '-p', 'tcp'], text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
    for line in output.splitlines():
        fields = line.split()
        if len(fields) >= 5 and fields[0] == 'TCP' and fields[3] == 'LISTENING':
            if fields[1].rsplit(':', 1)[-1] in ('8765', '8766'):
                raise RuntimeError('Production worker port is active')


def main():
    profiles = json.loads((ROOT/'benchmarks/profiles.json').read_text())
    parser = argparse.ArgumentParser()
    parser.add_argument('profile', choices=profiles)
    parser.add_argument('--suite', choices=['all', 'project', 'project-fenced', 'dual'], default='all')
    args = parser.parse_args()
    if os.name != 'nt':
        raise SystemExit('Windows Job Object required')
    node = which('node')
    if not node:
        raise SystemExit('Node.js not installed')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    mutex = kernel.CreateMutexW
    mutex.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
    mutex.restype = wintypes.HANDLE
    handle = mutex(None, False, 'Local\\DeepThorTModelBenchmark')
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    existing = ctypes.get_last_error() == 183
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    try:
        if existing:
            raise SystemExit('A benchmark is already active in this Windows session')
        production_check()
        query = kernel.QueryInformationJobObject
        query.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p)
        query.restype = wintypes.BOOL
        suffix = '' if args.suite == 'all' else '-' + args.suite
        command = [node, str(ROOT/'model_benchmark.mjs'), args.profile, 'offline', args.suite]
        if args.suite == 'dual':
            if args.profile != 'baseline':
                raise SystemExit('The production worker currently selects the baseline model')
            single = ROOT/'benchmark-local/results/baseline.json'
            if not single.is_file() or not json.loads(single.read_text(encoding='utf-8')).get('complete'):
                raise SystemExit('Complete the single-worker baseline first')
            command = [node, str(ROOT/'model_benchmark_dual.mjs')]
        path = ROOT/'benchmark-local/results'/(args.profile + suffix + '-windows-job.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        def observe(job, requested, finished):
            limits, rate, accounting = ExtendedLimitInfo(), CpuRate(), Accounting()
            for kind, value in ((9, limits), (15, rate), (1, accounting)):
                if not query(job, kind, ctypes.byref(value), ctypes.sizeof(value), None):
                    raise ctypes.WinError(ctypes.get_last_error())
            if (limits.BasicLimitInformation.LimitFlags & 512 == 0 or
                not 0 < limits.JobMemoryLimit <= requested or
                rate.ControlFlags & 5 != 5 or rate.CpuRate != 3500 or
                limits.PeakJobMemoryUsed > limits.JobMemoryLimit):
                raise RuntimeError('Windows Job Object cap readback failed')
            elapsed = time.monotonic() - started
            cpu_time = (accounting.user + accounting.kernel) / 10_000_000
            details = dict(profile=args.profile, suite=args.suite,
                kernel_cpu_hard_cap_percent=rate.CpuRate / 100,
                kernel_job_commit_limit_bytes=limits.JobMemoryLimit,
                kernel_peak_job_commit_bytes=limits.PeakJobMemoryUsed,
                job_cpu_seconds=cpu_time, elapsed_seconds=elapsed,
                mean_system_cpu_percent=100 * cpu_time / (elapsed * (os.cpu_count() or 1)),
                finished=finished)
            temporary = path.with_suffix('.tmp')
            temporary.write_text(json.dumps(details, indent=2), encoding='utf-8')
            temporary.replace(path)
            if not finished:
                production_check()
        os.environ['DEEPTHORT_BENCH_PYTHON'] = sys.executable
        return run_capped(command,
                          cwd=str(ROOT), percent=35, ram_percent=35, observe=observe)
    finally:
        kernel.CloseHandle(handle)


if __name__ == '__main__':
    raise SystemExit(main())
