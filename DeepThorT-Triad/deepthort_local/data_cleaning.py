"""Reviewed deterministic CSV cleaning with explicit missing-value and duplicate policy."""
from __future__ import annotations
import argparse
import csv
import io
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.csv_processing import parse,formula_like,DELIMITERS,MAX_FIELD,MAX_COLUMNS

SCHEMA='janus-data-cleaning-v1'
def checked(s):
    keys={'csv','delimiter','trim_columns','missing_tokens','missing_columns','missing_action','fill_value','deduplicate_by','formula_like_cells'}
    if not isinstance(s,dict) or set(s)!=keys or not isinstance(s['csv'],str) or s['delimiter'] not in DELIMITERS:
        raise ValueError('Expected typed CSV cleaning specification')
    for k in ('trim_columns','missing_columns','deduplicate_by'):
        v=s[k]
        if not isinstance(v,list) or len(v)>MAX_COLUMNS or any(not isinstance(x,str) or not x or len(x)>MAX_FIELD for x in v) or len(set(v))!=len(v):
            raise ValueError('Invalid column list: '+k)
    tokens=s['missing_tokens']
    if not isinstance(tokens,list) or len(tokens)>32 or any(not isinstance(x,str) or len(x)>200 for x in tokens) or len(set(tokens))!=len(tokens):
        raise ValueError('Invalid literal missing tokens')
    if s['missing_action'] not in ('keep','drop_row','fill') or s['formula_like_cells'] not in ('reject','preserve'):
        raise ValueError('Explicit cleaning and formula policy required')
    if not isinstance(s['fill_value'],str) or len(s['fill_value'])>MAX_FIELD or '\0' in s['fill_value']:
        raise ValueError('Invalid fill text')
    if s['missing_action']!='keep' and not s['missing_columns']:raise ValueError('Select columns for missing-value handling')
    if s['missing_action']!='fill' and s['fill_value']!='':raise ValueError('Fill value requires fill action')
    return s

def clean(raw,spec):
    header,rows=parse(raw,spec['delimiter'])
    try:
        trim=[header.index(x) for x in spec['trim_columns']]
        missing=[header.index(x) for x in spec['missing_columns']]
        dedup=[header.index(x) for x in spec['deduplicate_by']]
    except ValueError as exc:raise ValueError('Selected cleaning column missing') from exc
    tokens=set(spec['missing_tokens']);seen=set();output=[]
    stats={'input_rows':len(rows),'trimmed_cells':0,'missing_cells_seen':0,'filled_cells':0,'missing_rows_removed':0,'duplicate_rows_removed':0}
    for original in rows:
        row=list(original)
        for i in trim:
            value=row[i].strip()
            stats['trimmed_cells']+=value!=row[i];row[i]=value
        empty=[i for i in missing if row[i] in tokens]
        stats['missing_cells_seen']+=len(empty)
        if empty and spec['missing_action']=='drop_row':
            stats['missing_rows_removed']+=1;continue
        if spec['missing_action']=='fill':
            for i in empty:row[i]=spec['fill_value'];stats['filled_cells']+=1
        if dedup:
            key=tuple(row[i] for i in dedup)
            if key in seen:stats['duplicate_rows_removed']+=1;continue
            seen.add(key)
        output.append(row)
    suspect=sum(formula_like(v) for r in [header,*output] for v in r)
    if suspect and spec['formula_like_cells']=='reject':raise ValueError('Formula-like output refused')
    stream=io.StringIO(newline='');writer=csv.writer(stream,delimiter=spec['delimiter'],lineterminator='\r\n')
    writer.writerow(header);writer.writerows(output);payload=stream.getvalue().encode('utf-8')
    if parse(payload,spec['delimiter'])!=(header,output):raise ValueError('Cleaned CSV roundtrip mismatch')
    stats.update(output_rows=len(output),formula_like_cells_preserved=suspect)
    if stats['input_rows']!=stats['output_rows']+stats['missing_rows_removed']+stats['duplicate_rows_removed']:
        raise ValueError('Cleaning row reconciliation failed')
    return payload,stats

def review(root,source,output,exclude=()):
    return guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.csv',extra=('csv','.csv'))
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.csv',extra=('csv','.csv'))
def execute(root,plan):
    spec,dst,source=validate(root,plan)
    payload,stats=clean(guard.exact(source,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-data-cleaning-result-v1','status':'cleaned_csv_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**stats}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Cleaning unavailable; inspect reviewed source and policies'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
