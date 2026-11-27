"""Reviewed PDF diagram interpretation: labelled rectangular nodes and straight connectors."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.pdf_knowledge_worker import MAX_PDF_BYTES,MAX_PAGES,PARSER_VERSION
from deepthort_local.pdf_table_extract import PARSER
SCHEMA='janus-pdf-diagrams-v1'
EXTRA=('document','.pdf')
MAX_SELECTED=8

def checked(s):
    if not isinstance(s,dict) or set(s)!={'document','pages'} or not isinstance(s['document'],str):
        raise ValueError('Expected PDF and page list')
    p=s['pages']
    if not isinstance(p,list) or not 1<=len(p)<=MAX_SELECTED or any(type(n) is not int or not 1<=n<=MAX_PAGES for n in p) or len(set(p))!=len(p):
        raise ValueError('Choose 1–8 distinct PDF pages')
    return s

def bounds(obj):
    box=[float(obj[k]) for k in ('x0','top','x1','bottom')]
    if not all(math.isfinite(x) for x in box) or box[0]>box[2] or box[1]>box[3]:
        raise ValueError('Invalid PDF geometry')
    return box

def distance_to_border(point,b):
    x,y=point;l,t,r,z=b
    if l<=x<=r and t<=y<=z:return min(x-l,r-x,y-t,z-y)
    return math.hypot(max(l-x,0,x-r),max(t-y,0,y-z))

def page_diagram(page):
    if len(page.chars)>50000 or len(page.rects)>256 or len(page.lines)>2000 or len(page.curves)>2000:
        raise ValueError('Diagram geometry exceeds page budget')
    words=page.extract_words()
    if len(words)>10000:raise ValueError('Too many words')
    nodes=[]
    for rect in sorted(page.rects,key=lambda r:(r['top'],r['x0'],r['bottom'],r['x1'])):
        box=bounds(rect)
        if box[2]-box[0]<12 or box[3]-box[1]<8:continue
        inside=[w for w in words if (box[0]<=float(w['x0']) and float(w['x1'])<=box[2]
                and box[1]<=float(w['top']) and float(w['bottom'])<=box[3])]
        label=' '.join(w['text'] for w in inside)
        if not label or len(label)>500:continue
        nodes.append({'id':'n'+str(len(nodes)+1),'label':label,'bbox_points_top_origin':box})
    def endpoint(p):
        hits=[n['id'] for n in nodes if distance_to_border(p,n['bbox_points_top_origin'])<=3]
        return hits[0] if len(hits)==1 else None
    connectors=[]
    for line in page.lines:
        # pdfplumber provides transformed top-origin points; bounding boxes
        # alone do not preserve the slope of a diagonal segment.
        pts=line.get('pts')
        if not isinstance(pts,list) or len(pts)!=2:continue
        try:p,q=[[float(v) for v in pt] for pt in pts]
        except (TypeError,ValueError):continue
        if len(p)!=2 or len(q)!=2 or not all(math.isfinite(v) for v in p+q) or math.dist(p,q)<6:continue
        a,b=endpoint(p),endpoint(q)
        if a and b and a!=b:
            connectors.append({'endpoints':[a,b],'points_top_origin':[p,q],
                               'direction':None,'status':'geometric_connector_candidate'})
    return {'page':page.page_number,'nodes':nodes,'connectors':connectors,
            'uninterpreted_curves':len(page.curves),'embedded_images':len(page.images),
            'text_layer_present':bool(page.chars)}

def inspect(raw,pages,analyzer=page_diagram):
    import pdfplumber
    from pypdf import PdfReader,__version__
    if pdfplumber.__version__!=PARSER or __version__!=PARSER_VERSION:
        raise ValueError('Install pinned PDF production tools')
    if len(raw)>MAX_PDF_BYTES or not raw.startswith(b'%PDF-'):raise ValueError('Invalid PDF')
    reader=PdfReader(io.BytesIO(raw),strict=True)
    if reader.is_encrypted or not 1<=len(reader.pages)<=MAX_PAGES or max(pages)>len(reader.pages):
        raise ValueError('Unsupported PDF or selection')
    with pdfplumber.open(io.BytesIO(raw)) as doc:
        if len(doc.pages)!=len(reader.pages):raise ValueError('Page count disagreement')
        results=[]
        for number in pages:
            page=doc.pages[number-1]
            try:results.append(analyzer(page))
            finally:page.close()
    return results

def analyze(raw,pages):
    return {'schema':'janus-pdf-diagram-result-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'pages':inspect(raw,pages),'semantic_verification':False,'visual_verification':False,
            'scope':'Labelled vector rectangles and unambiguous straight-line endpoint candidates only. No arrows, raster diagrams, causal or semantic interpretation claims.'}

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    _,_,doc=validate(root,plan)
    if doc.stat().st_size>MAX_PDF_BYTES:raise ValueError('PDF exceeds byte limit')
    return plan,dict(s,scope='Extract labelled vector rectangles and connector candidates; no semantic verification.')
def execute(root,plan):
    s,dst,doc=validate(root,plan);r=analyze(guard.exact(doc,plan['guards'][1],MAX_PDF_BYTES),s['pages'])
    payload=json.dumps(r,ensure_ascii=True,allow_nan=False,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'diagram_candidates_observed','output':plan['output'],'sha256':digest,
            'pages':len(r['pages']),'nodes':sum(len(p['nodes']) for p in r['pages']),
            'connectors':sum(len(p['connectors']) for p in r['pages']),'semantic_verification':False}
def limits():
    if sys.platform!='win32':
        import resource
        resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2)
        resource.setrlimit(resource.RLIMIT_CPU,(30,30))
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        limits();print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'PDF diagram inspection unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
