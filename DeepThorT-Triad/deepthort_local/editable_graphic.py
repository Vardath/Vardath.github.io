"""Reviewed editable graphic design with named, independent SVG groups."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import sys
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.logo_generation import SVG,checked as check_logo,generate as generate_logo
from deepthort_local.long_form_writing import literal

SCHEMA='janus-editable-graphic-v1'

def checked(s):
    if not isinstance(s,dict) or set(s)!={'title','width','height','background','groups'}:
        raise ValueError('Expected canvas and ordered editable groups')
    groups=s['groups']
    if not isinstance(groups,list) or not 1<=len(groups)<=12:
        raise ValueError('Choose 1–12 groups')
    names=set();count=0
    for g in groups:
        if not isinstance(g,dict) or set(g)!={'name','visible','opacity','elements'}:
            raise ValueError('Invalid graphic group')
        literal(g['name'],80)
        if not g['name'].strip() or g['name'].casefold() in names:
            raise ValueError('Choose unique group names')
        names.add(g['name'].casefold())
        if type(g['visible']) is not bool or type(g['opacity']) is not int or not 0<=g['opacity']<=100:
            raise ValueError('Invalid group opacity or visibility')
        check_logo({k:s[k] for k in ('title','width','height','background')}|{'elements':g['elements']})
        count+=len(g['elements'])
    if count>64:raise ValueError('At most 64 total vector elements')
    return s

def generate(s):
    checked(s)
    base={k:s[k] for k in ('title','width','height','background')}
    w,h=s['width'],s['height']
    root=ET.Element(SVG+'svg',{'width':str(w),'height':str(h),'viewBox':f'0 0 {w} {h}',
        'role':'img','aria-labelledby':'design-title'})
    ET.SubElement(root,SVG+'title',{'id':'design-title'}).text=s['title']
    if s['background'] is not None:
        ET.SubElement(root,SVG+'rect',{'id':'background','x':'0','y':'0','width':str(w),'height':str(h),'fill':s['background']})
    for i,g in enumerate(s['groups']):
        node=ET.SubElement(root,SVG+'g',{'id':f'group-{i+1}','aria-label':g['name'],
             'display':'inline' if g['visible'] else 'none','opacity':format(g['opacity']/100,'.2f')})
        ET.SubElement(node,SVG+'title').text=g['name']
        raw,_=generate_logo(dict(base,background=None,elements=g['elements']))
        for j,element in enumerate(list(ET.fromstring(raw))[1:]):
            element.set('id',f'group-{i+1}-element-{j+1}')
            node.append(copy.deepcopy(element))
    payload=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    def signature(n):
        return n.tag,n.attrib,n.text,[signature(c) for c in n]
    if signature(ET.fromstring(payload))!=signature(root):
        raise ValueError('Editable vector structure changed')
    return payload,{'width':w,'height':h,'groups':len(s['groups']),
        'elements':sum(len(g['elements']) for g in s['groups']),
        'editable_groups_verified':True,'visual_render_verified':False,'font_fit_verified':False,
        'external_editor_acceptance_verified':False}

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.svg')

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.svg')
    _,r=generate(s)
    return plan,dict(s,verification=r,scope='Editable SVG groups; external editor and rendered layout not verified.')

def execute(root,plan):
    s,dst,_=validate(root,plan);payload,r=generate(s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-editable-graphic-result-v1','status':'editable_groups_verified',
        'output':plan['output'],'sha256':sha,'source_unchanged':True,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed graphic design or source'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
