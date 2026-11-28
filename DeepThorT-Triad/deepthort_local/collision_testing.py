"""Exact continuous 2D axis-aligned rectangle collision fixture testing."""
from __future__ import annotations
import argparse
from fractions import Fraction
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard

SCHEMA='janus-swept-aabb-tests-v1'
LIMIT=1000000

def vector(v,n):
    if not isinstance(v,list) or len(v)!=n or any(type(x) is not int or abs(x)>LIMIT for x in v):
        raise ValueError('Invalid integer geometry')
    return v

def box(v):
    x,y,w,h=vector(v,4)
    if w<=0 or h<=0:raise ValueError('Rectangle dimensions must be positive')
    return x,y,w,h

def name(v):
    if not isinstance(v,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,39}',v):
        raise ValueError('Invalid fixture identifier')
    return v

def checked(s):
    if not isinstance(s,dict) or set(s)!={'obstacles','cases'}:
        raise ValueError('Expected obstacles and collision cases')
    obstacles,cases=s['obstacles'],s['cases']
    if not isinstance(obstacles,list) or not 1<=len(obstacles)<=64 or not isinstance(cases,list) or not 1<=len(cases)<=64:
        raise ValueError('Collision fixtures exceed bounds')
    ids=set()
    for o in obstacles:
        if not isinstance(o,dict) or set(o)!={'id','rect'}:raise ValueError('Invalid obstacle')
        ident=name(o['id']);box(o['rect'])
        if ident in ids:raise ValueError('Duplicate obstacle')
        ids.add(ident)
    seen=set()
    for c in cases:
        if not isinstance(c,dict) or set(c)!={'id','rect','delta','expected_first'}:raise ValueError('Invalid case')
        ident=name(c['id']);box(c['rect']);vector(c['delta'],2)
        expected=c['expected_first']
        if not isinstance(expected,list) or any(not isinstance(i,str) or i not in ids for i in expected) or len(set(expected))!=len(expected):
            raise ValueError('Invalid expected first-contact identifiers')
        if ident in seen:raise ValueError('Duplicate case')
        seen.add(ident)
    return s

def contact(moving,delta,static):
    """Closed rectangles: boundary contact counts, even at t=0 or t=1.
    Calculate the exact intersection of the two time slabs in [0,1].
    Return None or the first rational contact time.
    """
    x,y,w,h=box(moving);a,b,c,d=box(static);dx,dy=vector(delta,2)
    enter,leave=Fraction(0),Fraction(1)
    for lo,hi,slo,shi,v in ((x,x+w,a,a+c,dx),(y,y+h,b,b+d,dy)):
        if v==0:
            if hi<slo or lo>shi:return None
            continue
        t1=Fraction(slo-hi,v);t2=Fraction(shi-lo,v)
        enter=max(enter,min(t1,t2));leave=min(leave,max(t1,t2))
        if enter>leave:return None
    return enter

def ratio(t):return [t.numerator,t.denominator]

def generate(s):
    checked(s);results=[]
    for case in s['cases']:
        hits=[]
        for obstacle in s['obstacles']:
            t=contact(case['rect'],case['delta'],obstacle['rect'])
            if t is not None:hits.append((t,obstacle['id']))
        hits.sort()
        first=[ident for t,ident in hits if t==hits[0][0]] if hits else []
        passed=first==sorted(case['expected_first'])
        results.append({'id':case['id'],'expected_first':sorted(case['expected_first']),
                        'observed_first':first,'first_contact':ratio(hits[0][0]) if hits else None,
                        'contacts':[{'id':ident,'time':ratio(t)} for t,ident in hits],
                        'passed':passed})
    count=sum(r['passed'] for r in results)
    report={'schema':SCHEMA,'contact_policy':'closed_aabb_including_initial_and_endpoint_touch',
            'cases':results,'passed':count,'failed':len(results)-count,'native_engine_verified':False}
    payload=(json.dumps(report,sort_keys=True,indent=2)+'\n').encode('utf-8')
    if json.loads(payload)!=report:raise ValueError('Collision report roundtrip failed')
    return payload,{'cases':len(results),'passed':count,'failed':len(results)-count,
                    'all_cases_passed':count==len(results),'native_engine_verified':False}

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    _,r=generate(s)
    return plan,{'observations':r,'scope':'Exact linear swept AABB fixture tests with closed boundaries; no game engine execution. Mismatched expectations are reported as failed cases.'}
def execute(root,plan):
    s,dst,_=validate(root,plan);payload,r=generate(s);sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-swept-aabb-result-v1','status':'collision_report_generated','output':plan['output'],
            'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        result=execute(a.root,json.loads(a.plan))
        print(json.dumps(result,sort_keys=True),flush=True)
        return 0 if result['all_cases_passed'] else 1
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed collision fixture or publication failure'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
