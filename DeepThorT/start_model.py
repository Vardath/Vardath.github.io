"""Run Node/ONNX under one hard Windows job-object CPU and commit memory limit."""
import os
from pathlib import Path
from shutil import which
from deepthort_local.win_cpu_cap import run_capped

if __name__=='__main__':
    if os.name!='nt': raise SystemExit('Windows CPU/RAM hard limit required; refusing uncapped launch')
    root=Path(__file__).resolve().parent
    node=which('node')
    if not node: raise SystemExit('Node.js not installed. Install the official Node.js LTS first.')
    print('CPU <=30% total, job committed memory <=30% of installed RAM, idle priority, no GPU.',flush=True)
    raise SystemExit(run_capped([node,str(root/'inference_server.mjs')],cwd=str(root),percent=30,ram_percent=30))
