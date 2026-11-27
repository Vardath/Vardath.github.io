"""One explicitly approved cross-device status alert via ntfy, no project content."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import socket
import sqlite3
import time
from .structured_source import strict_json
from .website_monitor import PinnedHTTPS,resolve_public,stopped
from .job_queue import STATES as JOB_STATES
from .conversation_workflow import VALID_STATES as REQUEST_STATES

HOST='ntfy.sh'
TERMINAL={'job':{'complete','responded','failed','cancelled'},'conversation':{'responded','failed','cancelled'}}
TABLE={'job':'jobs','conversation':'conversation_requests'}
STATES={'job':JOB_STATES,'conversation':REQUEST_STATES}
MAX_RESPONSE=32768

def destination(topic,token):
    if not isinstance(topic,str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,64}',topic):raise ValueError('Use an exact dedicated topic (16–64 safe characters)')
    if not isinstance(token,str) or not re.fullmatch(r'tk_[A-Za-z0-9_-]{16,100}',token):raise ValueError('Use a dedicated ntfy access token')
def selected_state(path,kind,ident,project,chat):
    if kind not in TABLE or type(ident) is not int or not 1<=ident<=2147483647 or not isinstance(project,str) or not project or not isinstance(chat,str) or not chat:raise ValueError('Invalid exact status scope')
    path=Path(path)
    if not path.is_file() or path.is_symlink():raise ValueError('Local state unavailable')
    with closing(sqlite3.connect(path.resolve(strict=True).as_uri()+'?mode=ro',uri=True,timeout=.5)) as db:
        db.execute('PRAGMA query_only=ON')
        row=db.execute('SELECT state FROM '+TABLE[kind]+' WHERE id=? AND project=? AND chat_id=?',(ident,project,chat)).fetchone()
    if not row or row[0] not in STATES[kind]:raise ValueError('Selected record is unavailable in this scope')
    return row[0]

def message(kind,state):
    if kind not in TERMINAL or state not in TERMINAL[kind]:raise ValueError('Terminal state required')
    return 'JANUS '+kind+' status: '+state+'.'

def publish(topic,token,kind,state,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise PermissionError('Explicit notification approval required')
    destination(topic,token);body=message(kind,state)
    payload=json.dumps({'topic':topic,'title':'JANUS status','message':body},ensure_ascii=True,separators=(',',':')).encode('ascii')
    deadline=time.monotonic()+25
    stopped(cancelled,deadline);ip=resolve_public(HOST,resolver);stopped(cancelled,deadline)
    conn=connection(HOST,ip)
    try:
        conn.request('POST','/',body=payload,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','Accept':'application/json','Accept-Encoding':'identity','Connection':'close','User-Agent':'JANUS-status/1'})
        response=conn.getresponse();stopped(cancelled,deadline)
        if response.status!=200 or response.headers.get_content_type()!='application/json' or response.getheader('Content-Encoding','identity').lower()!='identity':
            raise ValueError('Notification outcome unconfirmed')
        data=bytearray()
        while True:
            stopped(cancelled,deadline);part=response.read1(min(8192,MAX_RESPONSE-len(data)+1));stopped(cancelled,deadline)
            if not part:break
            data.extend(part)
            if len(data)>MAX_RESPONSE:raise ValueError('Receipt exceeds bound')
        row=strict_json(data.decode('utf-8'))
        if not isinstance(row,dict) or row.get('event')!='message' or row.get('topic')!=topic or row.get('message')!=body or not isinstance(row.get('id'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',row['id']):
            raise ValueError('Unexpected provider receipt')
        return {'status':'provider_accepted','message_id':row['id'],'response_sha256':hashlib.sha256(data).hexdigest(),'device_delivery_verified':False}
    finally:conn.close()

def watch(read,kind,topic,token,cancelled,*,approved=False,seconds=300,clock=time.monotonic,wait=time.sleep,sender=publish):
    if approved is not True:raise PermissionError('Explicit finite notification watch approval required')
    destination(topic,token)
    if kind not in TERMINAL or type(seconds) is not int or not 5<=seconds<=300:raise ValueError('Invalid finite watch')
    end=clock()+seconds
    while clock()<end:
        if cancelled and cancelled():raise TimeoutError('Notification watch stopped')
        state=read()
        if state not in STATES[kind]:raise ValueError('Unexpected record state')
        if state in TERMINAL[kind]:
            if cancelled and cancelled() or clock()>=end:raise TimeoutError('Notification watch stopped')
            # Exactly one submission attempt, never retry an uncertain outcome.
            return sender(topic,token,kind,state,cancelled,approved=True)
        wait(min(3,max(0,end-clock())))
    return {'status':'watch_expired','device_delivery_verified':False}
