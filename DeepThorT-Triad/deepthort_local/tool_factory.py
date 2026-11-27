"""Generate a reusable, inert Python JSON transformation tool from a reviewed contract."""
import argparse
import json
import math
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
SCHEMA='janus-tool-factory-v1'
NAME=re.compile(r'[A-Za-z_][A-Za-z0-9_]{0,63}\Z')
OPS=('copy','trim','lower','upper')

def reference(fields,record):
    if not isinstance(record,dict) or set(record)!={f['source'] for f in fields}:raise ValueError('Unexpected input fields')
    result={}
    for field in fields:
        v=record[field['source']];op=field['operation']
        if type(v) not in (str,int,float,bool,type(None)) or (type(v) is float and not math.isfinite(v)):
            raise ValueError('Only finite JSON scalar inputs supported')
        if isinstance(v,str) and (len(v)>4096 or any(0xd800<=ord(c)<=0xdfff for c in v)):raise ValueError('Invalid text')
        if op!='copy':
            if type(v) is not str:raise ValueError('Text operation requires string')
            v={'trim':str.strip,'lower':str.lower,'upper':str.upper}[op](v)
        result[field['target']]=v
    return result

def checked(s):
    if not isinstance(s,dict) or set(s)!={'name','fields','fixtures'} or not isinstance(s['name'],str) or not NAME.fullmatch(s['name']):raise ValueError('Expected tool name, field mapping and fixtures')
    fields=s['fields']
    if not isinstance(fields,list) or not 1<=len(fields)<=32:raise ValueError('Choose 1–32 fields')
    targets=set()
    for f in fields:
        if not isinstance(f,dict) or set(f)!={'source','target','operation'} or any(not isinstance(f[k],str) or not NAME.fullmatch(f[k]) for k in ('source','target')) or f['operation'] not in OPS or f['target'] in targets:
            raise ValueError('Invalid field mapping')
        targets.add(f['target'])
    fixtures=s['fixtures']
    if not isinstance(fixtures,list) or not 1<=len(fixtures)<=8:raise ValueError('Provide 1–8 exact fixtures')
    for f in fixtures:
        if not isinstance(f,dict) or set(f)!={'input','expected'}:raise ValueError('Invalid fixture')
        actual=reference(fields,f['input'])
        if json.dumps(actual,sort_keys=True,allow_nan=False)!=json.dumps(f['expected'],sort_keys=True,allow_nan=False):raise ValueError('Fixture disagrees with declared operations')
    return s

TEMPLATE="""import json
import math
import sys

def pairs(items):
    result = {}
    for k, v in items:
        if k in result:
            raise ValueError('Duplicate field')
        result[k] = v
    return result

def invalid_constant(value):
    raise ValueError('Nonfinite input')

def transform(record):
    if type(record) is not dict or set(record) != {source for source, _, _ in FIELDS}:
        raise ValueError('Unexpected input fields')
    output = {}
    for source, target, operation in FIELDS:
        value = record[source]
        if type(value) not in (str, int, float, bool, type(None)):
            raise ValueError('Expected scalar')
        if type(value) is float and not math.isfinite(value):
            raise ValueError('Nonfinite input')
        if type(value) is str and (len(value) > 4096 or any(0xd800 <= ord(c) <= 0xdfff for c in value)):
            raise ValueError('Invalid text')
        if operation != 'copy':
            if type(value) is not str:
                raise ValueError('Expected text')
            if operation == 'trim':
                value = value.strip()
            elif operation == 'lower':
                value = value.lower()
            elif operation == 'upper':
                value = value.upper()
        output[target] = value
    return output

def main():
    try:
        raw = sys.stdin.buffer.read(65537)
        if not raw or len(raw) > 65536:
            raise ValueError('Invalid input size')
        record = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=invalid_constant)
        print(json.dumps(transform(record), sort_keys=True, ensure_ascii=True, allow_nan=False))
        return 0
    except (ValueError, TypeError, RecursionError):
        print('Invalid tool input', file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
"""

def render(s):
    checked(s)
    fields=tuple((f['source'],f['target'],f['operation']) for f in s['fields'])
    text='# JANUS reviewed generated JSON tool: '+s['name']+'\nFIELDS = '+repr(fields)+'\n\n'+TEMPLATE
    compile(text,'<generated-tool>','exec')
    return text.encode('utf-8')

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.py')
    render(s)
    return plan,dict(s,scope='Generate standalone Python source; reference fixtures checked, generated code compiled only. No registration or execution authority.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.py')
def execute(root,plan):
    s,dst,_=validate(root,plan);payload=render(s)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'tool_source_generated','output':plan['output'],'sha256':digest,'reference_fixtures':len(s['fixtures']),'compiled':True,'executed':False,'registered':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Tool generation unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
