"""Reviewed descriptive statistics with exact fractions and explicit missingness."""
from __future__ import annotations
import argparse
from decimal import Decimal,localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.csv_processing import parse,DELIMITERS
from deepthort_local.data_transformation import numeric
from deepthort_local.long_form_writing import literal

SCHEMA='janus-statistics-v1'
EXTRA=('csv','.csv')
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'csv','delimiter','columns','missing_tokens','variance'}:
        raise ValueError('Expected CSV, columns, missing tokens and variance convention')
    if not isinstance(spec['csv'],str) or not isinstance(spec['delimiter'],str) or spec['delimiter'] not in DELIMITERS or spec['variance'] not in ('sample','population'):
        raise ValueError('Invalid delimiter or variance convention')
    cols=spec['columns'];tokens=spec['missing_tokens']
    if not isinstance(cols,list) or not 1<=len(cols)<=20:raise ValueError('Select 1–20 numeric columns')
    for c in cols:literal(c,200)
    if len(set(cols))!=len(cols):raise ValueError('Repeated column')
    if (not isinstance(tokens,list) or len(tokens)>20 or any(not isinstance(t,str) or len(t)>100 for t in tokens)
        or len(set(tokens))!=len(tokens)):raise ValueError('Invalid exact missing tokens')
    return spec

def quantile(sorted_values,p):
    position=(len(sorted_values)-1)*p
    index=position.numerator//position.denominator
    f=position-index
    return sorted_values[index] if not f else sorted_values[index]+f*(sorted_values[index+1]-sorted_values[index])

def dec(n):
    if n is None:return None
    with localcontext() as ctx:
        ctx.prec=24
        return str(Decimal(n.numerator)/Decimal(n.denominator))

def summary(values,missing,variance):
    n=len(values)
    result={'count':n,'missing':missing,'total':n+missing,'variance_convention':variance}
    names=('minimum','maximum','sum','mean','median','q1','q3','variance')
    if not n:
        result.update({k:None for k in names});result['standard_deviation_decimal']=None;return result
    values=sorted(values);s=sum(values,Fraction(0));mean=s/n
    denom=n-1 if variance=='sample' else n
    var=sum(((v-mean)**2 for v in values),Fraction(0))/denom if denom else None
    exact=[values[0],values[-1],s,mean,quantile(values,Fraction(1,2)),quantile(values,Fraction(1,4)),quantile(values,Fraction(3,4)),var]
    for name,v in zip(names,exact):result[name]=None if v is None else {'exact':str(v),'decimal_24_digits':dec(v)}
    with localcontext() as ctx:
        ctx.prec=24
        result['standard_deviation_decimal']=None if var is None else str((Decimal(var.numerator)/Decimal(var.denominator)).sqrt())
    return result

def analyse(raw,spec):
    header,rows=parse(raw,spec['delimiter']);tokens=set(spec['missing_tokens']);out={}
    for c in spec['columns']:
        if c not in header:raise ValueError('Selected column missing: '+c)
        i=header.index(c);values=[];missing=0
        for row in rows:
            value=row[i]
            if value in tokens:missing+=1
            else:values.append(Fraction(numeric(value)))
        report=summary(values,missing,spec['variance'])
        if report['total']!=len(rows):raise ValueError('Count reconciliation failed')
        out[c]=report
    return {'schema':'janus-statistics-report-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'rows':len(rows),'columns':out,'missing_tokens':spec['missing_tokens'],
            'quantile_method':'linear interpolation at (n-1)*p','decimal_precision':24,
            'scope':'Descriptive numeric statistics; no inference, imputation or causal claims.'}

def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    _,_,path=validate(root,plan);report=analyse(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    return plan,dict(spec,exact_report=report)
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);raw=guard.exact(path,plan['guards'][1],guard.MAX_INPUT)
    result=analyse(raw,spec);payload=(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
    if json.loads(payload)!=result:raise ValueError('Report roundtrip failed')
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-statistics-result-v1','status':'descriptive_statistics_verified','output':plan['output'],'sha256':sha,'rows':result['rows'],'columns':len(result['columns']),'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Statistics unavailable; inspect exact numeric data and missing tokens'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
