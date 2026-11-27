"""Create a new styled XLSX workbook from an exact typed project specification."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.spreadsheet_edit import scalar,serialize,snapshot,VERSION,MAX_CELLS,MAX_SHEETS

SCHEMA='janus-spreadsheet-create-v1'
FORMATS={'general':'General','integer':'0','decimal':'#,##0.00','percent':'0.0%','text':'@'}

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'sheets'} or not isinstance(spec['sheets'],list) or not 1<=len(spec['sheets'])<=MAX_SHEETS:
        raise ValueError('Expected bounded workbook sheets')
    result=[];seen=set();cells=0
    for s in spec['sheets']:
        if not isinstance(s,dict) or set(s)!={'name','headers','rows','formats'}:
            raise ValueError('Expected name, headers, rows and formats')
        title=s['name']
        if not isinstance(title,str) or not 1<=len(title)<=31 or title!=title.strip() or re.search(r'[\x00-\x1f\\/*?:\[\]]',title) or title.startswith("'") or title.endswith("'") or title.casefold() in seen:
            raise ValueError('Invalid or duplicate worksheet name')
        seen.add(title.casefold())
        headers=s['headers'];rows=s['rows'];formats=s['formats']
        if not isinstance(headers,list) or not 1<=len(headers)<=40 or any(not isinstance(h,str) or not h.strip() or len(h)>100 for h in headers):
            raise ValueError('Invalid table headers')
        headers=[scalar(h) for h in headers]
        if len({h.casefold() for h in headers})!=len(headers):
            raise ValueError('Duplicate table headers')
        if not isinstance(rows,list) or len(rows)>5000 or not isinstance(formats,list) or len(formats)!=len(headers) or any(not isinstance(f,str) or f not in FORMATS for f in formats):
            raise ValueError('Invalid rows or number formats')
        cells+=(len(rows)+1)*len(headers)
        if cells>MAX_CELLS:raise ValueError('Workbook cell budget exceeded')
        clean=[]
        for row in rows:
            if not isinstance(row,list) or len(row)!=len(headers):raise ValueError('Row width does not match headers')
            clean.append([scalar(v) for v in row])
        result.append({'name':title,'headers':headers,'rows':clean,'formats':formats})
    return {'sheets':result}

def create(spec):
    import openpyxl
    from openpyxl.styles import Font,PatternFill,Alignment
    from openpyxl.utils import get_column_letter
    if openpyxl.__version__!=VERSION:raise ValueError('Install pinned spreadsheet tools first')
    wb=openpyxl.Workbook();wb.remove(wb.active)
    try:
        for s in spec['sheets']:
            ws=wb.create_sheet(s['name'])
            ws.freeze_panes='A2'
            for i,h in enumerate(s['headers'],1):
                c=ws.cell(1,i,h);c.data_type='s'
                c.font=Font(name='Calibri',bold=True,color='FFFFFF')
                c.fill=PatternFill('solid',fgColor='24445C')
                c.alignment=Alignment(vertical='center',wrap_text=True)
            ws.row_dimensions[1].height=29
            for r,row in enumerate(s['rows'],2):
                for i,v in enumerate(row,1):
                    c=ws.cell(r,i,v)
                    if isinstance(v,str):c.data_type='s'
                    c.number_format=FORMATS[s['formats'][i-1]]
                    if r%2==0:c.fill=PatternFill('solid',fgColor='F0F4F7')
                    c.alignment=Alignment(vertical='top',wrap_text=True)
            for i,h in enumerate(s['headers'],1):
                lengths=[len(str(v)) for row in s['rows'] if (v:=row[i-1]) is not None]
                ws.column_dimensions[get_column_letter(i)].width=min(55,max(13,len(h)+3,max(lengths,default=0)+2))
            ws.auto_filter.ref='A1:'+get_column_letter(len(s['headers']))+str(len(s['rows'])+1)
        payload=serialize(wb,snapshot(wb))
        reopened=openpyxl.load_workbook(__import__('io').BytesIO(payload),data_only=False)
        try:
            for s in spec['sheets']:
                ws=reopened[s['name']]
                if ws.freeze_panes!='A2' or not ws.auto_filter.ref or not ws['A1'].font.bold:
                    raise ValueError('Workbook layout metadata verification failed')
        finally:reopened.close()
        return payload
    finally:wb.close()

def review(root,source,output,exclude=()):
    return guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.xlsx')
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.xlsx')
def execute(root,plan):
    spec,dst,_=validate(root,plan);payload=create(spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-spreadsheet-create-result-v1','status':'workbook_structure_verified','output':plan['output'],
            'sha256':sha,'sheets':len(spec['sheets']),'data_rows':sum(len(s['rows']) for s in spec['sheets']),
            'formula_values_recalculated':False,'visual_render_verified':False}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--plan',required=True);args=parser.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(768*1024*1024,)*2)
            resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(args.root,json.loads(args.plan)),sort_keys=True),flush=True);return 0
    except Exception as exc:
        print(json.dumps({'status':'blocked','error_type':type(exc).__name__,'reason':'Workbook creation unavailable; inspect typed specification and installed tools'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
