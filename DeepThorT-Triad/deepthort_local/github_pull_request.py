"""Explicit GitHub draft pull-request creation; fixed HTTPS host, transient token."""
from __future__ import annotations
import hashlib
import json
import re
import socket
import time
from .website_monitor import PinnedHTTPS,resolve_public,stopped
from .web_search import token_checked
from .structured_source import strict_json
HOST='api.github.com'
MAX_RESPONSE=1024*1024

def repository(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}',value) or value.split('/')[1] in ('.','..'):
        raise ValueError('Use an exact owner/repository')
    return value
def branch(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./-]{0,79}',value) or '..' in value or any(not p or p.startswith('.') or p.endswith('.lock') or p.endswith('.') for p in value.split('/')):
        raise ValueError('Use an explicit branch name')
    return value
def literal(value,limit,*,multiline=False):
    if not isinstance(value,str) or not value.strip() or len(value)>limit or any((ord(c)<32 and not (multiline and c in '\n\t')) or 127<=ord(c)<=159 or 0xd800<=ord(c)<=0xdfff for c in value):
        raise ValueError('Invalid bounded text')
    return value
def checked(s):
    if not isinstance(s,dict) or set(s)!={'repository','head','base','title','body'}:raise ValueError('Expected repository, head, base, title and body')
    repository(s['repository']);branch(s['head']);branch(s['base'])
    if s['head']==s['base']:raise ValueError('Choose different branches')
    literal(s['title'],160);literal(s['body'],4000,multiline=True)
    return dict(s)

def _request(method,path,payload,token,cancelled,*,resolver,connection,expected):
    token_checked(token);deadline=time.monotonic()+25
    stopped(cancelled,deadline);ip=resolve_public(HOST,resolver);stopped(cancelled,deadline)
    conn=connection(HOST,ip)
    try:
        headers={'Accept':'application/vnd.github+json','Accept-Encoding':'identity','Authorization':'Bearer '+token,
                 'User-Agent':'JANUS-reviewed-github/1.0','Connection':'close','X-GitHub-Api-Version':'2022-11-28'}
        if payload is not None:headers['Content-Type']='application/json'
        conn.request(method,path,body=payload,headers=headers)
        response=conn.getresponse();stopped(cancelled,deadline)
        if response.status!=expected:raise ValueError('GitHub did not return expected status; inspect remote before retrying')
        if response.headers.get_content_type()!='application/json' or response.getheader('Content-Encoding','identity').lower()!='identity':
            raise ValueError('Unexpected GitHub response')
        size=0;chunks=[]
        length=response.getheader('Content-Length')
        if length is not None and (not length.isdecimal() or not 0<int(length)<=MAX_RESPONSE):raise ValueError('Response exceeds bound')
        while True:
            stopped(cancelled,deadline);part=response.read1(min(32768,MAX_RESPONSE-size+1));stopped(cancelled,deadline)
            if not part:break
            size+=len(part)
            if size>MAX_RESPONSE:raise ValueError('Response exceeds bound')
            chunks.append(part)
        if length is not None and size!=int(length):raise ValueError('Incomplete response')
        raw=b''.join(chunks)
        return strict_json(raw.decode('utf-8')),hashlib.sha256(raw).hexdigest()
    finally:conn.close()

def create(s,token,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise ValueError('Explicit approval required for remote draft creation')
    s=checked(s);repo=s['repository']
    body=json.dumps({k:s[k] for k in ('head','base','title','body')}|{'draft':True},ensure_ascii=True).encode('ascii')
    result,digest=_request('POST','/repos/'+repo+'/pulls',body,token,cancelled,resolver=resolver,connection=connection,expected=201)
    if not isinstance(result,dict) or type(result.get('number')) is not int or result['number']<=0 or result.get('draft') is not True:
        raise ValueError('Unexpected pull request receipt; inspect remote before retry')
    n=result['number']
    for key in ('head','base'):
        part=result.get(key)
        if not isinstance(part,dict) or part.get('ref')!=s[key] or not isinstance(part.get('repo'),dict) or str(part['repo'].get('full_name','')).casefold()!=repo.casefold():
            raise ValueError('Remote receipt differs from reviewed branches')
    return {'status':'remote_draft_created','repository':repo,'number':n,'url':'https://github.com/'+repo+'/pull/'+str(n),
            'draft':True,'response_sha256':digest,'merged':False,'pushed':False}
