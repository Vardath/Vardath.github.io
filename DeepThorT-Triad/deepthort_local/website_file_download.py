"""Reviewed static public link download; no browser execution or automatic opening."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import socket
import sys
import time
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.structured_source import strict_json
from deepthort_local.website_monitor import checked_url,resolve_public,PinnedHTTPS,stopped
from deepthort_local.website_crawling import allowed_link,robots_policy
from deepthort_local.webpage_retrieval import fetch_page
from deepthort_local.webpage_elements import extract_elements
from deepthort_local.website_control_selection import checked as control_checked,selected,HASH

SCHEMA='janus-reviewed-file-download-v1'
EXTRA=('inspection','.json')
MAX_BYTES=8*1024*1024
MIMES={'application/octet-stream','application/pdf','application/zip','text/plain','text/csv','application/json',
       'image/png','image/jpeg','image/webp','audio/wav','audio/mpeg','video/mp4'}

def selection(s):
    return {k:s[k] for k in ('inspection','locator','path_prefix','destination')}|{'tag':'a','action':'read_link'}

def checked(s):
    if not isinstance(s,dict) or set(s)!={'inspection','locator','path_prefix','destination','mime','max_bytes','expected_sha256'}:
        raise ValueError('Expected exact inspected link, MIME, size ceiling and optional expected digest')
    control_checked(selection(s))
    if s['mime'] not in MIMES or type(s['max_bytes']) is not int or not 1<=s['max_bytes']<=MAX_BYTES:
        raise ValueError('Unsupported download MIME or byte ceiling')
    digest=s['expected_sha256']
    if digest is not None and (not isinstance(digest,str) or not HASH.fullmatch(digest)):
        raise ValueError('Expected SHA-256 must be lowercase hex or null')
    return s

def read_review(root,plan):
    s,dst,src=guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
    evidence=selected(selection(s),strict_json(guard.exact(src,plan['guards'][1],guard.MAX_INPUT).decode('utf-8-sig')))
    return s,dst,evidence

def fetch_bytes(s,*,approved=False,cancelled=None,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    checked(s)
    if approved is not True:raise ValueError('Explicit download approval required')
    host,path=checked_url(s['destination']);deadline=time.monotonic()+35
    stopped(cancelled,deadline);ip=resolve_public(host,resolver);stopped(cancelled,deadline)
    conn=connection(host,ip)
    try:
        conn.request('GET',path,headers={'User-Agent':'JANUS-local-research/1.0','Accept':s['mime'],
                                         'Accept-Encoding':'identity','Connection':'close'})
        response=conn.getresponse();stopped(cancelled,deadline)
        if response.status!=200 or response.headers.get_content_type()!=s['mime'] or response.getheader('Content-Encoding','identity').lower()!='identity':
            raise ValueError('Unexpected download response; redirects and compression refused')
        length=response.getheader('Content-Length')
        if length is not None and (not length.isdecimal() or not 1<=int(length)<=s['max_bytes']):
            raise ValueError('Invalid download length')
        data=bytearray()
        while True:
            stopped(cancelled,deadline)
            chunk=response.read1(min(32768,s['max_bytes']-len(data)+1))
            stopped(cancelled,deadline)
            if not chunk:break
            data.extend(chunk)
            if len(data)>s['max_bytes']:raise ValueError('Download exceeds byte ceiling')
        if not data or (length is not None and len(data)!=int(length)):raise ValueError('Empty or incomplete download')
        return bytes(data)
    finally:conn.close()

def run(s,evidence,*,approved=False,cancelled=None,retrieve=fetch_page,download=fetch_bytes,clock=time.monotonic,sleep=time.sleep):
    checked(s)
    if approved is not True:raise ValueError('Explicit download approval required')
    url=evidence['url'];host,path=checked_url(url);target=s['destination'];prefix=s['path_prefix']
    if not allowed_link(url,host,prefix) or not allowed_link(target,host,prefix) or url==target:
        raise ValueError('Link outside reviewed scope')
    deadline=clock()+100
    def stop():return bool((cancelled and cancelled()) or clock()>=deadline)
    def check():
        if stop():raise TimeoutError('Download stopped')
    def wait(delay):
        until=clock()+delay
        while clock()<until:
            check();sleep(min(.25,until-clock()))
    check();robots_url='https://'+host+'/robots.txt'
    robots=retrieve(robots_url,approved=True,cancelled=stop)
    if robots.get('url')!=robots_url or robots.get('mime')!='text/plain':raise ValueError('Exact robots policy required')
    permit,delay=robots_policy(robots['text'])
    if not permit(path) or not permit(checked_url(target)[1]):raise ValueError('Robots policy forbids download')
    wait(delay);check()
    fresh=selected(selection(s),retrieve(url,approved=True,cancelled=stop,extractor=extract_elements))
    if fresh!=evidence:raise ValueError('Reviewed source or anchor changed')
    wait(delay);check()
    data=download(s,approved=True,cancelled=stop);check()
    if not isinstance(data,bytes) or not 1<=len(data)<=s['max_bytes']:raise ValueError('Invalid received bytes')
    digest=hashlib.sha256(data).hexdigest()
    if s['expected_sha256'] is not None and digest!=s['expected_sha256']:raise ValueError('Expected download digest mismatch')
    receipt={'schema':SCHEMA,'source':fresh,'destination':target,'mime':s['mime'],'bytes':len(data),
             'sha256':digest,'expected_sha256':s['expected_sha256'],'expected_digest_matched':s['expected_sha256'] is not None,
             'robots_response_sha256':robots['response_sha256'],'browser_used':False,'content_safety_verified':False,
             'executed':False,'payload':'payload.bin'}
    return data,receipt

def review(root,source,output,exclude=()):
    plan,_=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
    s,_,evidence=read_review(root,plan)
    return plan,dict(s,selected_control=evidence,network_consent='Read same-host robots.txt, recheck inspected HTML and anchor, then GET exact reviewed public file. Save inert bytes in a new ZIP with digest receipt. No redirects, scripts, login, automatic extraction or opening.')

def execute(root,plan,*,runner=run):
    s,dst,evidence=read_review(root,plan);data,receipt=runner(s,evidence,approved=True)
    digest=hashlib.sha256(data).hexdigest()
    if (not isinstance(data,bytes) or not 1<=len(data)<=s['max_bytes'] or receipt.get('sha256')!=digest
        or receipt.get('destination')!=s['destination'] or receipt.get('mime')!=s['mime']
        or receipt.get('source')!=evidence or receipt.get('bytes')!=len(data)
        or (s['expected_sha256'] is not None and s['expected_sha256']!=digest)):
        raise ValueError('Download receipt mismatch')
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_STORED) as z:
        z.writestr('payload.bin',data);z.writestr('receipt.json',json.dumps(receipt,sort_keys=True,indent=2,ensure_ascii=True))
    payload=buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.namelist()!=['payload.bin','receipt.json'] or z.testzip() is not None or z.read('payload.bin')!=data or json.loads(z.read('receipt.json'))!=receipt:
            raise ValueError('Download bundle verification failed')
    bundle_sha=guard.publish(payload,dst,lambda:read_review(root,plan))
    return {'schema':SCHEMA,'status':'download_bytes_saved','output':plan['output'],'sha256':bundle_sha,
            'payload_sha256':digest,'bytes':len(data),'browser_used':False,'content_safety_verified':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Download unavailable; verify approved scope, response and digest'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
