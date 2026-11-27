"""Explicit bounded loopback HTTP GET acceptance tests; no redirects or credentials."""
from __future__ import annotations
import argparse
import hashlib
import http.client
import json
import math
from pathlib import Path
import re
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import ID
from deepthort_local.structured_source import strict_json
SCHEMA='janus-loopback-api-tests-v1'
MAX_BODY=65536
MAX_CASES=8
PATH=re.compile(r'/[A-Za-z0-9_./~-]{0,300}\Z')
def target(port,path):
    if type(port) is not int or not 1024<=port<=65535 or port==8765:
        raise ValueError('Choose a project test port; JANUS control port refused')
    if not isinstance(path,str) or not PATH.fullmatch(path) or path.startswith('//') or any(v in ('.','..') for v in path.split('/')):
        raise ValueError('Use an exact loopback path without query, fragments or traversal')
def value(v):
    if v is None or type(v) in (bool,int):return v
    if type(v) is float and math.isfinite(v):return v
    if isinstance(v,str) and len(v)<=1000:return v
    raise ValueError('Expected bounded JSON scalar')
def checked(s):
    if not isinstance(s,dict) or set(s)!={'port','cases'} or not isinstance(s['cases'],list) or not 1<=len(s['cases'])<=MAX_CASES:
        raise ValueError('Expected port and 1–8 GET cases')
    ids=set()
    for c in s['cases']:
        if not isinstance(c,dict) or set(c)!={'id','path','status','json_fields'} or not isinstance(c['id'],str) or not ID.fullmatch(c['id']) or c['id'] in ids:
            raise ValueError('Invalid test case')
        ids.add(c['id']);target(s['port'],c['path'])
        if type(c['status']) is not int or not 200<=c['status']<=599 or not isinstance(c['json_fields'],dict) or len(c['json_fields'])>16:
            raise ValueError('Invalid expected response')
        for k,v in c['json_fields'].items():
            if not isinstance(k,str) or not 1<=len(k)<=100:raise ValueError('Invalid field')
            value(v)
    return s
def fetch(port,path):
    target(port,path)
    connection=http.client.HTTPConnection('127.0.0.1',port,timeout=2)
    start=time.monotonic()
    try:
        connection.request('GET',path,headers={'Accept':'application/json','Connection':'close'})
        response=connection.getresponse()
        if response.getheader('Content-Encoding','identity').casefold()!='identity':
            raise ValueError('Encoded responses unsupported')
        chunks=[];used=0
        while True:
            if time.monotonic()-start>5:raise TimeoutError('Response deadline exceeded')
            chunk=response.read1(min(8192,MAX_BODY+1-used))
            if not chunk:break
            used+=len(chunk)
            if used>MAX_BODY:raise ValueError('Response exceeds bound')
            chunks.append(chunk)
        return response.status,response.getheader('Content-Type','').split(';',1)[0].strip().casefold(),b''.join(chunks),round((time.monotonic()-start)*1000,3)
    finally:connection.close()
def same(a,b):
    return type(a) is type(b) and a==b
def run(s):
    checked(s);results=[]
    for c in s['cases']:
        try:
            status,content_type,body,elapsed=fetch(s['port'],c['path'])
            fields=[]
            if c['json_fields']:
                obj=None
                if content_type=='application/json':
                    try:obj=strict_json(body.decode('utf-8'))
                    except Exception:pass
                for k,v in c['json_fields'].items():
                    fields.append({'field':k,'matched':isinstance(obj,dict) and k in obj and same(obj[k],v)})
            results.append({'id':c['id'],'status':status,'expected_status':c['status'],
                'response_sha256':hashlib.sha256(body).hexdigest(),'response_bytes':len(body),'elapsed_ms':elapsed,
                'field_checks':fields,'passed':status==c['status'] and all(x['matched'] for x in fields)})
        except (OSError,http.client.HTTPException,ValueError) as exc:
            results.append({'id':c['id'],'passed':False,'error_type':type(exc).__name__})
    return {'schema':'janus-loopback-api-test-result-v1','target':'127.0.0.1:'+str(s['port']),
        'cases':results,'all_passed':all(r['passed'] for r in results),
        'scope':'Explicit GET requests to reviewed local project service only. No redirect following, response body publication, authentication, mutation tests or external network.'}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,scope='Execute listed local GET requests once against an already running project service.')
def execute(root,plan):
    s,dst,_=validate(root,plan);r=run(s)
    digest=guard.publish(json.dumps(r,ensure_ascii=True,allow_nan=False,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'status':'api_tests_completed','output':plan['output'],'sha256':digest,'cases':len(r['cases']),'all_passed':r['all_passed']}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Loopback API testing unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
