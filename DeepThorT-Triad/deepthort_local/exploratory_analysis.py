"""Bounded exploratory CSV profiles with declared types and pairwise correlations."""
from __future__ import annotations
import argparse
from collections import Counter
from decimal import Decimal,localcontext
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.csv_processing import parse,DELIMITERS
from deepthort_local.data_transformation import numeric
from deepthort_local.long_form_writing import literal
from deepthort_local.statistical_analysis import summary

SCHEMA='janus-exploratory-analysis-v1'
EXTRA=('csv','.csv')
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'csv','delimiter','numeric_columns','categorical_columns','missing_tokens','top_categories','correlations'}:
        raise ValueError('Expected explicit column types, missing tokens and profiling options')
    if not isinstance(spec['csv'],str) or not isinstance(spec['delimiter'],str) or spec['delimiter'] not in DELIMITERS:
        raise ValueError('Unsupported CSV or delimiter')
    nums=spec['numeric_columns'];cats=spec['categorical_columns'];tokens=spec['missing_tokens']
    if not isinstance(nums,list) or not isinstance(cats,list) or not 1<=len(nums)+len(cats)<=24 or len(nums)>8:
        raise ValueError('Select up to 24 columns including at most 8 numeric')
    for c in nums+cats:literal(c,200)
    if len(set(nums+cats))!=len(nums)+len(cats):raise ValueError('Columns must be distinct')
    if (not isinstance(tokens,list) or len(tokens)>20 or any(not isinstance(t,str) or len(t)>100 for t in tokens)
        or len(set(tokens))!=len(tokens)):raise ValueError('Invalid missing tokens')
    if type(spec['top_categories']) is not int or not 1<=spec['top_categories']<=30 or type(spec['correlations']) is not bool:
        raise ValueError('Invalid profiling options')
    return spec

def correlate(xs,ys):
    pairs=[(x,y) for x,y in zip(xs,ys) if x is not None and y is not None]
    n=len(pairs);r={'paired_count':n,'omitted_count':len(xs)-n,'pearson_decimal':None,'reason':None}
    if n<2:r['reason']='insufficient_pairs';return r
    sx=sum((x for x,y in pairs),Fraction(0));sy=sum((y for x,y in pairs),Fraction(0))
    xx=n*sum((x*x for x,y in pairs),Fraction(0))-sx*sx
    yy=n*sum((y*y for x,y in pairs),Fraction(0))-sy*sy
    xy=n*sum((x*y for x,y in pairs),Fraction(0))-sx*sy
    if not xx or not yy:r['reason']='constant_column';return r
    if xy*xy>xx*yy:raise ValueError('Correlation invariant failed')
    with localcontext() as ctx:
        ctx.prec=24
        def d(x):return Decimal(x.numerator)/Decimal(x.denominator)
        value=d(xy)/(d(xx)*d(yy)).sqrt()
        r['pearson_decimal']=str(max(Decimal(-1),min(Decimal(1),value)))
    return r

def analyse(raw,spec):
    header,rows=parse(raw,spec['delimiter']);tokens=set(spec['missing_tokens'])
    selected=spec['numeric_columns']+spec['categorical_columns']
    if any(c not in header for c in selected):raise ValueError('Selected column missing')
    if len(rows)>10000:raise ValueError('Profiling limited to 10,000 rows')
    out={};arrays={};total=len(rows)
    for c in selected:
        i=header.index(c);raw_values=[row[i] for row in rows]
        vals=[v for v in raw_values if v not in tokens];missing=total-len(vals)
        counts=Counter(vals)
        item={'count':len(vals),'missing':missing,'distinct':len(counts),'total':total}
        if c in spec['numeric_columns']:
            array=[None if v in tokens else Fraction(numeric(v)) for v in raw_values];arrays[c]=array
            nums=[v for v in array if v is not None]
            stats=summary(nums,missing,'sample');item.update(type='numeric',statistics=stats,numeric_distinct=len(set(nums)))
            if nums:
                q1=Fraction(stats['q1']['exact']);q3=Fraction(stats['q3']['exact'])
                iqr=q3-q1;lo=q1-Fraction(3,2)*iqr;hi=q3+Fraction(3,2)*iqr
                item['iqr_flags']={'lower_exact':str(lo),'upper_exact':str(hi),'below':sum(v<lo for v in nums),'above':sum(v>hi for v in nums)}
            else:item['iqr_flags']=None
        else:
            top=sorted(counts.items(),key=lambda pair:(-pair[1],pair[0]))[:spec['top_categories']]
            # Full category strings are data, bounded by the shared CSV parser.
            if any(len(v)>500 for v,n in top):raise ValueError('Category label exceeds reporting bound')
            item.update(type='categorical',top=[{'value':v,'count':n} for v,n in top],other_count=len(vals)-sum(n for v,n in top))
        if item['count']+item['missing']!=total:raise ValueError('Profile count reconciliation failed')
        out[c]=item
    corr=[]
    if spec['correlations']:
        for a,b in combinations(spec['numeric_columns'],2):
            corr.append({'left':a,'right':b,**correlate(arrays[a],arrays[b])})
    duplicate_count=total-len({tuple(r) for r in rows})
    return {'schema':'janus-exploratory-report-v1','source_sha256':hashlib.sha256(raw).hexdigest(),'rows':total,
            'source_columns':len(header),'duplicate_full_rows_after_first':duplicate_count,'columns':out,'correlations':corr,
            'missing_tokens':spec['missing_tokens'],'methods':{'quantiles':'linear at (n-1)*p','variance':'sample',
            'outliers':'1.5 IQR flags; not automatic removal','correlations':'pairwise complete Pearson; decimal precision 24',
            'categorical_order':'frequency descending then literal value','duplicates':'exact full-row strings'},
            'scope':'Exploratory descriptions only; no imputation, causal or inferential claims.'}

def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    _,_,path=validate(root,plan);report=analyse(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    return plan,dict(spec,exact_report=report)
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);report=analyse(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    payload=(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
    if json.loads(payload)!=report:raise ValueError('Profile roundtrip failed')
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-exploratory-result-v1','status':'profile_verified','output':plan['output'],'sha256':sha,
            'rows':report['rows'],'columns':len(report['columns']),'correlations':len(report['correlations']),'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Exploratory analysis unavailable; inspect types, missing tokens and data bounds'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
