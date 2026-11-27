"""Exact regular-interval forecasts with chronological holdout and naive baseline."""
from __future__ import annotations
import argparse
from datetime import date,timedelta
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
from deepthort_local.predictive_modelling import mean,record
from deepthort_local.mathematics import bounded
from deepthort_local.pdf_diagrams import limits
SCHEMA='janus-time-series-forecast-v1'
EXTRA=('csv','.csv')
MAX_ROWS=10000
def checked(s):
    if not isinstance(s,dict) or set(s)!={'csv','delimiter','date_column','value_column','train_rows','horizon','season_length'}:
        raise ValueError('Expected dated numeric CSV, training prefix, horizon and seasonal period')
    if not isinstance(s['csv'],str) or not isinstance(s['delimiter'],str) or s['delimiter'] not in DELIMITERS:
        raise ValueError('Invalid source')
    for k in ('date_column','value_column'):literal(s[k],200)
    if s['date_column']==s['value_column']:raise ValueError('Choose distinct columns')
    for key,lo,hi in [('train_rows',4,MAX_ROWS-2),('horizon',1,100),('season_length',1,366)]:
        if type(s[key]) is not int or not lo<=s[key]<=hi:raise ValueError('Invalid '+key)
    if s['train_rows']<2*s['season_length']:raise ValueError('Need two complete training seasons')
    return s
def forecast(values,n,season,method):
    if method=='last_value':return [values[-1]]*n
    if method=='seasonal_naive':return [values[-season+i%season] for i in range(n)]
    drift=bounded((values[-1]-values[0])/(len(values)-1))
    return [bounded(values[-1]+drift*(i+1)) for i in range(n)]
def metrics(actual,predicted):
    errors=[bounded(a-b) for a,b in zip(actual,predicted)]
    return {'mae':record(mean(list(map(abs,errors)))),
            'mse':record(mean([bounded(x*x) for x in errors]))}
def analyze(raw,s):
    checked(s);header,rows=parse(raw,s['delimiter'])
    if not s['train_rows']+2<=len(rows)<=MAX_ROWS:raise ValueError('Need two held-out observations')
    di,vi=header.index(s['date_column']),header.index(s['value_column'])
    dates=[];values=[]
    for row in rows:
        d=date.fromisoformat(row[di])
        if d.isoformat()!=row[di]:raise ValueError('Use exact YYYY-MM-DD dates')
        dates.append(d);values.append(bounded(Fraction(numeric(row[vi]))))
    step=dates[1]-dates[0]
    if step.days<=0 or any(b-a!=step for a,b in zip(dates,dates[1:])):
        raise ValueError('Dates must be strictly increasing with constant day interval')
    train=values[:s['train_rows']];test=values[s['train_rows']:];season=s['season_length']
    methods=('last_value','seasonal_naive','drift')
    scores={}
    for method in methods:
        predicted=forecast(train,len(test),season,method)
        scores[method]=metrics(test,predicted)
    # This holdout compares candidates; it is not independent of selection.
    selected=min(methods,key=lambda m:(Fraction(scores[m]['mae']['exact']),methods.index(m)))
    future=forecast(values,s['horizon'],season,selected)
    return {'schema':'janus-time-series-forecast-result-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'training_rows':len(train),'holdout_rows':len(test),'interval_days':step.days,'season_length':season,
            'holdout_metrics':scores,'selected_by_holdout_mae':selected,'refit_using_all_observations':True,
            'forecasts':[{'date':(dates[-1]+step*(i+1)).isoformat(),'value':record(v)} for i,v in enumerate(future)],
            'independent_final_test':False,'uncertainty_intervals_provided':False,
            'scope':'Regular daily-multiple intervals, complete numeric values, fixed chronological candidate comparison. Holdout selects model; not independent final accuracy estimate. No future accuracy guarantee.'}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def review(root,source,output,exclude=()):return guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def execute(root,plan):
    s,dst,src=validate(root,plan);r=analyze(guard.exact(src,plan['guards'][1],guard.MAX_INPUT),s)
    digest=guard.publish(json.dumps(r,ensure_ascii=True,allow_nan=False,sort_keys=True,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'status':'chronological_forecast_evaluated','output':plan['output'],'sha256':digest,'selected':r['selected_by_holdout_mae'],'horizon':len(r['forecasts'])}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        limits();print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Forecast unavailable; inspect date interval, numeric completeness and split'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
