"""Prepare literal values for exact static form controls; no live fill or submission."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlencode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.structured_source import strict_json
from deepthort_local.website_control_selection import selected,LOCATOR
from deepthort_local.website_crawling import safe_path
from deepthort_local.website_monitor import checked_url
from deepthort_local.rest_api import key

SCHEMA='janus-static-form-completion-v1'
EXTRA=('inspection','.json')
TYPES={'text','number','date','url','tel','email','search',None}
MAX_FIELDS=24
def locator(x):
    if not isinstance(x,str) or len(x)>2000 or not LOCATOR.fullmatch(x):
        raise ValueError('Invalid static form control locator')
    return x

def checked(s):
    if not isinstance(s,dict) or set(s)!={'inspection','form_locator','path_prefix','fields'}:
        raise ValueError('Expected inspection, exact form and explicit field values')
    if not isinstance(s['inspection'],str):raise ValueError('Invalid inspection path')
    locator(s['form_locator'])
    if not safe_path(s['path_prefix']).endswith('/'):raise ValueError('Explicit directory prefix required')
    if not isinstance(s['fields'],list) or not 1<=len(s['fields'])<=MAX_FIELDS:raise ValueError('Invalid field count')
    seen=set()
    for f in s['fields']:
        if not isinstance(f,dict) or set(f)!={'locator','name','value'}:raise ValueError('Expected exact literal field')
        loc=locator(f['locator']);name=key(f['name'])
        if loc in seen or not loc.startswith(s['form_locator']+'/'):raise ValueError('Duplicate or foreign field')
        seen.add(loc)
        v=f['value']
        if not isinstance(v,str) or len(v)>2000 or any(ord(c)<32 or 0xD800<=ord(c)<=0xDFFF for c in v):
            raise ValueError('Only bounded literal single-line values accepted')
    return s

def prepare(s,report):
    checked(s)
    spec={'inspection':s['inspection'],'locator':s['form_locator'],'tag':'form','action':'identify',
          'path_prefix':s['path_prefix'],'destination':None}
    form=selected(spec,report)
    if report.get('elements_truncated') is not False:raise ValueError('Truncated inspection cannot establish form controls')
    if form['control'].get('disabled_attribute') is not False:raise ValueError('Disabled form refused')
    prefix=s['form_locator']+'/'
    rows=report['elements']
    if any(row.get('tag')=='form' and row.get('locator','').startswith(prefix) for row in rows if isinstance(row,dict)):
        raise ValueError('Nested form refused')
    mapped=[];names=set()
    for f in s['fields']:
        candidates=[r for r in rows if isinstance(r,dict) and r.get('locator')==f['locator']]
        if len(candidates)!=1:raise ValueError('Exact field not uniquely observed')
        row=candidates[0]
        if (row.get('tag')!='input' or row.get('type') not in TYPES or row.get('disabled_attribute') is not False
            or row.get('name')!=f['name'] or f['name'] in names):
            raise ValueError('Unsupported, disabled, duplicate or mismatched form input')
        if row.get('required_attribute') is True and not f['value'].strip():raise ValueError('Required field is empty')
        names.add(f['name']);mapped.append(dict(f,type=row.get('type')))
    uncovered=[{'locator':r['locator'],'name':r.get('name',''),'type':r.get('type')}
               for r in rows if isinstance(r,dict) and r.get('locator','').startswith(prefix)
               and r.get('tag') in ('input','select','textarea') and r.get('required_attribute') is True
               and r.get('disabled_attribute') is False and r['locator'] not in {x['locator'] for x in mapped}]
    encoded=urlencode([(x['name'],x['value']) for x in mapped])
    if len(encoded)>32768:raise ValueError('Prepared form body exceeds bound')
    return {'schema':SCHEMA,'form':form,'fields':mapped,'required_controls_unmapped':uncovered,
            'urlencoded_preview':encoded,'source_historical':True,'browser_used':False,'form_filled_in_browser':False,
            'submitted':False,'validity_verified':False,
            'limitations':'Literal static preparation only. Hidden inputs, browser association, constraints, script state, action URL, credentials and live actionability not established. Never submit this preview automatically.'}

def read_review(root,plan):
    s,dst,src=guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    report=strict_json(guard.exact(src,plan['guards'][1],guard.MAX_INPUT).decode('utf-8-sig'))
    return s,dst,prepare(s,report)

def review(root,source,output,exclude=()):
    plan,_=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    _,_,preview=read_review(root,plan)
    return plan,preview

def execute(root,plan):
    _,dst,r=read_review(root,plan)
    data=json.dumps(r,ensure_ascii=True,sort_keys=True,indent=2).encode()
    sha=guard.publish(data,dst,lambda:read_review(root,plan))
    return {'schema':SCHEMA,'status':'static_form_values_prepared','output':plan['output'],'sha256':sha,
            'fields':len(r['fields']),'unmapped_required':len(r['required_controls_unmapped']),'submitted':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Review exact static form and field names'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
