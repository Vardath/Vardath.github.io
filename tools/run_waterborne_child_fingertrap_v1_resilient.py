#!/usr/bin/env python3
import argparse,shutil
from pathlib import Path
import test_waterborne_child_fingertrap_v2 as core
import run_waterborne_child_fingertrap_v2_batchprefetch as batch
V1_WORK=Path('research/waterborne_child_fingertrap_v1_work');V1_RESULTS=Path('research/waterborne_child_fingertrap_v1_results')
def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True);sp.add_parser('validate');sh=sp.add_parser('shard');sh.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args()
    if a.cmd=='validate': core.validate();print('{"batch_prefetch_transport":"ok","scientific_protocol":"v2"}')
    elif a.cmd=='shard':
        core.run_shard(a.id);V1_WORK.mkdir(parents=True,exist_ok=True);shutil.copy2(core.WORK/f'shard-{a.id:02d}.json',V1_WORK/f'shard-{a.id:02d}.json')
    else:
        core.WORK.mkdir(parents=True,exist_ok=True)
        for p in V1_WORK.glob('shard-*.json'):shutil.copy2(p,core.WORK/p.name)
        batch.run();V1_RESULTS.mkdir(parents=True,exist_ok=True)
        for p in core.RESULTS.glob('*'):shutil.copy2(p,V1_RESULTS/p.name)
if __name__=='__main__':main()
