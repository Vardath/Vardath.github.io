"""Fixed, correctness-first local benchmark for the four resident text workers."""
from __future__ import annotations
import json
import statistics
import time
from .triad_profiles import ALL_PROFILES,RUNTIME_VERSION
from .triad_acceptance import resident_roles
from .memory_core_probe import resident_memory
from .triad_collaboration import decode

TASKS=(
    ('arithmetic','Return only JSON {"answer": integer}. A ship moves at 120 units per second for 7 seconds, then 80 units per second for 3 seconds. Total distance?',{'answer':1080}),
    ('amendment','Original specification: cargo 80, crew 6, owner NPC. Amendment: owner player, cargo 120. Return exactly JSON keys cargo, crew, owner with final values.',{'cargo':120,'crew':6,'owner':'player'}),
    ('selection','Goal: repair a broken save-game owner field. Records: A: save-game reload resets owner; B: interface color blue. Return only JSON {"keep":["relevant record ID"]}.',{'keep':['A']}),
)
ROLES=tuple(ALL_PROFILES)

def exercise(health,pid,ask,*,cancelled=lambda:False,notify=lambda stage:None,clock=time.monotonic):
    rows={}
    def finish(status,detail):
        return {'status':status,'detail':detail,'evidence':{'benchmark_results':rows.copy(),'benchmark_runtime':RUNTIME_VERSION}}
    def identity(h):
        models=resident_roles(h,pid);memory=resident_memory(h,pid)
        return {**{k:v['pid'] for k,v in models.items()},'memory':memory['pid']}
    try:
        first=health();ids=identity(first)
        if any(v.get('busy') for v in (*first['models'].values(),first['memory_model'])):
            return finish('inconclusive','Workers busy; benchmark deferred')
    except Exception:return finish('blocked','Four resident text models required')
    serial=first.get('serial_memory_mode');retries=first.get('memory_retries',0)
    def stable():
        h=health()
        return identity(h)==ids and h.get('serial_memory_mode')==serial and h.get('memory_retries',0)==retries
    for role in ROLES:
        profile=ALL_PROFILES[role]
        row={'model':profile[0],'configured_revision':profile[2],'pid':ids[role],'cases':[]}
        rows[role]=row
        for repeat in range(2):
            for ident,prompt,expected in TASKS:
                if cancelled():return finish('cancelled','Benchmark cancelled before next request')
                try:
                    if not stable():return finish('inconclusive','Worker or memory policy changed during benchmark')
                    notify(role+':'+ident+':'+str(repeat+1))
                    start=clock()
                    try:
                        answer=ask(role,prompt,128,repeat,ident)
                        obj=decode(answer)
                        status='passed' if json.dumps(obj,sort_keys=True)==json.dumps(expected,sort_keys=True) else 'failed'
                    except (ValueError,TypeError):status='failed'
                    except Exception:status='blocked'
                    elapsed=round(max(0,clock()-start),3)
                    row['cases'].append({'task':ident,'repeat':repeat+1,'status':status,'elapsed_seconds':elapsed})
                    if cancelled():return finish('cancelled','Benchmark cancelled after request')
                    if not stable():return finish('inconclusive','Worker or memory policy changed during benchmark')
                except Exception:return finish('blocked','Worker health unavailable during benchmark')
        row['passed']=sum(c['status']=='passed' for c in row['cases'])
        row['failed']=sum(c['status']=='failed' for c in row['cases'])
        row['blocked']=sum(c['status']=='blocked' for c in row['cases'])
        row['median_verified_seconds']=statistics.median(c['elapsed_seconds'] for c in row['cases'] if c['status']=='passed') if row['passed'] else None
    statuses=[c['status'] for r in rows.values() for c in r['cases']]
    status='failed' if 'failed' in statuses else 'blocked' if 'blocked' in statuses else 'passed'
    return finish(status,'24 fixed native text requests; correctness before median verified request latency. Configured revision only; no token throughput, peak memory, Gemma comparison or general coding acceptance.')
