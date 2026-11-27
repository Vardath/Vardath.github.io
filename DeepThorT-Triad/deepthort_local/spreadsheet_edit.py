"""Reviewed cell edits of bounded ordinary XLSX workbooks, never the original."""
from __future__ import annotations
import argparse
import io
import json
import math
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard

SCHEMA='janus-spreadsheet-edit-v1'
VERSION='3.1.5'
MAX_CELLS=50000
MAX_SHEETS=32
MAX_XML=32*1024*1024

def scalar(v):
    if v is None or type(v) is bool:return v
    if type(v) is int and abs(v)<=10**15:return v
    if type(v) is float and math.isfinite(v) and abs(v)<=10**15:return v
    if isinstance(v,str) and 0<len(v)<=2000 and not any(ord(c)<32 and c not in '\t\n\r' or 0xd800<=ord(c)<=0xdfff or ord(c) in (0xfffe,0xffff) for c in v):return v
    raise ValueError('Invalid spreadsheet literal; use null to clear a cell')

def coordinate(value):
    from openpyxl.utils.cell import coordinate_from_string,column_index_from_string
    if not isinstance(value,str) or not re.fullmatch(r'[A-Z]{1,3}[1-9][0-9]{0,6}',value):
        raise ValueError('Use a single uppercase cell address')
    col,row=coordinate_from_string(value)
    if column_index_from_string(col)>16384 or row>1048576:raise ValueError('Cell outside XLSX bounds')
    return value

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'workbook','edits'} or not isinstance(spec['workbook'],str):
        raise ValueError('Expected workbook and edits')
    edits=spec['edits']
    if not isinstance(edits,list) or not 1<=len(edits)<=500:raise ValueError('Invalid edit count')
    seen=set();result=[]
    for e in edits:
        if not isinstance(e,dict) or set(e)!={'sheet','cell','value'} or not isinstance(e['sheet'],str) or not 1<=len(e['sheet'])<=31:
            raise ValueError('Invalid cell edit')
        key=(e['sheet'].casefold(),coordinate(e['cell']))
        if key in seen:raise ValueError('Duplicate cell edit')
        seen.add(key);result.append({'sheet':e['sheet'],'cell':e['cell'],'value':scalar(e['value'])})
    return {'workbook':spec['workbook'],'edits':result}

def review(root,source,output,exclude=()):
    return guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.xlsx',extra=('workbook','.xlsx'))

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.xlsx',extra=('workbook','.xlsx'))

def safe_archive(raw):
    # Refuse advanced OOXML parts that openpyxl might silently discard.
    allowed=re.compile(r'(?:\[Content_Types\]\.xml|_rels/\.rels|docProps/(?:core|app)\.xml|xl/(?:workbook|styles|sharedStrings)\.xml|xl/_rels/workbook\.xml\.rels|xl/theme/theme[0-9]+\.xml|xl/worksheets/sheet[0-9]+\.xml)')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files=z.infolist()
        if not 1<=len(files)<=100 or len({f.filename for f in files})!=len(files) or sum(f.file_size for f in files)>MAX_XML:
            raise ValueError('Workbook archive exceeds bound')
        for f in files:
            if not allowed.fullmatch(f.filename) or f.flag_bits&1:
                raise ValueError('Advanced or encrypted workbook part unsupported')
            data=z.read(f)
            if b'\0' in data or re.search(br'<!\s*(?:DOCTYPE|ENTITY)',data,re.I):
                raise ValueError('Unsafe workbook XML')
            if f.filename.endswith('.rels') and re.search(br'TargetMode\s*=\s*["\x27]External["\x27]',data,re.I):
                raise ValueError('External workbook relationships refused')

def load(raw):
    import openpyxl
    if openpyxl.__version__!=VERSION:raise ValueError('Install pinned spreadsheet tools first')
    safe_archive(raw)
    wb=openpyxl.load_workbook(io.BytesIO(raw),data_only=False,keep_links=False)
    if not 1<=len(wb.worksheets)<=MAX_SHEETS or wb.defined_names:
        raise ValueError('Workbook sheet count or defined names unsupported')
    total=0
    for ws in wb.worksheets:
        total+=len(ws._cells)
        if total>MAX_CELLS or ws.merged_cells.ranges or ws.conditional_formatting or ws.data_validations.dataValidation or ws.tables:
            raise ValueError('Advanced worksheet structures or cell count unsupported')
        if any(c.data_type=='f' and not isinstance(c.value,str) for c in ws._cells.values()):
            raise ValueError('Array or data-table formulas unsupported')
    return wb

def snapshot(wb):
    # Include populated values, data types, style arrays and sheet order.
    # Empty unstyled cells are not serialized consistently by XLSX.
    rows={}
    for ws in wb.worksheets:
        cells={}
        for c in ws._cells.values():
            if c.value is None and not c.has_style:continue
            cells[c.coordinate]=(c.value,c.data_type if c.value is not None else None,tuple(c._style) if c.has_style else ())
        rows[ws.title]=cells
    return list(wb.sheetnames),rows

def serialize(wb,expected):
    stream=io.BytesIO();wb.save(stream);payload=stream.getvalue()
    if len(payload)>guard.MAX_OUTPUT:raise ValueError('Workbook exceeds output bound')
    reopened=load(payload)
    try:
        if snapshot(reopened)!=expected:raise ValueError('Reopened workbook cell/style verification failed')
    finally:reopened.close()
    return payload

def apply(wb,edits):
    for edit in edits:
        if edit['sheet'] not in wb.sheetnames:raise ValueError('Sheet name not found')
        cell=wb[edit['sheet']][edit['cell']]
        if cell.data_type=='f':raise ValueError('Existing formula cell requires a separate formula operation')
        value=edit['value'];cell.value=value
        if isinstance(value,str):cell.data_type='s'  # Literal, never formula inference.

def execute(root,plan):
    spec,dst,source=validate(root,plan)
    raw=guard.exact(source,plan['guards'][1],guard.MAX_INPUT)
    wb=load(raw)
    try:
        apply(wb,spec['edits'])
        payload=serialize(wb,snapshot(wb))
    finally:wb.close()
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-spreadsheet-edit-result-v1','status':'cell_structure_verified','output':plan['output'],
            'sha256':sha,'edited_cells':len(spec['edits']),'source_unchanged':True,
            'formula_values_recalculated':False,'full_workbook_fidelity_verified':False}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--plan',required=True)
    args=parser.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(768*1024*1024,)*2)
            resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(args.root,json.loads(args.plan)),sort_keys=True),flush=True);return 0
    except Exception as exc:
        print(json.dumps({'status':'blocked','error_type':type(exc).__name__,'reason':'Spreadsheet edit unavailable; inspect reviewed workbook, specification and installed tools'}),flush=True);return 1

if __name__=='__main__':sys.exit(main())
