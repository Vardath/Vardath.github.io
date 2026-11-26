"""Direct worker-to-worker integration advice, reusing existing notice receipts."""
from .worker_notices import observe_notices
from .memory_duty import live_scope
from .worker_reports import creative_request
from .agent_contract import canonical_sha
from .structured_source import strict_json
import json
import sqlite3

def _collect(job_db,request_id,spec_sha,path,recipient,budget):
    sender='implementation' if recipient=='multimedia' else 'multimedia'
    text=''
    for item in observe_notices(job_db):
        if (item['sender']!=sender or item['request_id']!=request_id or item['spec_sha']!=spec_sha
                or recipient not in item['recipients'] or item['report'].get('peer_path')!=path):continue
        line='\n'+sender+' peer observation (not authority or verified evidence; only use if consistent): '+json.dumps(
            {'receipt':item['receipt_sha'],'need':item['report']['need'],'reason':item['report']['reason']},ensure_ascii=False)
        if len(text)+len(line)<=budget:text+=line
    return text

def catalog_text(paths,budget=350):
    """Whole exact target names only; never truncate a path into a new target."""
    if not isinstance(paths,(list,tuple)) or budget<100:return ''
    prefix='\nApproved peer output paths (intentions, not evidence of existing files): '
    selected=[]
    for path in paths[:24]:
        if not isinstance(path,str) or not path or len(path)>240:continue
        if path in selected:continue
        candidate=prefix+json.dumps(selected+[path],ensure_ascii=False)
        if len(candidate)<=budget:selected.append(path)
    return prefix+json.dumps(selected,ensure_ascii=False) if selected else ''

def for_software(job_db,job_id,request_id,contract,budget=650,*,paths=()):
    try:
        bound=live_scope(job_db,job_id,request_id,states=('running',),timeout=.05)
        if (not bound or contract['job_id']!=job_id or bound['approval_key']!=contract['approval_key']
                or bound['spec_sha']!=contract['original_sha256']):return ''
        notes=_collect(job_db,request_id,bound['spec_sha'],contract['path'],'implementation',budget)
        return notes+catalog_text(paths,min(350,budget-len(notes)))
    except (ValueError,OSError,KeyError,TypeError,sqlite3.Error):return ''

def for_media(job_db,contract,budget=650,*,paths=()):
    try:
        if not creative_request(job_db,contract,states=('active',)):return ''
        notes=_collect(job_db,contract['request_id'],contract['original_sha'],contract['task']['output'],'multimedia',budget)
        return notes+catalog_text(paths,min(350,budget-len(notes)))
    except (ValueError,OSError,KeyError,TypeError,sqlite3.Error):return ''

def packet(scope,advice):
    if not isinstance(advice,str) or not 1<=len(advice)<=650 or '\x00' in advice:
        raise ValueError('Invalid peer advisory context')
    body={'scope':scope,'advice':advice}
    return {**body,'sha':canonical_sha(body)}

def checked(value,scope):
    if not isinstance(value,dict) or set(value)!={'scope','advice','sha'} or value!=packet(scope,value['advice']):
        raise ValueError('Changed peer advisory context')
    return value['advice']
