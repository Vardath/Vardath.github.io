"""Let the resident producer choose useful work from exact host-ready options."""
import json
from .agent_contract import canonical_sha
from .reasoning_council import sha
from .structured_source import strict_json

MAX_OPTIONS=6

def choose(client,job,original,amendments,candidates,*,stopped):
    """One bounded role-native decision; no new task, grant or dependency.

    No inference for a singleton. A malformed preference uses the existing
    deterministic ready rank; cancellation NEVER becomes a fallback.
    The caller must revalidate the exact selected node before assignment.
    """
    options=candidates[:MAX_OPTIONS]
    if not options or stopped():return None
    if len(options)==1:return {'step_id':options[0]['id'],'reason':'Only eligible ready stage','origin':'host_ready'}
    allowed={s['id'] for s in options}
    scope=canonical_sha([job['id'],job['approval_key'],sha(original),amendments,
                          [{k:s[k] for k in ('id','path','description','state')} for s in options]])
    # Exact original excerpts are context, not a replacement of the full
    # master, which the normal production and independent review still bind.
    prompt=('Choose YOUR next useful software assignment from these already approved dependency-ready stages. '
            'Consider actual integration, what other workers may need and avoiding wasted work. '
            'All listed stages are equally authorized. Never invent a task, alter requirements, or claim completion. '
            'Return ONLY JSON {"step_id":integer,"reason":"specific reason, max 160 characters"}. '
            'The host rechecks readiness and Sentinel still reviews actual work.\n'
            'Original specification SHA: '+sha(original)+'\nOriginal beginning (verbatim): '+original[:1200]+
            '\nCurrent approved job scope: '+str(job['prompt'])[:900]+
            '\nAmendment history SHA: '+canonical_sha(amendments)+
            '\nReady stages in host dependency-impact order: '+json.dumps(
                [{'step_id':s['id'],'path':s['path'],'description':s['description'][:300]} for s in options],ensure_ascii=False))
    if amendments:prompt+='\nLatest recorded amendment (excerpt): '+json.dumps(amendments[-1],ensure_ascii=False)[:600]
    decision=None
    try:
        raw=client.chat_as('implementation','ready-selection-'+scope[:48],prompt,max_tokens=160)
        if isinstance(raw,str) and len(raw)<=500:
            data=strict_json(raw.strip())
            if (isinstance(data,dict) and set(data)=={'step_id','reason'} and type(data['step_id']) is int
                    and data['step_id'] in allowed and isinstance(data['reason'],str) and 1<=len(data['reason'].strip())<=160
                    and all(ord(c)>=32 for c in data['reason'])):
                decision={'step_id':data['step_id'],'reason':data['reason'].strip(),'origin':'implementation'}
    except (ValueError,TypeError,RuntimeError,OSError):pass
    if stopped():return None
    return decision or {'step_id':options[0]['id'],'reason':'No valid model preference; existing ready rank','origin':'host_ready'}
