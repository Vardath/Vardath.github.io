#!/usr/bin/env python3
import argparse, json, shutil
from pathlib import Path

import test_waterborne_child_fingertrap_v2 as v2

V1_WORK = Path("research/waterborne_child_fingertrap_v1_work")
V1_RESULTS = Path("research/waterborne_child_fingertrap_v1_results")


def validate():
    v2.validate()
    print(json.dumps({"execution_harness":"existing_v1_20_shard_workflow","scientific_protocol":"v2","status":"ok"}))


def shard(i):
    v2.run_shard(i)
    V1_WORK.mkdir(parents=True, exist_ok=True)
    src = v2.WORK / f"shard-{i:02d}.json"
    dst = V1_WORK / src.name
    shutil.copy2(src, dst)
    print(json.dumps({"v2_shard":i,"mirrored_for_existing_workflow":str(dst)}))


def merge():
    v2.WORK.mkdir(parents=True, exist_ok=True)
    for p in sorted(V1_WORK.glob("shard-*.json")):
        shutil.copy2(p, v2.WORK / p.name)
    v2.merge()
    V1_RESULTS.mkdir(parents=True, exist_ok=True)
    for p in v2.RESULTS.iterdir():
        if p.is_file():
            shutil.copy2(p, V1_RESULTS / ("V2_" + p.name))
    print(json.dumps({"scientific_protocol":"v2","v2_results":str(v2.RESULTS),"mirrored_result_dir":str(V1_RESULTS)}))


def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True)
    sp.add_parser("validate"); sh=sp.add_parser("shard"); sh.add_argument("--id",type=int,required=True); sp.add_parser("merge")
    a=ap.parse_args()
    if a.cmd=="validate": validate()
    elif a.cmd=="shard": shard(a.id)
    else: merge()

if __name__=="__main__": main()
