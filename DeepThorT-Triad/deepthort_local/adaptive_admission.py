"""Conservative, measured admission slots, not a second OS resource limit."""
GIB=1024**3

def capacity(sample):
    """Physical reserve plus one GiB of additional allowance per extra slot.

    Each native worker retains its fixed thread/context limit. This is a
    conservative scheduling heuristic, not a prediction of its exact commit
    requirements. The shared Windows Job Object remains authoritative.
    """
    try:cap,available,total=sample
    except (TypeError,ValueError):return 0
    if any(type(v) is not int for v in (cap,available,total)):return 0
    if not (0<cap<=total and 0<=available<=total):return 0
    spare=available-max(3*GIB,total//10)
    if spare<0:return 0
    return min(4,1+spare//GIB)

def admission_ready(active,waiters,ticket,slots,rank,now):
    return (len(active)<slots and bool(waiters) and
            min(waiters,key=lambda t:rank(t,now))==ticket)



def parallel_media_admitted(health,expected_pid,headroom):
    """Existing broker plus additional measured fourth-worker headroom.

    Never start unsolicited overlapping media in protected serial mode or
    ahead of queued native inference, including the required Memory role.
    The shared OS Job Object remains the hard resource authority.
    """
    if not isinstance(health,dict) or health.get('pid')!=expected_pid or health.get('ready') is not True:
        return False
    if health.get('serial_memory_mode') is not False or health.get('admission_waiting')!=0:
        return False
    slots=health.get('admission_slots')
    if type(slots) is not int or slots<2:return False
    models=health.get('models')
    if not isinstance(models,dict) or any(not isinstance(models.get(role),dict)
        or models[role].get('resident') is not True for role in ('janus','sentinel','implementation')):
        return False
    memory=health.get('memory_model')
    if not isinstance(memory,dict) or memory.get('resident') is not True:return False
    active=[models[r].get('generating') for r in ('janus','sentinel','implementation')]+[memory.get('generating')]
    if any(type(v) is not bool for v in active) or sum(active)>=slots:return False
    try:return bool(headroom())
    except (ValueError,OSError,RuntimeError,KeyError):return False
