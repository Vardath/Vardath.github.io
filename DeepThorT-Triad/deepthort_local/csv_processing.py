"""Bounded local CSV projection, row selection and delimiter conversion."""
from __future__ import annotations
import argparse
import csv
import io
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard

SCHEMA='janus-csv-processing-v1'
DELIMITERS={',',';','\t','|'}
MAX_ROWS=20000
MAX_COLUMNS=128
MAX_CELLS=400000
MAX_FIELD=32768

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'csv','input_delimiter','output_delimiter','columns','start_row','row_count','formula_like_cells'}:
        raise ValueError('Expected CSV source, explicit delimiters, columns, row range and formula policy')
    if not isinstance(spec['csv'],str) or any(not isinstance(spec[k],str) or spec[k] not in DELIMITERS for k in ('input_delimiter','output_delimiter')):
        raise ValueError('Unsupported CSV input or delimiter')
    cols=spec['columns']
    if not isinstance(cols,list) or not 1<=len(cols)<=MAX_COLUMNS or any(not isinstance(c,str) or not c or len(c)>MAX_FIELD for c in cols) or len(set(cols))!=len(cols):
        raise ValueError('Select distinct exact column headers')
    if type(spec['start_row']) is not int or not 1<=spec['start_row']<=MAX_ROWS or type(spec['row_count']) is not int or not 1<=spec['row_count']<=MAX_ROWS:
        raise ValueError('Invalid one-based data row window')
    if spec['formula_like_cells'] not in ('reject','preserve'):
        raise ValueError('Explicit spreadsheet formula-like-cell policy required')
    return spec

def parse(raw,delimiter):
    try:text=raw.decode('utf-8-sig')
    except UnicodeError as exc:raise ValueError('CSV must be UTF-8') from exc
    if '\0' in text:raise ValueError('NUL in CSV')
    previous=csv.field_size_limit()
    csv.field_size_limit(MAX_FIELD)
    try:
        reader=csv.reader(io.StringIO(text,newline=''),delimiter=delimiter,strict=True)
        header=next(reader,None)
        if not header or not 1<=len(header)<=MAX_COLUMNS or any(not c.strip() for c in header) or len(set(header))!=len(header):
            raise ValueError('CSV header missing, blank or duplicated')
        rows=[]
        for row in reader:
            if len(row)!=len(header):raise ValueError('CSV row width mismatch')
            if len(rows)>=MAX_ROWS or (len(rows)+2)*len(header)>MAX_CELLS:
                raise ValueError('CSV record budget exceeded')
            rows.append(row)
        return header,rows
    except csv.Error as exc:raise ValueError('Malformed or oversized CSV field') from exc
    finally:csv.field_size_limit(previous)

def formula_like(value):
    if not value:return False
    # Do not mistake ordinary signed decimal/exponent numbers for formulas.
    if re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?',value.strip()):
        return False
    stripped=value.lstrip()
    return value.startswith(('\t','\r','\n')) or bool(stripped and stripped[0] in '=+-@')

def process(raw,spec):
    header,rows=parse(raw,spec['input_delimiter'])
    try:indexes=[header.index(x) for x in spec['columns']]
    except ValueError as exc:raise ValueError('Requested CSV column missing') from exc
    start=spec['start_row']-1
    if start>len(rows):raise ValueError('Start row beyond CSV data')
    selected=[[row[i] for i in indexes] for row in rows[start:start+spec['row_count']]]
    suspect=sum(formula_like(v) for row in [spec['columns'],*selected] for v in row)
    if suspect and spec['formula_like_cells']=='reject':raise ValueError('Formula-like text refused for spreadsheet safety')
    stream=io.StringIO(newline='')
    writer=csv.writer(stream,delimiter=spec['output_delimiter'],lineterminator='\r\n')
    writer.writerow(spec['columns']);writer.writerows(selected)
    payload=stream.getvalue().encode('utf-8')
    actual_header,actual_rows=parse(payload,spec['output_delimiter'])
    if actual_header!=spec['columns'] or actual_rows!=selected:raise ValueError('CSV roundtrip mismatch')
    return payload,{'source_rows':len(rows),'output_rows':len(selected),'columns':len(indexes),
                    'formula_like_cells_preserved':suspect,'value_type':'literal strings'}

def review(root,source,output,exclude=()):
    return guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.csv',extra=('csv','.csv'))
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.csv',extra=('csv','.csv'))
def execute(root,plan):
    spec,dst,source=validate(root,plan)
    payload,stats=process(guard.exact(source,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-csv-processing-result-v1','status':'csv_roundtrip_verified','output':plan['output'],
            'sha256':sha,'source_unchanged':True,**stats}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--plan',required=True);args=parser.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2)
            resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(args.root,json.loads(args.plan)),sort_keys=True),flush=True);return 0
    except Exception as exc:
        print(json.dumps({'status':'blocked','error_type':type(exc).__name__,'reason':'CSV processing unavailable; inspect source, selected columns, row bounds and formula policy'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
