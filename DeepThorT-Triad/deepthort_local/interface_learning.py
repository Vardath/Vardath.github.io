"""Learn documented HTTP interfaces from an exact local OpenAPI JSON contract."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.structured_source import strict_json
SCHEMA='janus-interface-learning-v1'
EXTRA=('document','.json')
MAX_SOURCE=512*1024
METHODS=('get','put','post','delete','patch','head','options','trace')
def checked(s):
    if not isinstance(s,dict) or set(s)!={'document'} or not isinstance(s['document'],str):
        raise ValueError('Expected reviewed OpenAPI JSON file')
    return s
def pointer(*parts):return '/'+ '/'.join(str(p).replace('~','~0').replace('/','~1') for p in parts)
def text(v,limit=500):
    if not isinstance(v,str) or len(v)>limit or any(ord(c)<32 or 0xd800<=ord(c)<=0xdfff for c in v):raise ValueError('Invalid bounded interface text')
    return v
def schema_fields(schema):
    if not isinstance(schema,dict):return {'supported':False}
    if '$ref' in schema or any(k in schema for k in ('oneOf','allOf','anyOf','not')):return {'supported':False}
    if schema.get('type')!='object':return {'supported':False}
    props=schema.get('properties',{});required=schema.get('required',[])
    if not isinstance(props,dict) or len(props)>64 or not isinstance(required,list) or any(not isinstance(v,str) or v not in props for v in required):
        raise ValueError('Invalid documented object fields')
    fields=[]
    for k,v in props.items():
        text(k,128)
        typ=v.get('type') if isinstance(v,dict) and '$ref' not in v else None
        fields.append({'name':k,'required':k in required,'type':typ if typ in ('string','integer','number','boolean','array','object','null') else None})
    return {'supported':True,'fields':fields,'additional_properties_forbidden':schema.get('additionalProperties') is False}
def body(obj):
    if not isinstance(obj,dict) or '$ref' in obj:return {'supported':False}
    content=obj.get('content',{})
    if not isinstance(content,dict):raise ValueError('Invalid content')
    if 'application/json' not in content:return {'supported':False}
    item=content['application/json']
    return schema_fields(item.get('schema')) if isinstance(item,dict) else {'supported':False}
def parameters(items):
    if not isinstance(items,list) or len(items)>64:raise ValueError('Invalid parameters')
    out=[];keys=set();unresolved=0
    for p in items:
        if not isinstance(p,dict):raise ValueError('Invalid parameter')
        if '$ref' in p:unresolved+=1;continue
        key=(text(p.get('in'),32),text(p.get('name'),128))
        if key in keys or key[0] not in ('query','path','header','cookie'):raise ValueError('Duplicate or invalid parameter')
        keys.add(key);required=p.get('required',False)
        if type(required) is not bool or key[0]=='path' and not required:raise ValueError('Invalid parameter requirement')
        out.append({'in':key[0],'name':key[1],'required':required})
    return out,unresolved
def analyze(raw):
    if not raw or len(raw)>MAX_SOURCE:raise ValueError('Contract exceeds limit')
    doc=strict_json(raw.decode('utf-8-sig'))
    if not isinstance(doc,dict) or not isinstance(doc.get('openapi'),str) or not re.fullmatch(r'3\.[01]\.[0-9]+',doc['openapi']):
        raise ValueError('Expected OpenAPI 3.0 or 3.1')
    paths=doc.get('paths');info=doc.get('info')
    if not isinstance(paths,dict) or not 1<=len(paths)<=64 or not isinstance(info,dict):raise ValueError('Unsupported contract')
    result=[]
    for path,item in paths.items():
        text(path,300)
        if not path.startswith('/') or path.startswith('//') or not isinstance(item,dict) or '$ref' in item:raise ValueError('Unsupported path item')
        common,unresolved=parameters(item.get('parameters',[]))
        for method in METHODS:
            if method not in item:continue
            op=item[method]
            if not isinstance(op,dict):raise ValueError('Invalid operation')
            if len(result)>=128:raise ValueError('Too many operations')
            local,missing=parameters(op.get('parameters',[]));by={(p['in'],p['name']):p for p in common}
            by.update({(p['in'],p['name']):p for p in local})
            responses=op.get('responses')
            if not isinstance(responses,dict) or not 1<=len(responses)<=32:raise ValueError('Invalid responses')
            response=[]
            for code,entry in responses.items():
                if not re.fullmatch(r'[1-5][0-9]{2}|[1-5]XX|default',code):raise ValueError('Invalid response status')
                response.append({'status':code,'json':body(entry),'pointer':pointer('paths',path,method,'responses',code)})
            request=op.get('requestBody')
            req=None if request is None else {'required':request.get('required',False) if isinstance(request,dict) else None,
                'json':body(request),'pointer':pointer('paths',path,method,'requestBody')}
            result.append({'method':method.upper(),'path':path,'operation_id':text(op.get('operationId',''),128),
                'summary':text(op.get('summary','')),'pointer':pointer('paths',path,method),
                'parameters':list(by.values()),'unresolved_parameter_refs':unresolved+missing,'request':req,'responses':response,
                'security_declared':bool(op.get('security',doc.get('security',[])))})
    if not result:raise ValueError('No supported documented operations')
    return {'schema':'janus-learned-http-interface-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
        'title':text(info.get('title'),200),'version':text(info.get('version'),80),'openapi_version':doc['openapi'],
        'operations':result,'scope':'Documented interface evidence only, exact JSON pointers. No reference resolution, network, credential extraction or calls. No operational verification or authority to execute.'}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    _,_,doc=validate(root,plan)
    if doc.stat().st_size>MAX_SOURCE:raise ValueError('Contract exceeds limit')
    return plan,dict(s,scope='Learn declared interface metadata from local JSON only.')
def execute(root,plan):
    s,dst,doc=validate(root,plan);r=analyze(guard.exact(doc,plan['guards'][1],MAX_SOURCE))
    digest=guard.publish(json.dumps(r,ensure_ascii=True,allow_nan=False,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'status':'documented_interface_learned','output':plan['output'],'sha256':digest,'operations':len(r['operations']),'runtime_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Interface learning unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
