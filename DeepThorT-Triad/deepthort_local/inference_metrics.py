"""Bounded, numeric local inference telemetry; never records input/output text."""
from __future__ import annotations
import math
import time
from contextlib import contextmanager
from .flight_recorder import record

ROLES=('implementation','janus','sentinel','memory','gemma')
KINDS=('native','broker','admission','creative_load')
def number(value):
    if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1e12:return None
    return value
def count(value):
    return value if type(value) is int and 0<=value<=1_000_000_000 else None
def runtime_counts(out):
    # OpenVINO GenAI public counters may be unavailable on some result types.
    # Never infer token count from characters or the configured maximum.
    result={}
    try:metrics=out.perf_metrics
    except Exception:return result
    for key,method in (('input_tokens','get_num_input_tokens'),('generated_tokens','get_num_generated_tokens')):
        try:
            value=count(getattr(metrics,method)())
            if value is not None:result[key]=value
        except Exception:pass
    return result
@contextmanager
def measured(state,role,kind,**fields):
    """Best effort. Original exceptions and return values are preserved."""
    if role not in ROLES or kind not in KINDS:
        yield {};return
    start=time.perf_counter();cpu=time.process_time()
    observation={k:v for k,v in fields.items() if k in ('budget_tokens','input_tokens','omitted_exchanges') and count(v) is not None}
    ok=False
    try:
        yield observation
        ok=True
    finally:
        elapsed=max(0,time.perf_counter()-start)
        process_cpu=max(0,time.process_time()-cpu)
        safe={k:v for k,v in observation.items() if k in ('budget_tokens','input_tokens','generated_tokens','omitted_exchanges') and count(v) is not None}
        # Separate component files for broker and each resident worker.
        # Broker CPU is shared and is deliberately not attributed to a role.
        if kind in ('native','creative_load'):safe['process_cpu_seconds']=round(process_cpu,6)
        try:
            record(state,'inference_'+('broker' if kind in ('broker','admission') else role),
                   'inference_measurement',role=role,kind=kind,success=ok,
                   seconds=round(elapsed,6),**safe)
        except Exception:pass
