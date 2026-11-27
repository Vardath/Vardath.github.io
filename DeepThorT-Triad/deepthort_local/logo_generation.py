"""Reviewed editable vector logos from explicit bounded geometric designs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import literal

SCHEMA='janus-logo-generation-v1'
SVG='{http://www.w3.org/2000/svg}'
ET.register_namespace('',SVG[1:-1])
COLOR=re.compile(r'#[0-9a-fA-F]{6}\Z')
FONTS={'sans':'Arial, sans-serif','serif':'Georgia, serif','mono':'monospace'}
FIELDS={
    'rect':{'x','y','width','height','radius','fill'},
    'circle':{'cx','cy','radius','fill'},
    'polygon':{'points','fill'},
    'text':{'x','y','text','size','family','weight','anchor','fill'},
}
def color(v):
    if not isinstance(v,str) or not COLOR.fullmatch(v):raise ValueError('Use literal six-digit hex RGB colors')
    return v
def integer(v,a,b):
    if type(v) is not int or not a<=v<=b:raise ValueError('Invalid integer geometry')
    return v
def checked(s):
    if not isinstance(s,dict) or set(s)!={'title','width','height','background','elements'}:
        raise ValueError('Expected title, canvas, optional background and ordered elements')
    literal(s['title'],100)
    w,h=integer(s['width'],64,2048),integer(s['height'],64,2048)
    if s['background'] is not None:color(s['background'])
    if not isinstance(s['elements'],list) or not 1<=len(s['elements'])<=32:
        raise ValueError('Choose 1–32 editable vector elements')
    for e in s['elements']:
        if not isinstance(e,dict) or not isinstance(e.get('kind'),str) or e['kind'] not in FIELDS or set(e)!=FIELDS[e['kind']]|{'kind'}:
            raise ValueError('Unsupported vector element or fields')
        color(e['fill']);k=e['kind']
        if k=='rect':
            x,y=integer(e['x'],0,w-1),integer(e['y'],0,h-1)
            ew,eh=integer(e['width'],1,w-x),integer(e['height'],1,h-y)
            integer(e['radius'],0,min(ew,eh)//2)
        elif k=='circle':
            x,y=integer(e['cx'],1,w-1),integer(e['cy'],1,h-1)
            integer(e['radius'],1,min(x,y,w-x,h-y))
        elif k=='polygon':
            pts=e['points']
            if not isinstance(pts,list) or not 3<=len(pts)<=24:raise ValueError('Choose 3–24 polygon points')
            for p in pts:
                if not isinstance(p,list) or len(p)!=2:raise ValueError('Expected coordinate pair')
                integer(p[0],0,w);integer(p[1],0,h)
            if len({tuple(p) for p in pts})!=len(pts) or sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(pts,pts[1:]+pts[:1]))==0:
                raise ValueError('Repeated points or zero-area polygon')
        else:
            integer(e['x'],0,w);size=integer(e['size'],8,min(w,h))
            integer(e['y'],size,h)
            literal(e['text'],60)
            if e['family'] not in FONTS or e['weight'] not in ('normal','bold') or e['anchor'] not in ('start','middle','end'):
                raise ValueError('Invalid wordmark typography')
    return s

def generate(s):
    checked(s);w,h=s['width'],s['height']
    root=ET.Element(SVG+'svg',{'width':str(w),'height':str(h),'viewBox':f'0 0 {w} {h}','role':'img','aria-labelledby':'logo-title'})
    ET.SubElement(root,SVG+'title',{'id':'logo-title'}).text=s['title']
    if s['background'] is not None:
        ET.SubElement(root,SVG+'rect',{'x':'0','y':'0','width':str(w),'height':str(h),'fill':s['background']})
    expected=[]
    for e in s['elements']:
        k=e['kind'];attrs={'fill':e['fill']}
        if k=='rect':attrs.update({x:str(e[x]) for x in ('x','y','width','height')},rx=str(e['radius']))
        elif k=='circle':attrs.update(cx=str(e['cx']),cy=str(e['cy']),r=str(e['radius']))
        elif k=='polygon':attrs['points']=' '.join(f'{x},{y}' for x,y in e['points'])
        else:
            attrs.update({'x':str(e['x']),'y':str(e['y']),'font-size':str(e['size']),
                          'font-family':FONTS[e['family']],'font-weight':e['weight'],'text-anchor':e['anchor']})
        node=ET.SubElement(root,SVG+k,attrs)
        if k=='text':node.text=e['text']
        expected.append((SVG+k,attrs,node.text))
    payload=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    parsed=ET.fromstring(payload)
    offset=2 if s['background'] is not None else 1
    if parsed.tag!=SVG+'svg' or parsed.attrib!=root.attrib or parsed[0].text!=s['title'] or [(n.tag,n.attrib,n.text) for n in list(parsed)[offset:]]!=expected:
        raise ValueError('SVG element verification failed')
    return payload,{'width':w,'height':h,'elements':len(expected),'transparent_background':s['background'] is None,
                    'geometry_verified':True,'visual_render_verified':False,'font_fit_verified':False,'trademark_clearance_verified':False}

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.svg')
    _,r=generate(s)
    return plan,dict(s,verification=r,scope='Editable geometric SVG. Text may render differently across fonts; inspect actual logo.')
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.svg')
def execute(root,plan):
    s,dst,_=validate(root,plan);payload,r=generate(s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-logo-result-v1','status':'logo_elements_verified','output':plan['output'],'sha256':sha,
            **r,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Logo unavailable; inspect bounded design specification'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
