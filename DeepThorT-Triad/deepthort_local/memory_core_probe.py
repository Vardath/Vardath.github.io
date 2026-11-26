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


def exercise(health,pid,live_result,*,cancelled=lambda:False):
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
    return {'status':'passed','detail':'Independent fifth AI produced correct scoped recall IDs, Sentinel governed delivery, advisory-only records excluded. Live overlap and faster retrieval not yet certified.',
            'evidence':{'pid':row['pid'],'memory_cases':cases}}
