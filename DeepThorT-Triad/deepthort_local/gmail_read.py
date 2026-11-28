"""Explicit reviewed Gmail search and plain-text message reading; no remote writes."""
from __future__ import annotations
import base64
import hashlib
import re
import socket
import time
from urllib.parse import urlencode
from .website_monitor import PinnedHTTPS,resolve_public,stopped
from .structured_source import strict_json

HOST='gmail.googleapis.com'
BASE='/gmail/v1/users/me'
MAX_RESPONSE=1024*1024
ID=re.compile(r'[A-Za-z0-9_-]{1,128}')
EMAIL=re.compile(r'[A-Za-z0-9.!#$%&\x27*+/=?^_~-]{1,128}@[A-Za-z0-9.-]{1,253}')

def checked(s):
    if not isinstance(s,dict) or s.get('operation') not in ('search','read'):
        raise ValueError('Choose search or read')
    if not isinstance(s.get('account'),str) or not EMAIL.fullmatch(s['account']):
        raise ValueError('Choose exact Gmail account address')
    if s['operation']=='search':
        if set(s)!={'operation','account','query','limit'} or not isinstance(s['query'],str) or not 1<=len(s['query'])<=500 or any(ord(c)<32 for c in s['query']) or type(s['limit']) is not int or not 1<=s['limit']<=5:
            raise ValueError('Enter a bounded explicit Gmail search and 1–5 results')
    elif set(s)!={'operation','account','message_id'} or not isinstance(s['message_id'],str) or not ID.fullmatch(s['message_id']):
        raise ValueError('Choose exact message ID')
    return s

def token_checked(token):
    if not isinstance(token,str) or not re.fullmatch(r'[A-Za-z0-9._~-]{8,2048}',token):
        raise ValueError('Invalid transient Google access token')
    return token

def request(path,token,cancelled,*,resolver,connection):
    token_checked(token);deadline=time.monotonic()+25
    stopped(cancelled,deadline);ip=resolve_public(HOST,resolver);stopped(cancelled,deadline)
    conn=connection(HOST,ip)
    try:
        conn.request('GET',path,headers={'Authorization':'Bearer '+token,'Accept':'application/json',
            'Accept-Encoding':'identity','User-Agent':'JANUS-reviewed-mail/1.0','Connection':'close'})
        r=conn.getresponse();stopped(cancelled,deadline)
        if r.status!=200 or r.headers.get_content_type()!='application/json' or r.getheader('Content-Encoding','identity').lower()!='identity':
            raise ValueError('Gmail response refused')
        length=r.getheader('Content-Length')
        if length is not None and (not length.isdecimal() or not 0<int(length)<=MAX_RESPONSE):raise ValueError('Response exceeds bound')
        chunks=[];size=0
        while True:
            stopped(cancelled,deadline);part=r.read1(min(32768,MAX_RESPONSE-size+1));stopped(cancelled,deadline)
            if not part:break
            size+=len(part)
            if size>MAX_RESPONSE:raise ValueError('Response exceeds bound')
            chunks.append(part)
        if length is not None and size!=int(length):raise ValueError('Incomplete Gmail response')
        raw=b''.join(chunks)
        return strict_json(raw.decode('utf-8')),hashlib.sha256(raw).hexdigest()
    finally:conn.close()

def safe_text(value,limit):
    if not isinstance(value,str):raise ValueError('Invalid message text')
    return ''.join(c if c.isprintable() or c in '\n\t' else ' ' for c in value[:limit])

def profile(s,row):
    if not isinstance(row,dict) or not isinstance(row.get('emailAddress'),str) or row['emailAddress'].casefold()!=s['account'].casefold():
        raise ValueError('Gmail account mismatch')
    return row['emailAddress']

def message(row,ident,full):
    if not isinstance(row,dict) or row.get('id')!=ident or not isinstance(row.get('payload'),dict):
        raise ValueError('Message identity mismatch')
    payload=row['payload'];headers=payload.get('headers',[])
    if not isinstance(headers,list) or len(headers)>200:raise ValueError('Invalid message headers')
    result={'message_id':ident,'headers':{},'snippet':safe_text(row.get('snippet',''),1000)}
    for h in headers:
        if not isinstance(h,dict) or not isinstance(h.get('name'),str):raise ValueError('Invalid header')
        key=h['name'].lower()
        if key in ('from','to','subject','date'):
            if key in result['headers']:raise ValueError('Ambiguous message header')
            result['headers'][key]=safe_text(h.get('value',''),1000)
    if full:
        parts=[];stack=[(payload,0)];count=0
        while stack:
            part,depth=stack.pop();count+=1
            if not isinstance(part,dict) or depth>8 or count>64:raise ValueError('MIME structure exceeds bound')
            children=part.get('parts',[])
            if not isinstance(children,list) or len(children)>64:raise ValueError('Invalid MIME children')
            stack.extend((child,depth+1) for child in reversed(children))
            if part.get('mimeType')!='text/plain' or part.get('filename',''):continue
            body=part.get('body',{})
            if not isinstance(body,dict):raise ValueError('Invalid MIME body')
            if body.get('attachmentId') or not body.get('data'):continue
            data=body['data']
            if not isinstance(data,str) or len(data)>90000 or not re.fullmatch(r'[A-Za-z0-9_-]+={0,2}',data):
                raise ValueError('Unsupported plain-text body')
            raw=base64.b64decode(data+'='*(-len(data)%4),altchars=b'-_',validate=True)
            if len(raw)>65536:raise ValueError('Plain-text body exceeds bound')
            parts.append(safe_text(raw.decode('utf-8',errors='replace'),16000))
        result['plain_text']='\n\n'.join(parts)[:16000]
        result['plain_text_available']=bool(parts)
        result['body_may_be_truncated']=sum(len(p) for p in parts)>=16000
    return result

def inspect(s,token,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise PermissionError('Explicit Gmail read approval required')
    s=checked(s);hashes=[]
    def get(path):
        value,digest=request(BASE+path,token,cancelled,resolver=resolver,connection=connection)
        hashes.append(digest);return value
    account=profile(s,get('/profile?fields=emailAddress'))
    if s['operation']=='search':
        listing=get('/messages?'+urlencode({'q':s['query'],'maxResults':s['limit'],'includeSpamTrash':'false','fields':'messages(id),nextPageToken'}))
        if not isinstance(listing,dict) or not isinstance(listing.get('messages',[]),list) or len(listing.get('messages',[]))>s['limit']:
            raise ValueError('Invalid bounded search results')
        ids=[]
        for item in listing.get('messages',[]):
            ident=item.get('id') if isinstance(item,dict) else None
            if not isinstance(ident,str) or not ID.fullmatch(ident) or ident in ids:raise ValueError('Invalid message ID')
            ids.append(ident)
        rows=[message(get('/messages/'+i+'?'+urlencode({'format':'metadata','metadataHeaders':['From','To','Subject','Date'],'fields':'id,snippet,payload(headers)'} ,doseq=True)),i,False) for i in ids]
        more=bool(listing.get('nextPageToken'))
    else:
        ident=s['message_id']
        rows=[message(get('/messages/'+ident+'?format=full'),ident,True)];more=False
    if profile(s,get('/profile?fields=emailAddress'))!=account:raise ValueError('Account changed during read')
    return {'schema':'janus-gmail-read-v1','account':account,'operation':s['operation'],'messages':rows,
            'more_results':more,'response_sha256':hashes,'remote_changed':False,'attachments_downloaded':False,
            'untrusted_mail_content':True,'model_dispatched':False,'persisted':False}
