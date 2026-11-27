"""Actual bounded PDF raster checks, not a general aesthetic quality verdict."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.pdf_diagrams import checked as pages_checked,inspect,limits,EXTRA,MAX_PDF_BYTES
SCHEMA='janus-pdf-visual-quality-v1'
DPI=96
MAX_PIXELS=4000000

def checked(s):
    if not isinstance(s,dict) or set(s)!={'document','pages','minimum_margin_points','allow_blank_pages'}:
        raise ValueError('Expected PDF, page list, minimum margin and blank-page policy')
    pages_checked({'document':s['document'],'pages':s['pages']})
    margin=s['minimum_margin_points']
    if type(margin) not in (int,float) or not math.isfinite(margin) or not 0<=margin<=72:
        raise ValueError('Margin must be 0–72 points')
    if type(s['allow_blank_pages']) is not bool:raise ValueError('Expected explicit blank-page policy')
    return s

def raster_metrics(image,margin,allow_blank):
    from PIL import Image,ImageChops
    rgb=image.convert('RGB')
    w,h=rgb.size
    if w<1 or h<1 or w*h>MAX_PIXELS:raise ValueError('Raster exceeds pixel budget')
    # Any RGB channel differing sufficiently from white counts as visible ink.
    delta=ImageChops.difference(rgb,Image.new('RGB',rgb.size,'white'))
    channels=delta.split()
    maximum=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2])
    mask=maximum.point(lambda n:255 if n>=24 else 0)
    box=mask.getbbox()
    count=mask.histogram()[255]
    warnings=[]
    margin_px=math.ceil(margin*DPI/72)
    if box:
        left,top,right,bottom=box
        margins=[left,top,w-right,h-bottom]
        if min(margins)<margin_px:warnings.append('visible_content_inside_requested_margin')
    else:
        margins=None
        if not allow_blank:warnings.append('blank_or_near_white_render')
    return {'raster_pixels':[w,h],'rgb_sha256':hashlib.sha256(rgb.tobytes()).hexdigest(),
            'visible_pixel_count':count,'visible_fraction':count/(w*h),
            'visible_bounds_pixels':list(box) if box else None,
            'visible_margins_ltrb_pixels':margins,'required_margin_pixels':margin_px,
            'warnings':warnings,'checks_passed':not warnings}

def render_page(page,margin,allow_blank):
    width,height=float(page.width),float(page.height)
    if not all(math.isfinite(n) and 0<n<=1440 for n in (width,height)):
        raise ValueError('Unsupported page dimensions')
    if math.ceil(width*DPI/72)*math.ceil(height*DPI/72)>MAX_PIXELS:
        raise ValueError('Requested page raster exceeds pixel budget')
    rendered=page.to_image(resolution=DPI,antialias=True,force_mediabox=False)
    try:
        return dict(raster_metrics(rendered.original,margin,allow_blank),page=page.page_number)
    finally:
        rendered.original.close()
        if rendered.annotated is not rendered.original:rendered.annotated.close()

def analyze(raw,s):
    checked(s)
    pages=inspect(raw,s['pages'],lambda page:render_page(page,s['minimum_margin_points'],s['allow_blank_pages']))
    return {'schema':'janus-pdf-visual-quality-result-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'dpi':DPI,'pages':pages,'selected_checks_passed':all(p['checks_passed'] for p in pages),
            'visual_raster_observed':True,'general_visual_quality_verified':False,
            'scope':'Actual selected-page raster checks: white-background visibility and requested ink margins. Full-bleed art may intentionally trigger margins; low-contrast content can be missed. No clipping, typography, contrast-accessibility or aesthetic guarantee.'}
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    _,_,doc=validate(root,plan)
    if doc.stat().st_size>MAX_PDF_BYTES:raise ValueError('PDF exceeds byte limit')
    return plan,dict(s,scope='Render selected pages locally; check visible ink margins and blank pages.')
def execute(root,plan):
    s,dst,doc=validate(root,plan);r=analyze(guard.exact(doc,plan['guards'][1],MAX_PDF_BYTES),s)
    payload=json.dumps(r,ensure_ascii=True,allow_nan=False,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'visual_raster_checks_completed','output':plan['output'],'sha256':digest,
            'pages':len(r['pages']),'selected_checks_passed':r['selected_checks_passed'],
            'general_visual_quality_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        limits();print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'PDF raster check unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
