"""Reviewed single text post to mastodon.social; no retry or credential storage."""
from __future__ import annotations
import hashlib
import re
import socket
import time
import uuid
from urllib.parse import urlencode
from .gmail_read import token_checked
from .structured_source import strict_json
from .website_monitor import PinnedHTTPS, resolve_public, stopped

HOST='mastodon.social'
ACCOUNT=re.compile(r'[A-Za-z0-9_]{1,30}')
ID=re.compile(r'[0-9]{1,40}')
MAX_RESPONSE=1024*1024

def checked(s):
    if not isinstance(s,dict) or set(s)!={'account','text','visibility'}:
        raise ValueError('Specify exact local account, text and visibility')
    if not isinstance(s['account'],str) or not ACCOUNT.fullmatch(s['account']):
        raise ValueError('Use the mastodon.social username without @')
    text=s['text']
    if not isinstance(text,str) or not text.strip() or len(text)>400 or any(not (c.isprintable() or c=='\n') for c in text):
        raise ValueError('Enter 1–400 printable characters')
    if s['visibility'] not in ('public','unlisted'):
        raise ValueError('Choose public or unlisted visibility')
    return dict(s)

def request(path,token,cancelled,*,body=None,key=None,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    token_checked(token);deadline=time.monotonic()+25
    if (path,body is None) not in (('/api/v1/accounts/verify_credentials',True),('/api/v1/statuses',False)):
        raise ValueError('Unexpected social API operation')
    stopped(cancelled,deadline);ip=resolve_public(HOST,resolver);stopped(cancelled,deadline)
    conn=connection(HOST,ip)
    headers={'Authorization':'Bearer '+token,'Accept':'application/json','Accept-Encoding':'identity',
             'User-Agent':'JANUS-reviewed-social/1.0','Connection':'close'}
    try:
        if body is None:
            conn.request('GET',path,headers=headers)
        else:
            headers.update({'Content-Type':'application/x-www-form-urlencoded','Idempotency-Key':key})
            conn.request('POST',path,body=body,headers=headers)
        r=conn.getresponse();stopped(cancelled,deadline)
        if r.status!=200 or r.headers.get_content_type()!='application/json' or r.getheader('Content-Encoding','identity').lower()!='identity':
            raise ValueError('Social response refused; no redirects or retry')
        length=r.getheader('Content-Length')
        if length is not None and (not length.isdecimal() or not 0<int(length)<=MAX_RESPONSE):
            raise ValueError('Social response exceeds bound')
        chunks=[];size=0
        while True:
            stopped(cancelled,deadline);part=r.read1(min(32768,MAX_RESPONSE-size+1));stopped(cancelled,deadline)
            if not part:break
            size+=len(part)
            if size>MAX_RESPONSE:raise ValueError('Social response exceeds bound')
            chunks.append(part)
        if not size or (length is not None and size!=int(length)):raise ValueError('Incomplete social response')
        return strict_json(b''.join(chunks).decode('utf-8'))
    finally:conn.close()

def account(s,row):
    if not isinstance(row,dict) or row.get('acct')!=s['account'] or row.get('username')!=s['account'] or not isinstance(row.get('id'),str) or not ID.fullmatch(row['id']):
        raise ValueError('Mastodon account identity mismatch')
    return row['id']

def publish(s,token,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise PermissionError('Explicit final publishing approval required')
    s=checked(s);token_checked(token)
    def call(path,**kw):
        return request(path,token,cancelled,resolver=resolver,connection=connection,**kw)
    owner=account(s,call('/api/v1/accounts/verify_credentials'))
    body=urlencode({'status':s['text'],'visibility':s['visibility']}).encode('ascii')
    key=uuid.uuid4().hex
    # One mutation only. Errors after sending are uncertain, never retried.
    result=call('/api/v1/statuses',body=body,key=key)
    if not isinstance(result,dict) or not isinstance(result.get('id'),str) or not ID.fullmatch(result['id']) or result.get('visibility')!=s['visibility'] or account(s,result.get('account'))!=owner:
        raise ValueError('Post receipt unverified; inspect account before any retry')
    return {'schema':'janus-mastodon-post-v1','host':HOST,'account':s['account'],'account_id':owner,
            'post_id':result['id'],'visibility':s['visibility'],'requested_text_sha256':hashlib.sha256(s['text'].encode()).hexdigest(),
            'provider_accepted':True,'rendered_text_verified':False,'reach_verified':False,'automatic_retry':False}
