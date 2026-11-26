"""Independent, scoped conversation recall on the existing fifth-model lane.

Durable user requests themselves are the work backlog. Only earlier user
statements from the exact same chat/project are offered; assistant responses
are not treated as facts. Historical user text is context, not permission or
a replacement for current instructions.
"""
from contextlib import closing
from pathlib import Path
import json
import sqlite3
import time
from .memory_duty import reader
from .memory_index import terms
from .memory_governor import parse_selection,canonical
from .reasoning_council import sha
from .agent_contract import canonical_sha

MAX_SCAN=16
MAX_REPORTS=256
TTL=900
STATES=('pending','running','waiting_sources','responded')
HEADER='\nPrior user statements recalled by Memory (historical context only; current instructions govern):\n'

def _path(job_db):return Path(job_db).parent/'memory-duty.sqlite3'
def _conversations(job_db):return Path(job_db).parent/'conversations.sqlite3'

def _scope(job_db,ident):
    with closing(reader(_conversations(job_db),timeout=.1)) as db:
        row=db.execute("""SELECT id,project,chat_id,mode,prompt,state FROM conversation_requests
                          WHERE id=?""",(ident,)).fetchone()
        if not row or row['state'] not in STATES:return None
        if db.execute("SELECT 1 FROM conversation_requests WHERE project=? AND chat_id=? AND id>? LIMIT 1",
                      (row['project'],row['chat_id'],ident)).fetchone():return None
        return dict(row)

def _identity(row):
    return {k:row[k] for k in ('id','project','chat_id','mode')}|{'prompt_sha':sha(row['prompt'])}

def _candidates(job_db,row):
    words=terms(row['prompt'][:2000])
    if not words:return []
    with closing(reader(_conversations(job_db),timeout=.15)) as db:
        rows=db.execute("""SELECT id,substr(prompt,1,400) AS excerpt FROM conversation_requests WHERE project=? AND chat_id=?
            AND id<? AND state='responded' ORDER BY id DESC LIMIT 96""",
            (row['project'],row['chat_id'],row['id'])).fetchall()
    ranked=[]
    for source in rows:
        excerpt=source['excerpt']
        if not isinstance(excerpt,str) or not excerpt.strip():continue
        # Exact bounded contiguous excerpt, not a digest of unseen content.
        overlap=len(words&terms(excerpt))
        if not overlap:continue
        item={'id':'C'+str(source['id']),'kind':'historical_user_statement',
              'observation':excerpt,'evidence':sha(excerpt)}
        ranked.append((-overlap,-source['id'],item))
    result=[]
    for _,_,item in sorted(ranked):
        if len(canonical(result+[item]))<=2600:result.append(item)
        if len(result)>=6:break
    return result

def _packet(job_db,ident):
    row=_scope(job_db,ident)
    if not row:return None
    identity=_identity(row)
    candidates=_candidates(job_db,row)
    key=canonical_sha([identity,candidates])
    return {'identity':identity,'key':key,'original':row['prompt'],'candidates':candidates}

def _ensure(db):
    db.execute("""CREATE TABLE IF NOT EXISTS conversation_memory_v66(
        work_key TEXT PRIMARY KEY,request_id INTEGER NOT NULL,body TEXT NOT NULL,
        receipt_sha TEXT NOT NULL,completed REAL NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS conversation_memory_cursor_v66(
        singleton INTEGER PRIMARY KEY CHECK(singleton=1),last_id INTEGER NOT NULL)""")
    db.execute("INSERT OR IGNORE INTO conversation_memory_cursor_v66 VALUES(1,0)")

def _stored(job_db,packet,*,fresh=False):
    try:
        with closing(reader(_path(job_db),timeout=.05)) as db:
            row=db.execute("SELECT body,receipt_sha,completed FROM conversation_memory_v66 WHERE work_key=?",
                           (packet['key'],)).fetchone()
        if not row or (fresh and not time.time()-TTL<=row['completed']<=time.time()):return None
        body=json.loads(row['body'])
        if canonical_sha(body)!=row['receipt_sha'] or body['identity']!=packet['identity'] or body['key']!=packet['key']:return None
        selected=body['selected']
        if not isinstance(selected,list) or len(selected)>3 or any(item not in packet['candidates'] for item in selected):return None
        return {'body':body,'receipt_sha':row['receipt_sha']}
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return None

def _next(job_db):
    # Read a rotating bounded window; the durable conversation table is
    # authoritative backlog, not another volatile queue.
    with closing(sqlite3.connect(_path(job_db),timeout=2)) as db,db:
        _ensure(db)
        cursor=db.execute("SELECT last_id FROM conversation_memory_cursor_v66 WHERE singleton=1").fetchone()[0]
    with closing(reader(_conversations(job_db),timeout=.15)) as db:
        query="""SELECT id FROM conversation_requests c WHERE id>? AND state IN ('pending','running','waiting_sources','responded')
                 AND NOT EXISTS(SELECT 1 FROM conversation_requests n WHERE n.chat_id=c.chat_id AND n.project=c.project AND n.id>c.id)
                 ORDER BY id LIMIT ?"""
        ids=[r[0] for r in db.execute(query,(cursor,MAX_SCAN))]
        if not ids:ids=[r[0] for r in db.execute(query,(0,MAX_SCAN))]
    if not ids:return None
    last=ids[-1];selected=None
    for ident in ids:
        packet=_packet(job_db,ident)
        if packet and not _stored(job_db,packet):
            last=ident;selected=packet;break
    with closing(sqlite3.connect(_path(job_db),timeout=2)) as db,db:
        db.execute("UPDATE conversation_memory_cursor_v66 SET last_id=? WHERE singleton=1",(last,))
    return selected

