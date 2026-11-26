"""Verify a separately resident fifth memory worker and its actual recall evidence."""
from .triad_profiles import MEMORY_PROFILE
from .triad_acceptance import resident_roles


def resident_memory(health,pid):
    models=resident_roles(health,pid)
    row=health.get('memory_model')
    if (not isinstance(row,dict) or row.get('resident') is not True
            or row.get('name')!=MEMORY_PROFILE[0] or row.get('revision')!=MEMORY_PROFILE[2]
            or type(row.get('pid')) is not int or row['pid']<=0
            or row['pid'] in {pid,*[m['pid'] for m in models.values()]}):
        raise ValueError('Independent fifth memory model not resident; install it or inspect broker memory admission')
    return row


def parallel_recall(health,pid,memory_pid,ask,cancelled):
    """Measure real overlapping generation with independent exact output checks."""
    from concurrent.futures import ThreadPoolExecutor
    import json
    import threading
    import time
    from .memory_governor import parse_selection
    before=health()
    models=resident_roles(before,pid)
    m=resident_memory(before,pid)
    ids={k:v['pid'] for k,v in models.items()}
    retries=before.get('memory_retries',0)
    if (m['pid']!=memory_pid or before.get('serial_memory_mode') is not False or
            m.get('busy') or any(v.get('busy') for v in models.values())):
        return 'inconclusive','Workers busy or protected serial mode; no overlap test started'
    gate=threading.Barrier(2)
    prompt=('Select records directly relevant to repairing ship ownership. '
            'N1: Regression: reloading incorrectly resets player ship owner. '
            'N2: Visual test of blue interface text. Return only JSON '
            '{"keep":["record ID"],"reason":"short explanation"}.')
    def work(role,request,tokens):
        gate.wait(timeout=10)
        return ask(role,request,tokens)
    overlap=False
    stopped=False
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            mem=pool.submit(work,'memory',prompt,96)
            jan=pool.submit(work,'janus','Return exactly PLAN_READY and nothing else.',32)
            while not (mem.done() and jan.done()):
                stopped=stopped or cancelled()
                try:
                    current=health()
                    cm=resident_memory(current,pid)
                    roles=resident_roles(current,pid)
                    if (cm['pid']==memory_pid and {k:v['pid'] for k,v in roles.items()}==ids
                            and current.get('serial_memory_mode') is False
                            and current.get('memory_retries',0)==retries
                            and cm.get('generating') and roles['janus'].get('generating')):
                        overlap=True
                except (ValueError,TypeError,KeyError,OSError):
                    pass
                time.sleep(.2)
            selected=set(parse_selection(mem.result(),{'N1','N2'}))
            janus=jan.result().strip()
        if stopped or cancelled():return 'cancelled','Stopped after in-flight inference completed'
        final=health()
        if (resident_memory(final,pid)['pid']!=memory_pid
                or {k:v['pid'] for k,v in resident_roles(final,pid).items()}!=ids
                or final.get('serial_memory_mode') is not False
                or final.get('memory_retries',0)!=retries):
            return 'inconclusive','Worker configuration or pressure policy changed'
        if selected!={'N1'} or janus!='PLAN_READY':
            return 'failed','Concurrent memory/JANUS outputs did not meet exact task requirements'
        if not overlap:return 'inconclusive','Both replies correct but simultaneous generation was not observed'
        return 'passed','Native fifth AI and JANUS generated simultaneously, both correct, no worker changes or memory retries'
    except Exception as exc:
        return ('cancelled' if cancelled() else 'blocked',
                'Parallel memory probe unavailable: '+type(exc).__name__)


def exercise(health,pid,live_result,*,cancelled=lambda:False,ask=None):
    if cancelled():return {'status':'cancelled','detail':'Fifth-core test stopped'}
    try:row=resident_memory(health(),pid)
    except (OSError,ValueError,TypeError,KeyError) as error:
        return {'status':'blocked','detail':str(error)[:300]}
    if not live_result or live_result.get('status')!='passed':
        return {'status':'blocked','detail':'Independent live governed recall must finish successfully first'}
    cases=live_result.get('evidence',{}).get('memory_cases',{})
    expected_calls={'ownership':1,'prices':1,'advice_only':0}
    if set(cases)!=set(expected_calls) or any(
        cases[k].get('memory_core_status')!='passed' or cases[k].get('memory_core_calls')!=n
        for k,n in expected_calls.items()):
        return {'status':'failed','detail':'Fifth AI did not independently satisfy all recall oracles. Sentinel recovery is not a fifth-model pass.',
                'evidence':{'pid':row['pid'],'memory_cases':cases}}
    evidence={'pid':row['pid'],'memory_cases':cases}
    if ask is not None:
        status,detail=parallel_recall(health,pid,row['pid'],ask,cancelled)
        evidence['simultaneous_roles']=['memory','janus'] if status=='passed' else []
        return {'status':status,'detail':'Exact governed recall passed. '+detail,'evidence':evidence}
    return {'status':'passed','detail':'Independent fifth AI produced correct scoped recall IDs, Sentinel governed delivery, advisory-only records excluded. Live overlap not exercised.',
            'evidence':evidence}
