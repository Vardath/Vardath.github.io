"""Bounded PDF layout inspection using exact text-layer and vector geometry."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.pdf_diagrams import checked,bounds,inspect,limits,EXTRA,MAX_PDF_BYTES
SCHEMA='janus-pdf-layout-v1'
MAX_LINES=1200
MAX_WORDS=10000

def page_layout(page):
    if len(page.chars)>50000 or len(page.edges)>5000 or len(page.images)>256:
        raise ValueError('Page geometry exceeds layout budget')
    l,t,r,b=bounds(dict(zip(('x0','top','x1','bottom'),page.bbox)))
    if r<=l or b<=t:raise ValueError('Invalid page size')
    words=page.extract_words(extra_attrs=['size','fontname'])
    if len(words)>MAX_WORDS:raise ValueError('Word count exceeds budget')
    rows=[]
    for w in sorted(words,key=lambda v:(v['top'],v['x0'])):
        box=bounds(w)
        if rows and abs(rows[-1]['anchor']-box[1])<=3:
            rows[-1]['words'].append(w)
        else:
            rows.append({'anchor':box[1],'words':[w]})
    if len(rows)>MAX_LINES:raise ValueError('Line count exceeds budget')
    segments=[]
    for row in rows:
        group=[];right=None
        for w in sorted(row['words'],key=lambda v:v['x0']):
            if group and w['x0']-right>36:
                segments.append(group);group=[];right=None
            group.append(w);right=max(right if right is not None else w['x1'],w['x1'])
        if group:segments.append(group)
    if len(segments)>MAX_LINES:raise ValueError('Segment count exceeds budget')
    text=[]
    for group in segments:
        boxes=[bounds(w) for w in group]
        sizes=[float(w['size']) for w in group]
        if not all(math.isfinite(v) and v>0 for v in sizes):raise ValueError('Invalid font size')
        value=' '.join(w['text'] for w in group)
        if len(value)>4000:raise ValueError('Text segment too long')
        text.append({'text':value,'bbox_points_top_origin':[min(x[0] for x in boxes),min(x[1] for x in boxes),max(x[2] for x in boxes),max(x[3] for x in boxes)],
                     'font_size_range_points':[min(sizes),max(sizes)],'fonts':sorted({str(w['fontname'])[:128] for w in group})})
    images=[bounds(x) for x in page.images]
    boxes=[x['bbox_points_top_origin'] for x in text]+images
    content=[min(x[0] for x in boxes),min(x[1] for x in boxes),max(x[2] for x in boxes),max(x[3] for x in boxes)] if boxes else None
    margins=[content[0]-l,content[1]-t,r-content[2],b-content[3]] if content else None
    return {'page':page.page_number,'page_bbox_points_top_origin':[l,t,r,b],
            'text_segments':text,'image_bounds':images,'vector_edge_count':len(page.edges),
            'text_image_content_bounds':content,'text_image_margins_ltrb_points':margins,
            'text_layer_present':bool(page.chars),'rotation_degrees':int(page.rotation),
            'reading_order_verified':False}

def analyze(raw,pages):
    return {'schema':'janus-pdf-layout-result-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'pages':inspect(raw,pages,page_layout),'visual_render_verified':False,
            'scope':'Text and image bounding boxes, text segments, fonts and estimated margins. Geometry only; no semantic reading order or visual quality verdict.'}
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    _,_,doc=validate(root,plan)
    if doc.stat().st_size>MAX_PDF_BYTES:raise ValueError('PDF exceeds byte limit')
    return plan,dict(s,scope='Inspect exact page layout geometry; no visual or reading-order verification.')
def execute(root,plan):
    s,dst,doc=validate(root,plan);r=analyze(guard.exact(doc,plan['guards'][1],MAX_PDF_BYTES),s['pages'])
    payload=json.dumps(r,ensure_ascii=True,allow_nan=False,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'layout_geometry_observed','output':plan['output'],'sha256':digest,
            'pages':len(r['pages']),'text_segments':sum(len(p['text_segments']) for p in r['pages']),'visual_render_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        limits();print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'PDF layout inspection unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
