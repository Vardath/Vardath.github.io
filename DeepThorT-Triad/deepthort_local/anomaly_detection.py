"""Exact baseline-relative numeric anomaly candidates, never automatic deletion."""
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
from deepthort_local.statistical_analysis import quantile
from deepthort_local.predictive_modelling import record
from deepthort_local.mathematics import bounded
from deepthort_local.long_form_writing import literal
from deepthort_local.pdf_diagrams import limits
SCHEMA='janus-anomaly-detection-v1'
EXTRA=('csv','.csv')
MAX_ROWS=10000
MAX_EXAMPLES=1000
def checked(s):
    if not isinstance(s,dict) or set(s)!={'csv','delimiter','column','baseline_rows','missing_tokens','iqr_multiplier'}:
        raise ValueError('Expected CSV, numeric column, baseline prefix and explicit IQR threshold')
    if not isinstance(s['csv'],str) or not isinstance(s['delimiter'],str) or s['delimiter'] not in DELIMITERS:
        raise ValueError('Invalid source or delimiter')
    literal(s['column'],200)
    if type(s['baseline_rows']) is not int or not 4<=s['baseline_rows']<MAX_ROWS:
        raise ValueError('Choose at least four baseline rows')
    tokens=s['missing_tokens']
    if not isinstance(tokens,list) or len(tokens)>20 or any(not isinstance(t,str) or len(t)>100 for t in tokens) or len(set(tokens))!=len(tokens):
        raise ValueError('Invalid missing tokens')
    if not isinstance(s['iqr_multiplier'],str):raise ValueError('Use a numeric string for IQR multiplier')
    k=Fraction(numeric(s['iqr_multiplier']))
    if not 0<k<=10:raise ValueError('Multiplier must be positive and at most 10')
    return s

def analyze(raw,s):
    checked(s);header,rows=parse(raw,s['delimiter'])
    if len(rows)>MAX_ROWS or len(rows)<=s['baseline_rows']:raise ValueError('Need monitoring rows after the baseline')
    index=header.index(s['column']);tokens=set(s['missing_tokens'])
    values=[None if row[index] in tokens else bounded(Fraction(numeric(row[index]))) for row in rows]
    base=sorted(v for v in values[:s['baseline_rows']] if v is not None)
    if len(base)<4:raise ValueError('Insufficient complete baseline values')
    q1=quantile(base,Fraction(1,4));q3=quantile(base,Fraction(3,4));iqr=bounded(q3-q1)
    k=Fraction(numeric(s['iqr_multiplier']));lo=bounded(q1-k*iqr);hi=bounded(q3+k*iqr)
    monitoring=values[s['baseline_rows']:]
    hits=[];below=above=missing=0
    for i,v in enumerate(monitoring,s['baseline_rows']+1):
        if v is None:missing+=1;continue
        side='below' if v<lo else 'above' if v>hi else None
        if side is None:continue
        if side=='below':below+=1
        else:above+=1
        if len(hits)<MAX_EXAMPLES:hits.append({'data_row':i,'value':record(v),'side':side})
    complete=len(monitoring)-missing
    if below+above>complete:raise ValueError('Anomaly count reconciliation failed')
    return {'schema':'janus-anomaly-candidates-result-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'column':s['column'],'source_rows':len(rows),'baseline_rows':s['baseline_rows'],
            'baseline_complete':len(base),'baseline_missing':s['baseline_rows']-len(base),
            'monitoring_rows':len(monitoring),'monitoring_missing':missing,
            'q1':record(q1),'q3':record(q3),'iqr':record(iqr),'lower_threshold':record(lo),'upper_threshold':record(hi),
            'degenerate_zero_iqr':not bool(iqr),'below':below,'above':above,'unflagged':complete-below-above,
            'examples':hits,'omitted_examples':below+above-len(hits),
            'anomalies_verified':False,'scope':'Baseline-relative IQR candidate flags only. Zero IQR flags any departure from the equal quartiles; this may be oversensitive. No causal inference, automatic removal or distributional guarantee.'}
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def review(root,source,output,exclude=()):
    return guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def execute(root,plan):
    s,dst,src=validate(root,plan);r=analyze(guard.exact(src,plan['guards'][1],guard.MAX_INPUT),s)
    payload=json.dumps(r,ensure_ascii=True,allow_nan=False,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'anomaly_candidates_flagged','output':plan['output'],'sha256':digest,
            'flagged':r['below']+r['above'],'anomalies_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        limits();print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Anomaly review unavailable; inspect baseline and numeric values'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
