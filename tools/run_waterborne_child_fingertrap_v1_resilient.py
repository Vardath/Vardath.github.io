#!/usr/bin/env python3
"""Temporary bridge: execute frozen waterborne-child v2 with shard-local bulk-revisions acquisition."""
import argparse
import shutil
from pathlib import Path

import test_waterborne_child_fingertrap_v2 as core
import run_waterborne_child_fingertrap_v2_batchprefetch as v2

V1_WORK = Path("research/waterborne_child_fingertrap_v1_work")
V1_RESULTS = Path("research/waterborne_child_fingertrap_v1_results")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("validate")
    sh = sp.add_parser("shard")
    sh.add_argument("--id", type=int, required=True)
    sp.add_parser("merge")
    a = ap.parse_args()

    if a.cmd == "validate":
        v2.validate()
    elif a.cmd == "shard":
        v2.shard_with_evidence(a.id)
        V1_WORK.mkdir(parents=True, exist_ok=True)
        src = core.WORK / f"shard-{a.id:02d}.json"
        shutil.copy2(src, V1_WORK / src.name)
    else:
        core.WORK.mkdir(parents=True, exist_ok=True)
        for p in V1_WORK.glob("shard-*.json"):
            shutil.copy2(p, core.WORK / p.name)
        v2.merge_local()
        V1_RESULTS.mkdir(parents=True, exist_ok=True)
        for p in core.RESULTS.glob("*"):
            shutil.copy2(p, V1_RESULTS / p.name)


if __name__ == "__main__":
    main()
