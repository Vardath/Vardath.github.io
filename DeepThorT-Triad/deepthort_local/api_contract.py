"""Create reviewed OpenAPI contracts for explicitly declared JSON endpoints."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import ID,literal
SCHEMA='janus-api-contract-v1'
METHODS={'get','post','put','patch','delete'}
PATH=re.compile(r'/(?:[a-zA-Z0-9_-]+|\{[a-zA-Z_][a-zA-Z0-9_]*\})(?:/(?:[a-zA-Z0-9_-]+|\{[a-zA-Z_][a-zA-Z0-9_]*\}))*\Z')
FIELD=re.compile(r'[a-zA-Z_][a-zA-Z0-9_]{0,63}\Z')
TYPES={'string','integer','number','boolean'}
def fields(items):
    if not isinstance(items,list) or len(items)>32:raise ValueError('Invalid bounded fields')
    seen=set()
    for f in items:
        if not isinstance(f,dict) or set(f)!={'name','type','required'} or not isinstance(f['name'],str) or not FIELD.fullmatch(f['name']) or f['name'] in seen or f['type'] not in TYPES or type(f['required']) is not bool:
            raise ValueError('Invalid field')
        seen.add(f['name'])
    return {'type':'object','properties':{f['name']:{'type':f['type']} for f in items},
            'required':[f['name'] for f in items if f['required']],'additionalProperties':False}
def checked(s):
    if not isinstance(s,dict) or set(s)!={'title','version','endpoints'}:raise ValueError('Expected API title, version and endpoints')
    literal(s['title'],200);literal(s['version'],80)
    endpoints=s['endpoints']
    if not isinstance(endpoints,list) or not 1<=len(endpoints)<=32:raise ValueError('Choose 1–32 endpoints')
    seen=set();ids=set();shapes={}
    for e in endpoints:
        if not isinstance(e,dict) or set(e)!={'path','method','id','summary','request','response','status'}:raise ValueError('Invalid endpoint')
        p=e['path'];m=e['method'];i=e['id']
        if not isinstance(p,str) or len(p)>200 or not PATH.fullmatch(p) or m not in METHODS or not isinstance(i,str) or not ID.fullmatch(i) or i in ids or (p,m) in seen:
            raise ValueError('Invalid or duplicate route')
        params=re.findall(r'\{([^}]+)\}',p)
        if len(params)!=len(set(params)):raise ValueError('Duplicate path parameter')
        shape=re.sub(r'\{[^}]+\}','{}',p)
        if shape in shapes and shapes[shape]!=p:raise ValueError('Ambiguous templated routes')
        shapes[shape]=p;seen.add((p,m));ids.add(i)
        literal(e['summary'],300)
        fields(e['request']);fields(e['response'])
        if m in ('get','delete') and e['request']:raise ValueError('No request body for GET or DELETE')
        if type(e['status']) is not int or e['status'] not in (200,201,202,204):raise ValueError('Choose explicit success status')
        if e['status']==204 and e['response']:raise ValueError('204 cannot contain a body')
    return s
def contract(s):
    checked(s);paths={}
    for e in s['endpoints']:
        response={'description':'Declared successful response'}
        if e['status']!=204:
            response['content']={'application/json':{'schema':fields(e['response'])}}
        operation={'operationId':e['id'],'summary':e['summary'],'responses':{str(e['status']):response}}
        params=re.findall(r'\{([^}]+)\}',e['path'])
        if params:operation['parameters']=[{'name':n,'in':'path','required':True,'schema':{'type':'string'}} for n in params]
        if e['request']:operation['requestBody']={'required':True,'content':{'application/json':{'schema':fields(e['request'])}}}
        paths.setdefault(e['path'],{})[e['method']]=operation
    return {'openapi':'3.1.0','info':{'title':s['title'],'version':s['version']},'paths':paths}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,scope='Generate an OpenAPI contract, not an implemented or running server.')
def execute(root,plan):
    s,dst,_=validate(root,plan);result=contract(s)
    payload=(json.dumps(result,ensure_ascii=True,allow_nan=False,indent=2)+'\n').encode()
    if json.loads(payload)!=result:raise ValueError('OpenAPI roundtrip mismatch')
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'api_contract_exported','output':plan['output'],'sha256':digest,
            'operations':len(s['endpoints']),'server_implemented':False,'server_started':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'API contract export unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
