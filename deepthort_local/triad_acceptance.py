"""Independent three-role readiness and synthetic inference checks."""
from concurrent.futures import ThreadPoolExecutor
import threading
from .triad_profiles import PROFILES

def resident_roles(health,pid):
    if not isinstance(health,dict) or health.get('pid')!=pid or health.get('ready') is not True or health.get('offline') is not True:
        raise ValueError('Triad broker not ready or not the supervised child')
    models=health.get('models')
    if not isinstance(models,dict) or set(models)!=set(PROFILES):raise ValueError('Three model records required')
    ids=[]
    for role,p in PROFILES.items():
        row=models[role]
        if row.get('name')!=p[0] or row.get('resident') is not True or type(row.get('pid')) is not int or row['pid']<=0:
            raise ValueError('Missing resident '+role+' model')
        ids.append(row['pid'])
    if len(set(ids+[pid]))!=4:raise ValueError('Models must have three distinct child PIDs')
    return models

def smoke(health,ask,pid,cancelled):
    """Submit fixed synthetic challenges concurrently, sample real busy flags."""
    models=resident_roles(health(),pid)
    if any(m.get('busy') for m in models.values()):
        return {'status':'inconclusive','detail':'Real inference already active; test not started.'},False
    if cancelled.is_set():return {'status':'cancelled','detail':'Test stopped'},False
    words={'implementation':'CODE_READY','janus':'PLAN_READY','sentinel':'REVIEW_READY'}
    gate=threading.Barrier(3)
    def one(role):
        gate.wait(timeout=10)
        result=ask(role,words[role])
        return isinstance(result,str) and result.strip()==words[role]
    overlap=False
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={role:pool.submit(one,role) for role in words}
        while not all(f.done() for f in futures.values()):
            try:
                current=resident_roles(health(),pid)
                overlap=overlap or all(m.get('busy') is True for m in current.values())
            except (ValueError,OSError,TypeError,KeyError):pass
            if cancelled.wait(.25):break
        results={}
        for role,f in futures.items():
            try:results[role]='passed' if f.result() else 'failed'
            except Exception:results[role]='blocked'
    if cancelled.is_set():return {'status':'cancelled','detail':'Test stopped after in-flight requests returned'},overlap
    try:resident_roles(health(),pid)
    except (ValueError,OSError,TypeError,KeyError):return {'status':'blocked','detail':'A model stopped during the test','evidence':{'role_results':results}},overlap
    return {'status':'passed' if all(x=='passed' for x in results.values()) else 'failed',
            'detail':'Exact fixed response checks: '+', '.join(r+' '+v for r,v in results.items()),
            'evidence':{'role_results':results}},overlap
