"""Run one experimental CPU model under the existing Windows cap supervisor."""
import argparse
import os
from pathlib import Path
from shutil import which
import socket
from deepthort_local.win_cpu_cap import run_capped

def main():
    p=argparse.ArgumentParser();p.add_argument('profile',choices=['baseline','coder3b','qwen3-4b']);a=p.parse_args()
    if os.name!='nt':raise SystemExit('Windows capped benchmark only')
    for port in (8765,8766):
        with socket.socket() as s:
            s.settimeout(0.5)
            if s.connect_ex(('127.0.0.1',port))==0:
                raise SystemExit('Close DeepThorT and both model workers before benchmark')
    node=which('node')
    if not node:raise SystemExit('Node.js not installed')
    root=Path(__file__).resolve().parent
    return run_capped([node,str(root/'model_benchmark.mjs'),a.profile,'offline'],cwd=str(root),percent=30,ram_percent=30)

if __name__=='__main__':raise SystemExit(main())
