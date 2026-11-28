"""Reviewed data-only game configuration override bundle, independent of game engine."""
from __future__ import annotations
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.structured_source import strict_json
from deepthort_local.source_security import excluded

SCHEMA='janus-game-config-mod-v1'
EXTRA=('asset','.json')
MAX_JSON=2_000_000
SAFE_SEGMENT=r'[A-Za-z0-9_][A-Za-z0-9_. -]{0,79}'
RESERVED={'con','prn','aux','nul',*(f'com{i}' for i in range(1,10)),*(f'lpt{i}' for i in range(1,10))}

def scalar(v):
    return (type(v) is bool or (type(v) is int and abs(v)<=2**53-1)
            or (type(v) is str and len(v)<=512 and all(ord(c)>=32 for c in v)))

def same(a,b):
    return type(a) is type(b) and a==b

def checked(s):
    if not isinstance(s,dict) or set(s)!={'asset','mod_id','edits'}:
        raise ValueError('Expected asset, mod_id and edits')
    asset=s['asset']
    if (not isinstance(asset,str) or not asset.endswith('.json') or len(asset)>220
        or excluded(asset,set()) or any(not re.fullmatch(SAFE_SEGMENT,p) or p.endswith((' ','.'))
            or p.split('.')[0].casefold() in RESERVED for p in asset.split('/'))):
        raise ValueError('Choose a safe project-relative JSON data asset')
    if not isinstance(s['mod_id'],str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}',s['mod_id']):
        raise ValueError('Choose a bounded lowercase mod identifier')
    edits=s['edits'];seen=set()
    if not isinstance(edits,list) or not 1<=len(edits)<=32:raise ValueError('Choose 1–32 edits')
    for e in edits:
        if not isinstance(e,dict) or set(e)!={'path','expected','value'}:
            raise ValueError('Expected explicit path and old/new values')
        path=e['path']
        if (not isinstance(path,list) or not 1<=len(path)<=12
            or any(not ((type(p) is str and 1<=len(p)<=128 and all(ord(c)>=32 for c in p))
                        or (type(p) is int and 0<=p<=10000)) for p in path)):
            raise ValueError('Choose literal object keys or array indices')
        if tuple(path) in seen:raise ValueError('Repeated edit path')
        seen.add(tuple(path))
        if not scalar(e['expected']) or not scalar(e['value']) or type(e['expected']) is not type(e['value']) or same(e['expected'],e['value']):
            raise ValueError('Only changed, same-type bounded integer, Boolean or string scalars allowed')
    return s

def locate(tree,path):
    node=tree
    for p in path[:-1]:
        if type(p) is str and isinstance(node,dict) and p in node:node=node[p]
        elif type(p) is int and isinstance(node,list) and p<len(node):node=node[p]
        else:raise ValueError('Missing or wrong-type intermediate selector')
    key=path[-1]
    if type(key) is str and isinstance(node,dict) and key in node:return node,key
    if type(key) is int and isinstance(node,list) and key<len(node):return node,key
    raise ValueError('Existing scalar target required')

def apply(tree,edits):
    targets=[]
    for e in edits:
        node,key=locate(tree,e['path'])
        if not same(node[key],e['expected']):raise ValueError('Expected original value mismatch')
        targets.append((node,key,e['value']))
    for node,key,value in targets:node[key]=value
    return tree

def encode(data):
    return (json.dumps(data,ensure_ascii=True,indent=2,allow_nan=False)+'\n').encode()

def generate(raw,s):
    checked(s)
    if not isinstance(raw,bytes) or not 1<=len(raw)<=MAX_JSON:raise ValueError('Data asset exceeds bound')
    original=strict_json(raw.decode('utf-8-sig'))
    if not isinstance(original,(dict,list)):raise ValueError('Expected data object or array')
    modified=apply(copy.deepcopy(original),s['edits'])
    output=encode(modified)
    if len(output)>MAX_JSON:raise ValueError('Modified asset exceeds bound')
    # Verify serialized result by reversing only the authorized edits.
    restored=strict_json(output.decode())
    inverse=[{'path':e['path'],'expected':e['value'],'value':e['expected']} for e in s['edits']]
    if encode(apply(restored,inverse))!=encode(original):raise ValueError('Inverse semantic replay diverged')
    receipt={'schema':SCHEMA,'mod_id':s['mod_id'],'asset':s['asset'],
        'original_sha256':hashlib.sha256(raw).hexdigest(),'modified_sha256':hashlib.sha256(output).hexdigest(),
        'edits':s['edits'],'semantic_rollback_verified':True,'game_compatibility_verified':False,'installed':False}
    entries={'override/'+s['asset']:output,'janus-mod-receipt.json':encode(receipt)}
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(entries.items()):z.writestr(name,data)
    payload=buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or sorted(z.namelist())!=sorted(entries) or any(z.read(k)!=v for k,v in entries.items()):
            raise ValueError('Override bundle verification failed')
    return payload,receipt

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
    _,_,src=validate(root,plan)
    _,receipt=generate(guard.exact(src,plan['guards'][1],MAX_JSON),s)
    return plan,dict(s,observations=receipt,scope='Data-only override archive for the exact local JSON asset. Existing scalar values only; preserve other data, verify semantic inverse and archive. No installation, code execution, game-specific loader or compatibility claim.')

def execute(root,plan):
    s,dst,src=validate(root,plan)
    payload,receipt=generate(guard.exact(src,plan['guards'][1],MAX_JSON),s)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'game_data_override_prepared','output':plan['output'],'sha256':digest,'source_unchanged':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed game data override could not be verified'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
