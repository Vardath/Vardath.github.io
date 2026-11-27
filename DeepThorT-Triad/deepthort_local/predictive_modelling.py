"""Exact one-predictor linear regression with explicit ordered held-out evaluation."""
from __future__ import annotations
import argparse
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
from deepthort_local.statistical_analysis import dec
from deepthort_local.mathematics import bounded
from deepthort_local.pdf_diagrams import limits
SCHEMA='janus-predictive-modelling-v1'
EXTRA=('csv','.csv')
MAX_ROWS=10000
def checked(s):
    if not isinstance(s,dict) or set(s)!={'csv','delimiter','predictor','target','train_rows','missing_tokens','predict_values'}:
        raise ValueError('Expected CSV, predictor, target, ordered training rows and prediction inputs')
    if not isinstance(s['csv'],str) or not isinstance(s['delimiter'],str) or s['delimiter'] not in DELIMITERS:
        raise ValueError('Invalid CSV or delimiter')
    for k in ('predictor','target'):literal(s[k],200)
    if s['predictor']==s['target']:raise ValueError('Distinct predictor and target required')
    if type(s['train_rows']) is not int or not 3<=s['train_rows']<=MAX_ROWS-2:
        raise ValueError('Choose explicit training prefix of at least three rows')
    tokens=s['missing_tokens']
    if not isinstance(tokens,list) or len(tokens)>20 or any(not isinstance(t,str) or len(t)>100 for t in tokens) or len(set(tokens))!=len(tokens):
        raise ValueError('Invalid missing tokens')
    if not isinstance(s['predict_values'],list) or len(s['predict_values'])>100:
        raise ValueError('At most 100 optional numeric prediction inputs')
    for value in s['predict_values']:
        if not isinstance(value,str):raise ValueError('Prediction inputs must be numeric strings')
        bounded(Fraction(numeric(value)))
    return s
def record(v):
    return None if v is None else {'exact':str(bounded(v)),'decimal_24_digits':dec(v)}
def mean(values):return bounded(sum(values,Fraction(0))/len(values))
def assess(pairs,slope,intercept,baseline):
    ymean=mean([y for x,y in pairs]);errors=[bounded(y-(intercept+slope*x)) for x,y in pairs]
    n=len(pairs);sse=bounded(sum((e*e for e in errors),Fraction(0)))
    total=bounded(sum(((y-ymean)**2 for x,y in pairs),Fraction(0)))
    baseline_mse=bounded(sum(((y-baseline)**2 for x,y in pairs),Fraction(0))/n)
    return {'count':n,'mean_absolute_error':record(sum(map(abs,errors),Fraction(0))/n),
            'mean_squared_error':record(sse/n),'r_squared':record(1-sse/total if total else None),
            'training_mean_baseline_mse':record(baseline_mse)}
def analyze(raw,s):
    checked(s);header,rows=parse(raw,s['delimiter'])
    if len(rows)>MAX_ROWS or len(rows)<s['train_rows']+2:
        raise ValueError('Need a held-out suffix of at least two rows')
    xi,yi=header.index(s['predictor']),header.index(s['target'])
    tokens=set(s['missing_tokens']);train=[];test=[];omitted=[0,0]
    for i,row in enumerate(rows):
        part=0 if i<s['train_rows'] else 1
        if row[xi] in tokens or row[yi] in tokens:omitted[part]+=1;continue
        pair=(bounded(Fraction(numeric(row[xi]))),bounded(Fraction(numeric(row[yi]))))
        (train if part==0 else test).append(pair)
    if len(train)<3 or len(test)<2:raise ValueError('Insufficient complete rows in either split')
    mx=mean([x for x,y in train]);my=mean([y for x,y in train])
    xx=bounded(sum(((x-mx)**2 for x,y in train),Fraction(0)))
    xy=bounded(sum(((x-mx)*(y-my) for x,y in train),Fraction(0)))
    if not xx:raise ValueError('Constant training predictor')
    slope=bounded(xy/xx);intercept=bounded(my-slope*mx)
    residuals=[(x,bounded(y-intercept-slope*x)) for x,y in train]
    if sum(e for x,e in residuals)!=0 or sum(x*e for x,e in residuals)!=0:
        raise ValueError('Exact normal-equation verification failed')
    lo=min(x for x,y in train);hi=max(x for x,y in train)
    predictions=[]
    for v in s['predict_values']:
        x=bounded(Fraction(numeric(v)))
        predictions.append({'input':v,'prediction':record(intercept+slope*x),'outside_training_range':not lo<=x<=hi})
    return {'schema':'janus-linear-prediction-result-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'method':'exact ordinary least squares with intercept; ordered holdout',
            'predictor':s['predictor'],'target':s['target'],'source_rows':len(rows),'train_rows':s['train_rows'],
            'train_missing_rows':omitted[0],'holdout_missing_rows':omitted[1],
            'coefficients':{'intercept':record(intercept),'slope':record(slope)},
            'training_predictor_range':[record(lo),record(hi)],
            'training_metrics':assess(train,slope,intercept,my),
            'holdout_metrics':assess(test,slope,intercept,my),'predictions':predictions,
            'holdout_outside_training_range':sum(not lo<=x<=hi for x,y in test),
            'normal_equations_verified':True,'generalisation_verified':False,
            'scope':'Single predictor linear model, complete cases, explicit row-order split. Holdout evidence is not proof of future accuracy, independence or causal effects.'}
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def review(root,source,output,exclude=()):
    return guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def execute(root,plan):
    s,dst,src=validate(root,plan);r=analyze(guard.exact(src,plan['guards'][1],guard.MAX_INPUT),s)
    payload=json.dumps(r,ensure_ascii=True,allow_nan=False,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'heldout_linear_model_evaluated','output':plan['output'],'sha256':digest,
            'training_rows':r['training_metrics']['count'],'holdout_rows':r['holdout_metrics']['count'],
            'generalisation_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        limits();print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Predictive model unavailable; inspect numeric inputs and training split'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
