"""Bounded exact scientific computations: square systems and polynomial integrals."""
from __future__ import annotations
import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.mathematics import number,bounded
from deepthort_local.statistical_analysis import dec
from deepthort_local.pdf_diagrams import limits
SCHEMA='janus-scientific-computing-v1'
def exact(v):return {'exact':str(bounded(v)),'decimal_24_digits':dec(v)}
def checked(s):
    if not isinstance(s,dict):raise ValueError('Expected typed scientific calculation')
    if s.get('operation')=='solve_linear_system':
        if set(s)!={'operation','matrix','rhs'}:raise ValueError('Expected matrix and right hand side')
        a=s['matrix'];b=s['rhs']
        if not isinstance(a,list) or not 1<=len(a)<=16 or not isinstance(b,list) or len(b)!=len(a):
            raise ValueError('Choose 1–16 square equations')
        if any(not isinstance(row,list) or len(row)!=len(a) for row in a):raise ValueError('Expected square matrix')
        for row in a:
            for v in row:number(v)
        for v in b:number(v)
    elif s.get('operation')=='integrate_polynomial':
        if set(s)!={'operation','coefficients','lower','upper'}:raise ValueError('Expected coefficients and limits')
        c=s['coefficients']
        if not isinstance(c,list) or not 1<=len(c)<=32:raise ValueError('Choose 1–32 ascending-power coefficients')
        for v in c:number(v)
        number(s['lower']);number(s['upper'])
    else:raise ValueError('Unsupported scientific operation')
    return s
def solve(s):
    a=[[number(v) for v in row] for row in s['matrix']];b=[number(v) for v in s['rhs']];n=len(a)
    m=[row+[v] for row,v in zip(a,b)];pivot_columns=[]
    for col in range(n):
        rank=len(pivot_columns)
        pivot=next((i for i in range(rank,n) if m[i][col]),None)
        if pivot is None:continue
        m[rank],m[pivot]=m[pivot],m[rank]
        p=m[rank][col];m[rank]=[bounded(v/p) for v in m[rank]]
        for i in range(n):
            if i==rank:continue
            f=m[i][col]
            if f:m[i]=[bounded(x-f*y) for x,y in zip(m[i],m[rank])]
        pivot_columns.append(col)
    rank=len(pivot_columns)
    if any(not any(row[:-1]) and row[-1] for row in m):
        return {'operation':'solve_linear_system','status':'inconsistent','rank':rank,'solution':None,'substitution_verified':False}
    if rank<n:
        return {'operation':'solve_linear_system','status':'non_unique','rank':rank,'solution':None,'substitution_verified':False}
    x=[m[i][-1] for i in range(n)]
    residual=[bounded(sum((v*z for v,z in zip(row,x)),Fraction(0))-y) for row,y in zip(a,b)]
    if any(residual):raise ValueError('Independent exact substitution failed')
    return {'operation':'solve_linear_system','status':'unique','rank':rank,'solution':[exact(v) for v in x],
            'residuals':[str(v) for v in residual],'substitution_verified':True}
def polynomial_integral(s):
    c=[number(v) for v in s['coefficients']];a=number(s['lower']);b=number(s['upper'])
    antiderivative=[Fraction(0)]+[bounded(v/(i+1)) for i,v in enumerate(c)]
    def horner(coefficients,x):
        result=Fraction(0)
        for v in reversed(coefficients):result=bounded(result*x+v)
        return result
    result=bounded(horner(antiderivative,b)-horner(antiderivative,a))
    # Independent direct monomial evaluation, including signed bounds.
    alternate=Fraction(0)
    for i,v in enumerate(c,1):
        alternate=bounded(alternate+bounded(v*bounded(b**i-a**i)/i))
    if result!=alternate or [bounded(i*v) for i,v in enumerate(antiderivative)][1:]!=c:
        raise ValueError('Independent integral evaluation or derivative failed')
    return {'operation':'integrate_polynomial','status':'exact','integral':exact(result),
            'antiderivative_coefficients':[exact(v) for v in antiderivative],
            'independent_evaluation_verified':True}
def calculate(s):
    checked(s)
    return {'schema':'janus-scientific-computation-result-v1',**(solve(s) if s['operation']=='solve_linear_system' else polynomial_integral(s)),
            'scope':'Exact rational arithmetic on explicitly typed bounded inputs. No physical model or experimental claim.'}
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def review(root,source,output,exclude=()):
    return guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
def execute(root,plan):
    s,dst,_=validate(root,plan);r=calculate(s)
    payload=json.dumps(r,ensure_ascii=True,allow_nan=False,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'scientific_calculation_completed','output':plan['output'],'sha256':digest,
            'operation':r['operation'],'result_status':r['status']}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        limits();print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Scientific computation exceeds scope or input bounds'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
