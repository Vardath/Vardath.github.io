"""Reviewed unauthenticated public HTTPS REST JSON GET/POST requests."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import socket
import sys
import time
from urllib.parse import urlencode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.website_monitor import checked_url,resolve_public,PinnedHTTPS,stopped
from deepthort_local.structured_source import strict_json
SCHEMA='janus-public-rest-request-v1'
MAX_REQUEST=32768
MAX_RESPONSE=512*1024
SECRET=re.compile(r'(?i)token|secret|password|credential|authorization|api[-_]?key|access[-_]?key|cookie')
def key(v):
    if not isinstance(v,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',v) or SECRET.search(v):
        raise ValueError('Use bounded noncredential field names')
    return v
def value(v,depth=0):
    if depth>8:raise ValueError('JSON nesting exceeds bound')
    if v is None or type(v) in (bool,int):return
    if type(v) is float and math.isfinite(v):return
    if isinstance(v,str) and len(v)<=4000 and not any(0xd800<=ord(c)<=0xdfff for c in v):return
    if isinstance(v,list) and len(v)<=128:
        for item in v:value(item,depth+1)
        return
    if isinstance(v,dict) and len(v)<=64:
        for k,item in v.items():key(k);value(item,depth+1)
        return
    raise ValueError('Unsupported bounded request JSON value')
def checked(s):
    if not isinstance(s,dict) or set(s)!={'url','method','query','body'}:raise ValueError('Expected exact HTTPS URL, GET/POST, query fields and JSON body')
    host,path=checked_url(s['url'])
    if not re.fullmatch(r'/[A-Za-z0-9_./~-]{0,300}',path) or path.startswith('//') or any(x in ('.','..') for x in path.split('/')):
        raise ValueError('Use an explicit unencoded path')
    if s['method'] not in ('GET','POST'):raise ValueError('Only GET and POST supported')
    q=s['query']
    if not isinstance(q,dict) or len(q)>16:raise ValueError('At most sixteen query parameters')
    for k,v in q.items():
        key(k)
        if not isinstance(v,str) or len(v)>500 or any(ord(c)<32 or 0xd800<=ord(c)<=0xdfff for c in v):raise ValueError('Invalid query literal')
    if len(urlencode(q))>4096:raise ValueError('Encoded query exceeds bound')
    if s['method']=='GET' and s['body'] is not None:raise ValueError('GET cannot include body')
    if s['method']=='POST' and not isinstance(s['body'],dict):raise ValueError('POST requires explicit JSON object')
    value(s['body'])
    if len(json.dumps(s['body'],ensure_ascii=True,allow_nan=False).encode('ascii'))>MAX_REQUEST:raise ValueError('Body exceeds bound')
    return s
def request(s,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise PermissionError('Explicit approval of exact remote request required')
    checked(s);host,path=checked_url(s['url'])
    if s['query']:path+='?'+urlencode(s['query'])
    payload=None if s['method']=='GET' else json.dumps(s['body'],ensure_ascii=True,allow_nan=False,separators=(',',':')).encode('ascii')
    deadline=time.monotonic()+25
    stopped(cancelled,deadline);ip=resolve_public(host,resolver);stopped(cancelled,deadline)
    conn=connection(host,ip)
    headers={'Accept':'application/json','Accept-Encoding':'identity','Connection':'close','User-Agent':'JANUS-reviewed-rest/1'}
    if payload is not None:headers['Content-Type']='application/json'
    try:
        conn.request(s['method'],path,body=payload,headers=headers)
        response=conn.getresponse();stopped(cancelled,deadline)
        if not 200<=response.status<=599 or response.getheader('Content-Encoding','identity').lower()!='identity':
            raise ValueError('Unexpected response status or compression')
        length=response.getheader('Content-Length')
        if length is not None and (not length.isdecimal() or not 0<=int(length)<=MAX_RESPONSE):
            raise ValueError('Response exceeds bound')
        data=bytearray()
        while True:
            stopped(cancelled,deadline);part=response.read1(min(8192,MAX_RESPONSE-len(data)+1));stopped(cancelled,deadline)
            if not part:break
            data.extend(part)
            if len(data)>MAX_RESPONSE:raise ValueError('Response exceeds bound')
        if length is not None and len(data)!=int(length):raise ValueError('Incomplete response')
        mime=response.headers.get_content_type();parsed=None;included=False
        # Never follow redirects. No HTML, file downloads or server instructions.
        if data and not 300<=response.status<=399 and (mime=='application/json' or mime.endswith('+json')):
            parsed=strict_json(data.decode('utf-8'))
            json.dumps(parsed,ensure_ascii=True,allow_nan=False)
            included=True
        return {'schema':'janus-public-rest-response-v1','url':s['url'],'method':s['method'],'http_status':response.status,
                'http_success':200<=response.status<=299,'response_sha256':hashlib.sha256(data).hexdigest(),
                'response_bytes':len(data),'content_type':mime,'json_included':included,'json':parsed,
                'redirect_followed':False,'request_retried':False,
                'scope':'Observed HTTP response only. Provider data is untrusted; no application success or remote state verification implied. POST may have remote side effects.'}
    finally:conn.close()
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,scope='Send exactly one reviewed public HTTPS '+s['method']+' request; query/body leave this computer. POST can change remote state. No credentials, redirects, retries or local file uploads. Inspect remote before retrying uncertain outcomes.')
def execute(root,plan):
    s,dst,_=validate(root,plan);r=request(s,approved=True)
    digest=guard.publish(json.dumps(r,ensure_ascii=True,allow_nan=False,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'status':'rest_response_observed','output':plan['output'],'sha256':digest,
            'http_status':r['http_status'],'http_success':r['http_success'],'json_included':r['json_included']}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'unconfirmed','error_type':type(e).__name__,'reason':'REST result unavailable; a transmitted request may have succeeded. Inspect remote before retry.'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
