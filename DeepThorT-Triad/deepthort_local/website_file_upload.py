"""Single explicitly reviewed public HTTPS multipart file upload; no live browser."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import socket
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.website_monitor import checked_url,resolve_public,PinnedHTTPS,stopped
from deepthort_local.website_crawling import safe_path
from deepthort_local.rest_api import key

SCHEMA='janus-reviewed-file-upload-v1'
MAX_FILE=4*1024*1024
MAX_RESPONSE=128*1024
TYPES={'.txt':'text/plain','.csv':'text/csv','.pdf':'application/pdf','.png':'image/png',
       '.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.wav':'audio/wav',
       '.mp3':'audio/mpeg','.mp4':'video/mp4','.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
       '.xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
       '.pptx':'application/vnd.openxmlformats-officedocument.presentationml.presentation'}
EXTRA=('file',set(TYPES))
def checked(s):
    if not isinstance(s,dict) or set(s)!={'url','file','field','filename'}:
        raise ValueError('Expected exact endpoint, project file, multipart field and disclosed filename')
    _,path=checked_url(s['url']);safe_path(path)
    key(s['field'])
    if not isinstance(s['file'],str) or not isinstance(s['filename'],str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,99}',s['filename']):
        raise ValueError('Use an explicit safe disclosed filename')
    suffix=Path(s['file']).suffix.casefold()
    if suffix not in TYPES or Path(s['filename']).suffix.casefold()!=suffix:
        raise ValueError('Unsupported or mismatched upload extension')
    return s

def read_review(root,plan):
    s,dst,src=guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    data=guard.exact(src,plan['guards'][1],MAX_FILE)
    return s,dst,data

def multipart(s,data):
    checked(s)
    if not isinstance(data,bytes) or not 1<=len(data)<=MAX_FILE:raise ValueError('File exceeds upload bounds')
    boundary='JANUS-'+hashlib.sha256(data).hexdigest()
    if boundary.encode('ascii') in data:raise ValueError('Multipart delimiter collision')
    mime=TYPES[Path(s['file']).suffix.casefold()]
    head=(f'--{boundary}\r\nContent-Disposition: form-data; name="{s["field"]}"; filename="{s["filename"]}"\r\n'
          f'Content-Type: {mime}\r\n\r\n').encode('ascii')
    body=head+data+f'\r\n--{boundary}--\r\n'.encode('ascii')
    return boundary,body

def send(s,data,*,approved=False,cancelled=None,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise PermissionError('Explicit file disclosure approval required')
    boundary,body=multipart(s,data)
    host,path=checked_url(s['url']);deadline=time.monotonic()+35
    stopped(cancelled,deadline);ip=resolve_public(host,resolver);stopped(cancelled,deadline)
    conn=connection(host,ip)
    try:
        conn.request('POST',path,body=body,headers={'User-Agent':'JANUS-reviewed-upload/1.0',
            'Accept':'application/json, text/plain','Accept-Encoding':'identity','Connection':'close',
            'Content-Type':'multipart/form-data; boundary='+boundary,'Content-Length':str(len(body))})
        response=conn.getresponse();stopped(cancelled,deadline)
        if not 200<=response.status<=599 or response.getheader('Content-Encoding','identity').lower()!='identity':
            raise ValueError('Unconfirmed response')
        length=response.getheader('Content-Length')
        if length is not None and (not length.isdecimal() or not 0<=int(length)<=MAX_RESPONSE):
            raise ValueError('Response exceeds bound')
        raw=bytearray()
        while True:
            stopped(cancelled,deadline);part=response.read1(min(8192,MAX_RESPONSE-len(raw)+1));stopped(cancelled,deadline)
            if not part:break
            raw.extend(part)
            if len(raw)>MAX_RESPONSE:raise ValueError('Response exceeds bound')
        if length is not None and len(raw)!=int(length):raise ValueError('Incomplete response')
        return {'http_status':response.status,'response_bytes':len(raw),'response_sha256':hashlib.sha256(raw).hexdigest()}
    finally:conn.close()

def review(root,source,output,exclude=()):
    plan,_=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    s,_,data=read_review(root,plan)
    return plan,dict(s,bytes_to_disclose=len(data),file_sha256=hashlib.sha256(data).hexdigest(),
        consent='The complete exact file bytes and disclosed filename leave this computer in ONE multipart POST to this public endpoint. May create remote state. Inspect file contents yourself before approval. No cookies, credentials, redirects, automatic retry or browser. Review remote outcome before any repeat.')

def execute(root,plan,*,sender=send):
    s,dst,data=read_review(root,plan)
    observed=sender(s,data,approved=True)
    if (not isinstance(observed,dict) or set(observed)!={'http_status','response_bytes','response_sha256'}
        or type(observed['http_status']) is not int or not 200<=observed['http_status']<=599
        or type(observed['response_bytes']) is not int or not 0<=observed['response_bytes']<=MAX_RESPONSE
        or not isinstance(observed['response_sha256'],str) or not re.fullmatch(r'[a-f0-9]{64}',observed['response_sha256'])):
        raise ValueError('Unconfirmed response evidence')
    r={'schema':SCHEMA,'url':s['url'],'field':s['field'],'filename':s['filename'],
       'file_sha256':hashlib.sha256(data).hexdigest(),'file_bytes':len(data),**observed,
       'http_success':200<=observed['http_status']<=299,'remote_storage_verified':False,
       'browser_used':False,'redirect_followed':False,'retried':False}
    digest=guard.publish(json.dumps(r,sort_keys=True,indent=2).encode(),dst,lambda:read_review(root,plan))
    return {'schema':SCHEMA,'status':'upload_response_observed','output':plan['output'],'sha256':digest,
            'http_status':r['http_status'],'remote_storage_verified':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'unconfirmed','error_type':type(e).__name__,'reason':'Upload may already have transmitted; inspect remote before any retry.'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
