"""Windows CI/native preflight: verify real runtime and nested venv process cap.

No model weights, no private data, no inference service or unrestricted process.
"""
import os
import sys
from pathlib import Path
from deepthort_local.win_cpu_cap import run_capped
from deepthort_local.triad_job import verify_root_cap,child_server,model_group,worker_budget

ROOT=Path(__file__).resolve().parent

def inner():
    import time
    import openvino_genai as genai
    from triad_openvino_worker import bounded_scheduler
    cfg=bounded_scheduler(genai)
    assert cfg.max_num_seqs==1 and cfg.num_kv_blocks==256 and not cfg.enable_prefix_caching
    cap,free,total=verify_root_cap()
    print('Root commit budget:',cap,'total physical:',total,flush=True)
    # Exercise a real nested job, rather than only mocked source tests.
    log=ROOT/'state/logs/triad-ci-native-preflight.log'
    with model_group() as (group,budget):
        if budget!=worker_budget(cap):raise RuntimeError('Worker reserve mismatch')
        with child_server([sys.executable,'-I',str(ROOT/'triad_openvino_worker.py'),'--probe'],ROOT,log,group=group) as (pid,alive):
            deadline=time.monotonic()+180
            while alive() and time.monotonic()<deadline:time.sleep(.5)
            if alive():raise RuntimeError('Nested native CPU probe timed out')
            if alive.code()!=0:raise RuntimeError(alive.failure())
    print(log.read_text(encoding='utf-8',errors='replace'),flush=True)
    return 0

if __name__=='__main__':
    if sys.argv[1:]==['--inside']:raise SystemExit(inner())
    raise SystemExit(run_capped([sys.executable,str(Path(__file__).resolve()),'--inside'],cwd=str(ROOT),percent=35,ram_percent=35))
