"""Exact bounded rational arithmetic and verified one-variable linear equations."""
from __future__ import annotations
import argparse
from fractions import Fraction
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard

SCHEMA='janus-mathematics-v1'
NUMBER=re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]+)?|[0-9]+/[1-9][0-9]*)\Z')
def number(text):
    if not isinstance(text,str) or len(text)>80 or not NUMBER.fullmatch(text):
        raise ValueError('Use exact integer, decimal or fraction strings')
    return bounded(Fraction(text))
def bounded(n):
    if n.numerator.bit_length()>2048 or n.denominator.bit_length()>2048:
        raise ValueError('Rational result exceeds bit budget')
    return n
def form(node,trace,depth=0):
    if depth>16 or len(trace)>=512 or not isinstance(node,dict):
        raise ValueError('Expression exceeds structural budget')
    if set(node)=={'number'}:a,b=Fraction(0),number(node['number'])
    elif node=={'variable':'x'}:a,b=Fraction(1),Fraction(0)
    elif set(node)=={'op','args'} and node['op'] in ('add','subtract','multiply','divide'):
        args=node['args']
        if not isinstance(args,list) or len(args)!=2:raise ValueError('Binary operation requires two arguments')
        c,d=form(args[0],trace,depth+1);e,f=form(args[1],trace,depth+1)
        if node['op']=='add':a,b=c+e,d+f
        elif node['op']=='subtract':a,b=c-e,d-f
        elif node['op']=='multiply':
            if c and e:raise ValueError('Nonlinear multiplication unsupported')
            a,b=c*f+e*d,d*f
        else:
            if e or not f:raise ValueError('Division by zero or variable denominator')
            a,b=c/f,d/f
    else:raise ValueError('Unsupported typed expression')
    a,b=bounded(a),bounded(b)
    if len(trace)>=512:raise ValueError('Expression exceeds node budget')
    trace.append({'coefficient':str(a),'constant':str(b)})
    return a,b
def direct(node,x):
    if 'number' in node:return number(node['number'])
    if 'variable' in node:return x
    a,b=(direct(n,x) for n in node['args'])
    op=node['op']
    return bounded(a+b if op=='add' else a-b if op=='subtract' else a*b if op=='multiply' else a/b)
def calculate(spec):
    if not isinstance(spec,dict):raise ValueError('Expected typed math request')
    trace=[]
    if set(spec)=={'expression'}:
        a,b=form(spec['expression'],trace)
        if a or direct(spec['expression'],Fraction(0))!=b:raise ValueError('Expected constant expression')
        # A cancelled variable is still not a valid constant-only arithmetic request.
        if '"variable"' in json.dumps(spec):raise ValueError('Use equation mode for variables')
        return {'kind':'exact_arithmetic','result':str(b),'steps':trace,'verified':True}
    if set(spec)!={'left','right'}:raise ValueError('Expected expression or left/right equation')
    a,b=form(spec['left'],trace);c,d=form(spec['right'],trace)
    slope=bounded(a-c);constant=bounded(d-b)
    if not slope:
        return {'kind':'linear_equation','solution':'all_rationals' if not constant else 'none',
                'coefficient':str(slope),'constant':str(constant),'steps':trace,'verified':True}
    x=bounded(constant/slope)
    l=direct(spec['left'],x);r=direct(spec['right'],x)
    if l!=r:raise ValueError('Independent substitution failed')
    return {'kind':'linear_equation','solution':str(x),'left_at_solution':str(l),'right_at_solution':str(r),
            'coefficient':str(slope),'constant':str(constant),'steps':trace,'verified':True}
def checked(spec):
    calculate(spec);return spec
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(spec,exact_result=calculate(spec))
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def execute(root,plan):
    spec,dst,_=validate(root,plan);result=calculate(spec)
    payload=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-mathematics-result-v1','status':'exact_result_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,'kind':result['kind']}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid or unsupported bounded mathematical expression'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
