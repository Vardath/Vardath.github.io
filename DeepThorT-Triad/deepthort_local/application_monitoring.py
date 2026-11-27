"""Bounded, explicitly approved live application health sampling."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.api_testing import run as api_run,checked as api_checked
SCHEMA='janus-application-health-monitor-v1'
def checked(s):
    if not isinstance(s,dict) or set(s)!={'port','path','expected_status','json_fields','samples','interval_seconds','max_latency_ms'}:
        raise ValueError('Expected exact local health endpoint and sampling limits')
    api_checked(test_spec(s))
    for k,lo,hi in (('samples',2,8),('interval_seconds',1,3),('max_latency_ms',1,5000)):
        if type(s[k]) is not int or not lo<=s[k]<=hi:raise ValueError('Invalid '+k)
    return s
def test_spec(s):
    return {'port':s['port'],'cases':[{'id':'health','path':s['path'],'status':s['expected_status'],'json_fields':s['json_fields']}]}
def observe(s,sample=api_run,sleep=time.sleep,clock=time.monotonic):
    checked(s);observations=[];start=clock();aborted=False
    for i in range(s['samples']):
        if clock()-start>45:aborted=True;break
        if i:sleep(s['interval_seconds'])
        if clock()-start>45:aborted=True;break
        stamp=datetime.now(timezone.utc).isoformat()
        result=sample(test_spec(s))['cases'][0]
        latency=result.get('elapsed_ms')
        contract=bool(result['passed'])
        slow=latency is not None and latency>s['max_latency_ms']
        observations.append({'index':i+1,'observed_utc':stamp,'contract_passed':contract,'latency_threshold_exceeded':slow,
            'healthy':contract and latency is not None and not slow,'status':result.get('status'),
            'elapsed_ms':latency,'error_type':result.get('error_type')})
    complete=len(observations)==s['samples']
    successful=sum(x['healthy'] for x in observations)
    times=sorted(x['elapsed_ms'] for x in observations if x['elapsed_ms'] is not None)
    median=None
    if times:
        n=len(times);median=times[n//2] if n%2 else (times[n//2-1]+times[n//2])/2
    return {'schema':'janus-application-health-result-v1','target':'127.0.0.1:'+str(s['port']),'path':s['path'],
        'requested_samples':s['samples'],'completed_samples':len(observations),'complete':complete,'deadline_reached':aborted,
        'healthy_samples':successful,'unhealthy_samples':len(observations)-successful,
        'all_healthy':complete and successful==s['samples'],'median_response_latency_ms':median,
        'max_response_latency_ms':max(times) if times else None,'observations':observations,
        'scope':'Finite sequential HTTP health observations only. Not continuous monitoring, uptime/SLA estimation or automatic repair. GET endpoint must be safe to sample.'}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,scope='Sample reviewed local endpoint a finite number of times; no service startup, restart or external network.')
def execute(root,plan):
    s,dst,_=validate(root,plan);r=observe(s)
    digest=guard.publish(json.dumps(r,ensure_ascii=True,allow_nan=False,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'status':'application_health_samples_completed','output':plan['output'],'sha256':digest,'complete':r['complete'],'all_healthy':r['all_healthy'],'samples':r['completed_samples']}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Health sampling unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
