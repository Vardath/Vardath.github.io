"""Typed, deterministic CSV transformations with no code execution."""
from __future__ import annotations
import argparse
import csv
import decimal
import io
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.csv_processing import parse,formula_like,DELIMITERS,MAX_COLUMNS,MAX_CELLS,MAX_FIELD

SCHEMA='janus-data-transformation-v1'
def label(v):
    if not isinstance(v,str) or not v.strip() or len(v)>200 or any(ord(c)<32 for c in v):
        raise ValueError('Invalid column label')
    return v

def numeric(v):
    if not isinstance(v,str) or not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)',v) or len(v)>32:
        raise ValueError('Numeric operation requires explicit finite decimal text')
    n=decimal.Decimal(v)
    if abs(n)>decimal.Decimal('1e15'):raise ValueError('Numeric value exceeds bound')
    return n

def checked(s):
    if not isinstance(s,dict) or set(s)!={'csv','delimiter','operations','formula_like_cells'} or not isinstance(s['csv'],str) or s['delimiter'] not in DELIMITERS or s['formula_like_cells'] not in ('reject','preserve'):
        raise ValueError('Expected typed CSV transformations')
    ops=s['operations']
    if not isinstance(ops,list) or not 1<=len(ops)<=12:raise ValueError('Invalid operation count')
    for op in ops:
        if not isinstance(op,dict):raise ValueError('Invalid operation')
        kind=op.get('type')
        if kind=='rename' and set(op)=={'type','column','name'}:
            label(op['column']);label(op['name'])
        elif kind=='filter' and set(op)=={'type','column','operator','value','mode'}:
            label(op['column'])
            if op['operator'] not in ('eq','ne','lt','le','gt','ge') or op['mode'] not in ('text','decimal') or not isinstance(op['value'],str) or len(op['value'])>MAX_FIELD:
                raise ValueError('Invalid filter')
            if op['mode']=='decimal':numeric(op['value'])
        elif kind=='sort' and set(op)=={'type','column','mode','descending'}:
            label(op['column'])
            if op['mode'] not in ('text','decimal') or type(op['descending']) is not bool:raise ValueError('Invalid sort')
        elif kind=='derive' and set(op)=={'type','name','left','operator','right'}:
            label(op['name']);label(op['left'])
            if op['operator'] not in ('add','subtract','multiply','divide') or not isinstance(op['right'],dict):raise ValueError('Invalid arithmetic operation')
            if set(op['right'])=={'column'}:label(op['right']['column'])
            elif set(op['right'])=={'decimal'}:numeric(op['right']['decimal'])
            else:raise ValueError('Specify a right-hand column or decimal literal')
        else:raise ValueError('Unsupported transformation')
    return s

def transform(raw,spec):
    header,rows=parse(raw,spec['delimiter'])
    def index(column):
        if column not in header:raise ValueError('Unknown column: '+column)
        return header.index(column)
    history=[]
    for op in spec['operations']:
        kind=op['type'];before=len(rows)
        if kind=='rename':
            i=index(op['column'])
            if op['name'] in header and header[i]!=op['name']:raise ValueError('Duplicate renamed column')
            header[i]=op['name']
        elif kind=='filter':
            i=index(op['column']);value=op['value'];cast=numeric if op['mode']=='decimal' else lambda x:x
            target=cast(value)
            import operator
            cmp={'eq':operator.eq,'ne':operator.ne,'lt':operator.lt,'le':operator.le,'gt':operator.gt,'ge':operator.ge}[op['operator']]
            rows=[r for r in rows if cmp(cast(r[i]),target)]
        elif kind=='sort':
            i=index(op['column']);cast=numeric if op['mode']=='decimal' else lambda x:x
            rows=sorted(rows,key=lambda r:cast(r[i]),reverse=op['descending'])
        elif kind=='derive':
            if op['name'] in header or len(header)>=MAX_COLUMNS or (len(rows)+1)*(len(header)+1)>MAX_CELLS:raise ValueError('Derived column exceeds bound or duplicates header')
            i=index(op['left']);right=op['right']
            j=index(right['column']) if 'column' in right else None
            constant=numeric(right['decimal']) if j is None else None
            with decimal.localcontext() as ctx:
                ctx.prec=32
                ctx.traps[decimal.DivisionByZero]=True
                ctx.traps[decimal.InvalidOperation]=True
                for row in rows:
                    a=numeric(row[i]);b=numeric(row[j]) if j is not None else constant
                    try:
                        if op['operator']=='add':v=a+b
                        elif op['operator']=='subtract':v=a-b
                        elif op['operator']=='multiply':v=a*b
                        else:v=a/b
                    except decimal.DecimalException as exc:raise ValueError('Invalid decimal calculation') from exc
                    if not v.is_finite() or abs(v)>decimal.Decimal('1e15'):raise ValueError('Derived numeric result exceeds bound')
                    result=format(v,'f')
                    if '.' in result:result=result.rstrip('0').rstrip('.')
                    row.append(result)
            header.append(op['name'])
        history.append({'operation':kind,'input_rows':before,'output_rows':len(rows),'columns':len(header)})
    suspect=sum(formula_like(v) for r in [header,*rows] for v in r)
    if suspect and spec['formula_like_cells']=='reject':raise ValueError('Formula-like output refused')
    stream=io.StringIO(newline='');writer=csv.writer(stream,delimiter=spec['delimiter'],lineterminator='\r\n')
    writer.writerow(header);writer.writerows(rows);payload=stream.getvalue().encode('utf-8')
    if parse(payload,spec['delimiter'])!=(header,rows):raise ValueError('Transformed CSV roundtrip mismatch')
    return payload,{'operations':history,'output_rows':len(rows),'columns':len(header),'formula_like_cells_preserved':suspect,
                    'decimal_precision':32}

def review(root,source,output,exclude=()):
    return guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.csv',extra=('csv','.csv'))
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.csv',extra=('csv','.csv'))
def execute(root,plan):
    spec,dst,source=validate(root,plan)
    payload,stats=transform(guard.exact(source,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-data-transformation-result-v1','status':'transformed_csv_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**stats}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Transformation unavailable; inspect reviewed source and typed operations'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
