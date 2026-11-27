"""Reviewed bounded Gmail inbox label organisation; no delete, trash or automatic retry."""
from __future__ import annotations
import hashlib
import json
import re
import socket
import time
from urllib.parse import urlencode
from .gmail_read import BASE,HOST,ID,MAX_RESPONSE,profile,request,token_checked,message
from .gmail_send import address
from .website_monitor import PinnedHTTPS,resolve_public,stopped
from .structured_source import strict_json

SCHEMA='janus-gmail-organise-v1'
LABEL=re.compile(r'(?:Label_[A-Za-z0-9_-]{1,100}|INBOX|STARRED|IMPORTANT|UNREAD)')
MAX_MESSAGES=5

def labels(values,*,reviewed=False):
    if not isinstance(values,list) or len(values)>100 or any(not isinstance(x,str) or not ID.fullmatch(x) for x in values) or len(set(values))!=len(values):
        raise ValueError('Invalid label inventory')
    if reviewed and (len(values)>5 or any(not LABEL.fullmatch(x) for x in values)):
        raise ValueError('Use existing user labels or INBOX, STARRED, IMPORTANT, UNREAD')
    return sorted(values)

def checked(s):
    if not isinstance(s,dict) or set(s)!={'account','query','limit','add','remove'}:
        raise ValueError('Expected account, query, limit, add and remove')
    address(s['account'])
    if not isinstance(s['query'],str) or not s['query'].strip() or len(s['query'])>500 or any(not c.isprintable() for c in s['query']) or type(s['limit']) is not int or not 1<=s['limit']<=MAX_MESSAGES:
        raise ValueError('Use explicit bounded search and 1–5 results')
    add=labels(s['add'],reviewed=True);remove=labels(s['remove'],reviewed=True)
    if not (add or remove) or set(add)&set(remove):raise ValueError('Choose nonconflicting label changes')
    return dict(s,add=add,remove=remove)

def metadata(row,ident):
    result=message(row,ident,False)
    result['labels']=labels(row.get('labelIds',[]))
    if {'TRASH','SPAM'}&set(result['labels']):raise ValueError('Trash and spam excluded')
    return result

def _get_metadata(get,ident):
    return metadata(get('/messages/'+ident+'?'+urlencode({'format':'metadata','metadataHeaders':['From','Subject','Date'],'fields':'id,labelIds,snippet,payload(headers)'},doseq=True)),ident)