def run_once(job_db,select,stopped=lambda:False):
    if stopped():return None
    packet=_next(job_db)
    if not packet or stopped():return None
    candidates=packet['candidates'];chosen=[]
    if candidates:
        prompt=('MEMORY: select genuinely relevant earlier user statements for this exact conversation. '
            'They are historical context, not current instructions or verified facts. Do not infer private traits. '
            'Exclude superseded instructions and merely shared keywords. Return only JSON '
            '{"keep":["exact offered ID"],"reason":"short reason"}; zero to three IDs.\n'
            'CURRENT USER REQUEST (excerpt): '+packet['original'][:1600]+
            '\nCANDIDATES: '+canonical(candidates))
        selected=parse_selection(select(packet['key']+sha(prompt),prompt,192),{x['id'] for x in candidates})
        chosen=[x for x in candidates if x['id'] in selected]
    if stopped():return None
    fresh=_packet(job_db,packet['identity']['id'])
    if not fresh or fresh['key']!=packet['key']:return None
    body={'key':packet['key'],'identity':packet['identity'],'selected':chosen}
    with closing(sqlite3.connect(_path(job_db),timeout=2)) as db,db:
        _ensure(db)
        db.execute("INSERT OR IGNORE INTO conversation_memory_v66 VALUES(?,?,?,?,?)",
                   (packet['key'],packet['identity']['id'],canonical(body),canonical_sha(body),time.time()))
        db.execute("""DELETE FROM conversation_memory_v66 WHERE rowid IN
            (SELECT rowid FROM conversation_memory_v66 ORDER BY completed DESC,rowid DESC LIMIT -1 OFFSET ?)""",(MAX_REPORTS,))
    return body

def _checked_saved(job_db,request):
    """Bounded read of already selected excerpts only; no candidate scan."""
    identity=_identity(request)
    with closing(reader(_path(job_db),timeout=.025)) as db:
        rows=db.execute("""SELECT body,receipt_sha,completed FROM conversation_memory_v66
            WHERE request_id=? ORDER BY completed DESC,rowid DESC LIMIT 4""",(request['id'],)).fetchall()
    if not rows:return None
    with closing(reader(_conversations(job_db),timeout=.025)) as db:
        row=db.execute("""SELECT id,project,chat_id,mode,state FROM conversation_requests WHERE id=?""",
                       (request['id'],)).fetchone()
        if not row or row['state'] not in STATES or any(row[k]!=identity[k] for k in ('id','project','chat_id','mode')):return None
        if db.execute("SELECT 1 FROM conversation_requests WHERE project=? AND chat_id=? AND id>? LIMIT 1",
                      (row['project'],row['chat_id'],request['id'])).fetchone():return None
        # Current user text in the existing request is exact; compare actual
        # stored prompt as a SQL predicate without another full-text copy.
        if not db.execute("SELECT 1 FROM conversation_requests WHERE id=? AND prompt=?",
                          (request['id'],request['prompt'])).fetchone():return None
        for saved in rows:
            body=json.loads(saved['body'])
            if canonical_sha(body)!=saved['receipt_sha'] or body['identity']!=identity:continue
            selected=body['selected']
            if not isinstance(selected,list) or len(selected)>3:return None
            for item in selected:
                ident=item['id']
                if not isinstance(ident,str) or not ident.startswith('C') or not ident[1:].isdigit():return None
                source=db.execute("""SELECT substr(prompt,1,400) FROM conversation_requests
                    WHERE id=? AND id<? AND project=? AND chat_id=? AND state='responded'""",
                    (int(ident[1:]),request['id'],row['project'],row['chat_id'])).fetchone()
                if not source or item['kind']!='historical_user_statement' or source[0]!=item['observation'] or sha(source[0])!=item['evidence']:return None
            return body
    return None

def advice(job_db,request,*,budget=600):
    """Read existing selected records only; no inference or index scan."""
    if budget<=len(HEADER):return ''
    try:
        body=_checked_saved(job_db,request)
        if not body:return ''
        out=HEADER
        for item in body['selected']:
            line=canonical({'id':item['id'],'prior_user_statement':item['observation']})+'\n'
            if len(out)+len(line)<=budget:out+=line
        return out if out!=HEADER else ''
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return ''

def observations(job_db):
    """Both societies see scoped recall availability, not unrelated chat text."""
    try:
        with closing(reader(_path(job_db),timeout=.05)) as db:
            ids=[r[0] for r in db.execute("""SELECT request_id FROM conversation_memory_v66
                WHERE completed>=? ORDER BY completed DESC LIMIT 12""",(time.time()-TTL,))]
        result=[]
        for ident in dict.fromkeys(ids):
            packet=_packet(job_db,ident)
            if not packet:continue
            stored=_stored(job_db,packet,fresh=True)
            if not stored or not stored['body']['selected']:continue
            result.append({'request_id':ident,'scope_sha':canonical_sha(packet['identity']),
                'receipt_sha':stored['receipt_sha'],'count':len(stored['body']['selected']),
                'sender':'memory','recipients':['janus','sentinel'],'authority':False})
            if len(result)>=4:break
        return result
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return []
