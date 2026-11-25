"""Privacy-safe, offline inference/planning performance accounting.

Processes existing rotating JSONL telemetry. It never reads conversation
SQLite tables, model prompts, source text or generated answers. Metrics are
observations, not guarantees of accuracy or model capability.
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def _records(folder: Path, filename: str):
    for extension in ('.3','.2','.1',''):
        path=folder/(filename+extension)
        if not path.is_file():
            continue
        with path.open('r',encoding='utf-8',errors='replace') as source:
            for line in source:
                try:
                    row=json.loads(line)
                    if isinstance(row,dict) and isinstance(row.get('data',{}),dict):
                        yield row
                except (ValueError,UnicodeError):
                    continue


def report(log_folder: str | Path) -> dict:
    folder=Path(log_folder)
    model=[row for row in _records(folder,'model_client.jsonl')
           if row.get('event')=='request_completed']
    planner=[row for row in _records(folder,'planner.jsonl')
             if row.get('event')=='model_plan_pass']
    seconds=[float(d['data']['seconds']) for d in model
             if isinstance(d['data'].get('seconds'),(float,int)) and d['data']['seconds']>=0]
    bad=[p for p in planner if p['data'].get('invalid_json')]
    cache=[p for p in planner if p['data'].get('output_token_budget')==0]
    progress=[p for p in planner if p['data'].get('net_new_files',0)>0]
    return {
        'completed_model_requests':len(model),
        'measured_duration_count':len(seconds),
        'mean_seconds':round(statistics.mean(seconds),2) if seconds else None,
        'median_seconds':round(statistics.median(seconds),2) if seconds else None,
        'maximum_seconds':round(max(seconds),2) if seconds else None,
        'planner_passes_logged':len(planner),
        'malformed_format_passes':len(bad),
        'passes_with_new_files':len(progress),
        'cached_completed_passes':len(cache),
        'last_remaining_gap_count':planner[-1]['data'].get('remaining_gap_count') if planner else None,
        'privacy':'Numeric local telemetry only; no chat text or source code',
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description='Offline DeepThorT model/planning timing report')
    parser.add_argument('logs',help='Path to DeepThorT/state/logs')
    args=parser.parse_args(argv)
    print(json.dumps(report(args.logs),indent=2,ensure_ascii=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