def preview(s,token,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise PermissionError('Explicit mail search approval required')
    s=checked(s)
    def get(path):
        return request(BASE+path,token,cancelled,resolver=resolver,connection=connection)[0]
    account=profile(s,get('/profile?fields=emailAddress'))
    found=get('/messages?'+urlencode({'q':s['query'],'maxResults':s['limit'],'includeSpamTrash':'false','fields':'messages(id),nextPageToken'}))
    if not isinstance(found,dict) or not isinstance(found.get('messages',[]),list) or len(found.get('messages',[]))>s['limit']:
        raise ValueError('Unexpected search inventory')
    ids=[]
    for row in found.get('messages',[]):
        ident=row.get('id') if isinstance(row,dict) else None
        if not isinstance(ident,str) or not ID.fullmatch(ident) or ident in ids:raise ValueError('Unexpected message identity')
        ids.append(ident)
    rows=[]
    for ident in ids:
        row=_get_metadata(get,ident)
        target=sorted((set(row['labels'])|set(s['add']))-set(s['remove']))
        if target!=row['labels']:
            rows.append(dict(row,target_labels=target))
    if profile(s,get('/profile?fields=emailAddress'))!=account:raise ValueError('Account changed')
    return {'schema':SCHEMA,'spec':s,'account':account,'rows':rows,'more_results':bool(found.get('nextPageToken')),
            'expires_at':int(time.time())+300,'remote_changed':False}

def modify(ident,add,remove,token,cancelled,*,resolver,connection):
    if not isinstance(ident,str) or not ID.fullmatch(ident):raise ValueError('Invalid message ID')
    add=labels(add,reviewed=True);remove=labels(remove,reviewed=True)
    if not (add or remove) or set(add)&set(remove):raise ValueError('Invalid label change')
    token_checked(token);deadline=time.monotonic()+25
    stopped(cancelled,deadline);ip=resolve_public(HOST,resolver);stopped(cancelled,deadline)
    conn=connection(HOST,ip)
    try:
        stopped(cancelled,deadline)
        payload=json.dumps({'addLabelIds':add,'removeLabelIds':remove},separators=(',',':')).encode()
        conn.request('POST',BASE+'/messages/'+ident+'/modify',body=payload,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','Accept':'application/json','Accept-Encoding':'identity','Connection':'close','User-Agent':'JANUS-reviewed-mail/1.0'})
        r=conn.getresponse();stopped(cancelled,deadline)
        if r.status!=200 or r.headers.get_content_type()!='application/json' or r.getheader('Content-Encoding','identity').lower()!='identity':raise ValueError('Modify outcome uncertain')
        length=r.getheader('Content-Length')
        if length is not None and (not length.isdecimal() or not 0<int(length)<=MAX_RESPONSE):raise ValueError('Response exceeds bound')
        chunks=[];size=0
        while True:
            stopped(cancelled,deadline);part=r.read1(min(32768,MAX_RESPONSE-size+1));stopped(cancelled,deadline)
            if not part:break
            size+=len(part)
            if size>MAX_RESPONSE:raise ValueError('Response exceeds bound')
            chunks.append(part)
        if length is not None and size!=int(length):raise ValueError('Incomplete modify receipt')
        raw=b''.join(chunks)
        return strict_json(raw.decode('utf-8')),hashlib.sha256(raw).hexdigest()
    finally:conn.close()

def apply(plan,token,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise PermissionError('Explicit exact message and label change approval required')
    if not isinstance(plan,dict) or set(plan)!={'schema','spec','account','rows','more_results','expires_at','remote_changed'} or plan['schema']!=SCHEMA or plan['remote_changed'] is not False or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+300:
        raise ValueError('Invalid or expired inbox review')
    s=checked(plan['spec']);rows=plan['rows']
    if not isinstance(rows,list) or not 1<=len(rows)<=s['limit']:raise ValueError('No bounded reviewed changes')
    def get(path):
        return request(BASE+path,token,cancelled,resolver=resolver,connection=connection)[0]
    if profile(s,get('/profile?fields=emailAddress'))!=plan['account']:raise ValueError('Account changed')
    ids=set()
    for row in rows:
        if not isinstance(row,dict):raise ValueError('Invalid reviewed message')
        ident=row.get('message_id')
        if not isinstance(ident,str) or not ID.fullmatch(ident) or ident in ids:raise ValueError('Invalid reviewed ID')
        ids.add(ident)
        actual=_get_metadata(get,ident)
        target=sorted((set(actual['labels'])|set(s['add']))-set(s['remove']))
        if target==actual['labels'] or dict(actual,target_labels=target)!=row:raise ValueError('Reviewed message or labels changed; no writes performed')
    confirmed=[]
    for row in rows:
        ident=row['message_id']
        try:
            if time.time()>=plan['expires_at']:raise ValueError('Review expired')
            if profile(s,get('/profile?fields=emailAddress'))!=plan['account']:raise ValueError('Account changed')
            actual=_get_metadata(get,ident)
            if actual!={k:v for k,v in row.items() if k!='target_labels'}:raise ValueError('Message changed')
            before=set(row['labels']);after=set(row['target_labels'])
            add=sorted(after-before);remove=sorted(before-after)
            response,digest=modify(ident,add,remove,token,cancelled,resolver=resolver,connection=connection)
            if not isinstance(response,dict) or response.get('id')!=ident or labels(response.get('labelIds',[]))!=sorted(after):
                raise ValueError('Unconfirmed label receipt')
            confirmed.append({'message_id':ident,'added':add,'removed':remove,'response_sha256':digest,
                              'inverse_add':remove,'inverse_remove':add})
        except Exception:
            return {'schema':SCHEMA,'status':'stopped_uncertain','account':plan['account'],'confirmed':confirmed,
                    'uncertain_message_id':ident,'remaining_not_attempted':len(rows)-len(confirmed)-1,
                    'automatic_retry':False,'deleted':False,'atomic':False}
    return {'schema':SCHEMA,'status':'reviewed_labels_modified','account':plan['account'],'confirmed':confirmed,
            'automatic_retry':False,'deleted':False,'atomic':False}
