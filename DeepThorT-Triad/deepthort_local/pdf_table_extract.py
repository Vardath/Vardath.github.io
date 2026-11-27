"""Reviewed local extraction of geometrically ruled PDF tables; no OCR or inferred cells."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local.action_guards import snapshot_file
from deepthort_local.pdf_page_edit import target
from deepthort_local.pdf_knowledge_worker import MAX_PDF_BYTES,MAX_PAGES
from deepthort_local.source_security import exclusions,excluded,linked
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-pdf-table-extraction-v1'
PARSER='0.11.7'
MAX_SELECTED=32
MAX_TABLES=100
MAX_CELLS=20000
MAX_TEXT=400000
MAX_OUTPUT=2_000_000

def output_path(root,relative,exclude):
    if not isinstance(relative,str) or not 1<=len(relative)<=300 or not relative.casefold().endswith('.json'):
        raise ValueError('Choose a new project-relative JSON output')
    parts=relative.split('/')
    if any(not x or x in ('.','..') or ':' in x or '\\' in x or '\0' in x or x.endswith((' ','.')) for x in parts) or excluded(relative,set(exclude)):
        raise ValueError('Protected or unsafe output path')
    current=root
    for part in parts:
        current=current/part
        if current.exists() or current.is_symlink():
            if linked(current):raise ValueError('Linked output path refused')
    if current.resolve(strict=False)!=current or not current.parent.is_dir() or current.exists() or current.is_symlink():
        raise ValueError('Output must be new and inside an existing project folder')
    return current

def selected_pages(spec):
    if not isinstance(spec,str) or not 1<=len(spec)<=160:raise ValueError('Specify page numbers')
    if not re.fullmatch(r'\s*[1-9][0-9]{0,2}(?:\s*,\s*[1-9][0-9]{0,2})*\s*',spec):
        raise ValueError('Enter comma-separated page numbers, e.g. 1,2,5')
    pages=[int(x) for x in spec.split(',')]
    if len(pages)>MAX_SELECTED or len(set(pages))!=len(pages) or max(pages)>MAX_PAGES:
        raise ValueError('Invalid or duplicate page numbers; at most 32 selected pages')
    return pages

def review(root,source,output,spec,exclude=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude)
    a=target(root,source,exclude,exists=True);output_path(root,output,exclude)
    if a.stat().st_size>MAX_PDF_BYTES:raise ValueError('Source exceeds 4 MiB PDF limit')
    return {'schema':SCHEMA,'root':str(root),'source':source,'output':output,'pages':selected_pages(spec),
            'exclude':exclude,'source_guard':snapshot_file(a),'expires_at':int(time.time())+1800}

def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if (not isinstance(plan,dict) or set(plan)!={'schema','root','source','output','pages','exclude','source_guard','expires_at'}
        or plan['schema']!=SCHEMA or plan['root']!=str(root)
        or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800
        or exclusions(plan['exclude'])!=plan['exclude']):
        raise ValueError('Invalid or expired table extraction approval')
    pages=plan['pages']
    if not isinstance(pages,list) or not 1<=len(pages)<=MAX_SELECTED or any(type(n) is not int or not 1<=n<=MAX_PAGES for n in pages) or len(set(pages))!=len(pages):
        raise ValueError('Invalid reviewed page selection')
    a=target(root,plan['source'],plan['exclude'],exists=True);b=output_path(root,plan['output'],plan['exclude'])
    if a.stat().st_size>MAX_PDF_BYTES or snapshot_file(a)!=plan['source_guard']:raise ValueError('Reviewed PDF changed')
    return a,b

def extract(raw,pages):
    import pdfplumber
    from pypdf import PdfReader
    if pdfplumber.__version__!=PARSER:raise ValueError('Install the pinned PDF table tools first')
    reader=PdfReader(io.BytesIO(raw),strict=True)
    if reader.is_encrypted or not 1<=len(reader.pages)<=MAX_PAGES or max(pages)>len(reader.pages):
        raise ValueError('Encrypted PDF or selected pages outside supported range')
    tables=[];summaries=[];cells=chars=0
    with pdfplumber.open(io.BytesIO(raw)) as document:
        if len(document.pages)!=len(reader.pages):raise ValueError('PDF page-count disagreement')
        for number in pages:
            page=document.pages[number-1]
            try:
                if len(page.chars)>50000 or len(page.edges)>5000:
                    raise ValueError('Page geometry exceeds extraction budget')
                found=page.find_tables(table_settings={'vertical_strategy':'lines','horizontal_strategy':'lines'})
                if len(found)+len(tables)>MAX_TABLES:raise ValueError('Table count exceeds budget')
                accepted=0;unresolved=0
                for table in sorted(found,key=lambda t:(t.bbox[1],t.bbox[0])):
                    rows=table.extract()
                    if not rows or len(rows)<2 or len(rows[0])<2 or any(len(row)!=len(rows[0]) for row in rows):
                        unresolved+=1;continue
                    if not any(isinstance(v,str) and v.strip() for row in rows for v in row):
                        unresolved+=1;continue
                    if any(not isinstance(v,(str,type(None))) for row in rows for v in row):
                        raise ValueError('Unexpected table cell type')
                    cells+=sum(len(row) for row in rows)
                    chars+=sum(len(v) for row in rows for v in row if isinstance(v,str))
                    if cells>MAX_CELLS or chars>MAX_TEXT:raise ValueError('Extracted tables exceed budget')
                    bounds=[float(x) for x in table.bbox]
                    if len(bounds)!=4 or not all(math.isfinite(x) for x in bounds):
                        raise ValueError('Invalid table coordinates')
                    tables.append({'page':number,'table':accepted+1,'bbox_points_top_origin':bounds,
                                   'rows':rows,'merged_or_missing_cells':sum(v is None for row in rows for v in row)})
                    accepted+=1
                summaries.append({'page':number,'tables':accepted,'unresolved_candidates':unresolved,
                                  'text_layer_present':bool(page.chars)})
            finally:page.close()
    return {'schema':'janus-pdf-table-data-v1','parser':'pdfplumber '+PARSER,
            'pages':summaries,'tables':tables,'cell_count':cells,'status':'extracted_candidates' if tables else 'no_supported_tables',
            'scope':'Ruled text-layer table candidates only. Null cells are unresolved; no header inference, OCR, cross-page stitching or semantic verification.',
            'exhaustive_extraction_verified':False,'visual_verification':False}

def execute(root,plan):
    a,b=validate(root,plan);require_storage(a.parent,b.parent)
    with a.open('rb') as f:raw=f.read(MAX_PDF_BYTES+1)
    if len(raw)>MAX_PDF_BYTES or hashlib.sha256(raw).hexdigest()!=plan['source_guard']['expected']:
        raise ValueError('Reviewed source bytes changed')
    result=extract(raw,plan['pages']);result['source_sha256']=plan['source_guard']['expected']
    payload=(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    if len(payload)>MAX_OUTPUT or json.loads(payload)!=result:raise ValueError('Invalid or oversized extraction output')
    a,b=validate(root,plan);require_storage(a.parent,b.parent)
    fd,tmp=tempfile.mkstemp(prefix='.janus-tables-',suffix='.tmp',dir=b.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(payload);f.flush();os.fsync(f.fileno())
        validate(root,plan);os.link(tmp,b)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return {'schema':'janus-pdf-table-receipt-v1','status':result['status'],'output':plan['output'],
            'sha256':hashlib.sha256(payload).hexdigest(),'tables':len(result['tables']),
            'cells':result['cell_count'],'source_unchanged':True,'visual_verification':False}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--plan',required=True)
    args=parser.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2)
            resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        result=execute(args.root,json.loads(args.plan));print(json.dumps(result,sort_keys=True),flush=True)
        return 0 if result['status']=='extracted_candidates' else 1
    except Exception as exc:
        print(json.dumps({'schema':'janus-pdf-table-receipt-v1','status':'blocked','error_type':type(exc).__name__,
                          'reason':'Extraction unavailable; check reviewed source, page selection and pinned tools'}),flush=True)
        return 1

if __name__=='__main__':sys.exit(main())
