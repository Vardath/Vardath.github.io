"""Explicit read-only metadata for one already selected project/chat scope."""
from contextlib import closing
from pathlib import Path
import sqlite3
import time
from .job_queue import STATES as JOB_STATES
from .conversation_workflow import VALID_STATES as REQUEST_STATES

LIMIT=50
def rows(path,project,chat,table,states,modes):
    path=Path(path)
    if not path.is_file() or path.is_symlink():raise ValueError('State database unavailable')
    # No application-store constructors: those may recover interrupted work.
    with closing(sqlite3.connect(path.resolve(strict=True).as_uri()+'?mode=ro',uri=True,timeout=.5)) as db:
        db.execute('PRAGMA query_only=ON')
        end=time.monotonic()+.5
        db.set_progress_handler(lambda:int(time.monotonic()>=end),1000)
        result=[]
        for ident,mode,state in db.execute('SELECT id,mode,state FROM '+table+' WHERE project=? AND chat_id=? ORDER BY id DESC LIMIT ?', (project,chat,LIMIT+1)):
            if type(ident) is not int or ident<=0 or mode not in modes or state not in states:raise ValueError('Unexpected stored state')
            result.append({'id':ident,'mode':mode,'state':state})
        return {'rows':result[:LIMIT],'more_omitted':len(result)>LIMIT}
def status(jobs_path,requests_path,project,chat,*,approved=False):
    if approved is not True:raise PermissionError('Explicit scope-metadata approval required')
    if not isinstance(project,str) or not project or len(project)>4096 or not isinstance(chat,str) or not chat or len(chat)>256:
        raise ValueError('Select an exact project/chat')
    jobs=rows(jobs_path,project,chat,'jobs',JOB_STATES,{'chat','edit','plan','build','vision','image'})
    requests=rows(requests_path,project,chat,'conversation_requests',REQUEST_STATES,{'chat','draft_plan'})
    return {'schema':'janus-local-status-v1','scope':'approved current project and chat','jobs':jobs,'conversation_requests':requests,
            'limit_per_store':LIMIT,'snapshot_atomic_across_stores':False,'mutated':False}
