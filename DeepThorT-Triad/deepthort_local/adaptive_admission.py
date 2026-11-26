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

def mandatory_ready(active,waiters,ticket,slots,rank,now):
    return (len(active)<slots and bool(waiters) and
            min(waiters,key=lambda t:rank(t,now))==ticket)

def optional_ready(active,waiters,slots):
    # Reserve at least one slot for a newly arriving mandatory operation;
    # a memory lookup is never placed on the mandatory wait list.
    return slots>=2 and len(active)<slots-1 and not waiters
