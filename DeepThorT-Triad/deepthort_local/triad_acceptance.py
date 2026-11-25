"""Independent three-role readiness and synthetic inference checks."""
from concurrent.futures import ThreadPoolExecutor
import threading
from .triad_profiles import PROFILES
from .triad_errors import WORDS,error_record
import time

def resident_roles(health,pid):
    if not isinstance(health,dict) or health.get('pid')!=pid or health.get('ready') is not True or health.get('offline') is not True or health.get('backend')!='native-openvino-ir-cpu':
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
    """Check individual inference first, then concurrent native activity."""
    initial=health()
    models=resident_roles(initial,pid)
    if any(m.get('busy') for m in models.values()):
        return {'status':'inconclusive','detail':'Real inference already active; test not started.'},False
    if cancelled.is_set():return {'status':'cancelled','detail':'Test stopped'},False
    def one(role):
        started=time.monotonic()
        try:
            result=ask(role,WORDS[role])
            status='passed' if isinstance(result,str) and result.strip()==WORDS[role] else 'failed'
            return {'status':status,'seconds':round(time.monotonic()-started,2)}
        except Exception as error:
            return {'status':'blocked','seconds':round(time.monotonic()-started,2),'error':error_record(error)}
    individual={}
    for role in WORDS:
        if cancelled.is_set():return {'status':'cancelled','detail':'Test stopped'},False
        individual[role]=one(role)
    gate=threading.Barrier(3)
    def simultaneous(role):
        gate.wait(timeout=10)
        return one(role)
    overlap=False
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={role:pool.submit(simultaneous,role) for role in WORDS}
        while not all(f.done() for f in futures.values()):
            try:
                current=resident_roles(health(),pid)
                overlap=overlap or all(m.get('generating') is True for m in current.values())
            except (ValueError,OSError,TypeError,KeyError):pass
            if cancelled.wait(.25):break
        results={}
        for role,f in futures.items():
            try:results[role]=f.result()
            except Exception as error:results[role]={'status':'blocked','error':error_record(error)}
    statuses={r:v['status'] for r,v in results.items()}
    evidence={'role_results':statuses,'individual_results':individual,'concurrent_results':results}
    if cancelled.is_set():return {'status':'cancelled','detail':'Test stopped after in-flight requests returned','evidence':evidence},overlap
    try:
        final=health();resident_roles(final,pid)
    except (ValueError,OSError,TypeError,KeyError):return {'status':'blocked','detail':'A model stopped during the test','evidence':evidence},overlap
    evidence['serial_memory_mode']=final.get('serial_memory_mode') is True
    evidence['memory_retries']=max(0,int(final.get('memory_retries',0))-int(initial.get('memory_retries',0)))
    passed=all(v['status']=='passed' for v in individual.values()) and all(v=='passed' for v in statuses.values())
    detail='Individual: '+', '.join(r+' '+v['status'] for r,v in individual.items())+'; simultaneous requests: '+', '.join(r+' '+v for r,v in statuses.items())
    if evidence['serial_memory_mode']:detail+='; memory-pressure serial mode (all models resident)'
    # Observing overlapping calls before an allocation failure does not prove
    # successful concurrent inference if they subsequently required serial retry.
    return {'status':'passed' if passed else 'failed','detail':detail,'evidence':evidence},overlap and not evidence['serial_memory_mode']
