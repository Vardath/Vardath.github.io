"""Privacy-safe, offline inference/planning performance accounting.

Processes existing rotating JSONL telemetry. It never reads conversation
SQLite tables, model prompts, source text or generated answers. Metrics are
observations, not guarantees of accuracy or model capability.
"""
from __future__ import annotations

import argparse
import json
import statistics
import math
from pathlib import Path
from .inference_metrics import ROLES,KINDS,number,count


def _records(folder: Path, filename: str):
    for extension in ('.3','.2','.1',''):
        path=folder/(filename+extension)
        if not path.is_file() or path.is_symlink() or path.stat().st_size>3*1024*1024+5000:
            continue
        with path.open('r',encoding='utf-8',errors='replace') as source:
            for line in source:
                try:
                    row=json.loads(line)
                    if isinstance(row,dict) and isinstance(row.get('data',{}),dict):
                        yield row
                except (ValueError,UnicodeError):
                    continue


def inference_report(folder):
    groups={(role,kind):[] for role in ROLES for kind in KINDS}
    for component in ('broker',*ROLES):
        for row in _records(folder,'inference_'+component+'.jsonl'):
            if row.get('event')!='inference_measurement':continue
            d=row['data'];role=d.get('role');kind=d.get('kind')
            if not isinstance(role,str) or not isinstance(kind,str) or (role,kind) not in groups:continue
            if component!=('broker' if kind in ('broker','admission') else role):continue
            if type(d.get('success')) is not bool or number(d.get('seconds')) is None:continue
            groups[(role,kind)].append(d)
    result={}
    for role in ROLES:
        per={}
        for kind in KINDS:
            rows=groups[(role,kind)]
            if not rows:continue
            good=[d for d in rows if d['success']]
            times=sorted(d['seconds'] for d in good)
            known=[d for d in good if count(d.get('generated_tokens')) is not None]
            timed=[d for d in known if d['seconds']>0]
            total_time=sum(d['seconds'] for d in timed)
            inputs=[d['input_tokens'] for d in good if count(d.get('input_tokens')) is not None]
            cpu=[d['process_cpu_seconds'] for d in good if number(d.get('process_cpu_seconds')) is not None]
            per[kind]={'attempts':len(rows),'succeeded':len(good),'failed':len(rows)-len(good),
                       'mean_seconds':round(statistics.mean(times),4) if times else None,
                       'p95_seconds':round(times[math.ceil(len(times)*.95)-1],4) if times else None,
                       'max_seconds':round(max(times),4) if times else None,
                       'input_count_samples':len(inputs),'input_tokens':sum(inputs) if inputs else None,
                       'generated_count_samples':len(known),'generated_tokens':sum(d['generated_tokens'] for d in known) if known else None,
                       'generation_rate_samples':len(timed),
                       'generated_tokens_per_second':round(sum(d['generated_tokens'] for d in timed)/total_time,3) if total_time else None,
                       'process_cpu_samples':len(cpu),'process_cpu_seconds':round(sum(cpu),4) if cpu else None}
        result[role]=per
    return {'roles':result,'scope':'Retained local log window; native generation, broker requests including retry/role queue, admission attempts, and Gemma loading are distinct; do not sum across stages.',
            'token_rate_scope':'Native runtime counters only; generation wall time includes prefill; unavailable counters remain null.',
            'first_token_latency_available':False,'quality_verified':False}

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
        'inference_by_role':inference_report(folder),
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
