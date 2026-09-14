#!/usr/bin/env python3
"""Temporary execution bridge: run frozen waterborne-child v2 through the existing 20-shard workflow.
Scientific protocol lives in test_waterborne_child_fingertrap_v2.py; merge acceleration is execution-only.
"""
import argparse, shutil
from pathlib import Path
import run_waterborne_child_fingertrap_v2_fast as v2

V1_WORK=Path('research/waterborne_child_fingertrap_v1_work')
V1_RESULTS=Path('research/waterborne_child_fingertrap_v1_results')

def mirror_shard(i):
    src=v2.core.WORK/f'shard-{i:02d}.json'
    V1_WORK.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,V1_WORK/src.name)

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True)
    sp.add_parser('validate'); sh=sp.add_parser('shard'); sh.add_argument('--id',type=int,required=True); sp.add_parser('merge')
    a=ap.parse_args()
    if a.cmd=='validate':
        v2.core.validate(); print('{"execution_harness":"existing_v1_20_shard_workflow","scientific_protocol":"v2","fast_merge":"concurrent_single_title","status":"ok"}')
    elif a.cmd=='shard':
        v2.core.run_shard(a.id); mirror_shard(a.id)
    else:
        # Workflow downloads shard artifacts into the v1 work directory; expose those unchanged to v2.
        v2.core.WORK.mkdir(parents=True,exist_ok=True)
        for p in V1_WORK.glob('shard-*.json'): shutil.copy2(p,v2.core.WORK/p.name)
        v2.fast_merge(workers=6)
        V1_RESULTS.mkdir(parents=True,exist_ok=True)
        for p in v2.core.RESULTS.glob('*'): shutil.copy2(p,V1_RESULTS/p.name)

if __name__=='__main__': main()
