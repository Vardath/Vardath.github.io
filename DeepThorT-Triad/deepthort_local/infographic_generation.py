"""Editable structured fact-card infographics; supplied facts, not invented research."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import textwrap
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import literal
from deepthort_local.logo_generation import SVG,color

SCHEMA='janus-infographic-generation-v1'
W=960
def lines(text,limit,max_lines):
    result=textwrap.wrap(text,width=limit,break_long_words=True,break_on_hyphens=False)
    if not 1<=len(result)<=max_lines:raise ValueError('Text exceeds infographic layout budget')
    return result
def checked(s):
    if not isinstance(s,dict) or set(s)!={'title','subtitle','accent','facts','source_note'}:
        raise ValueError('Expected title, subtitle, accent, supplied fact cards and source note')
    literal(s['title'],60);literal(s['subtitle'],100);literal(s['source_note'],150);color(s['accent'])
    lines(s['title'],38,2);lines(s['subtitle'],76,2);lines(s['source_note'],100,2)
    facts=s['facts']
    if not isinstance(facts,list) or not 2<=len(facts)<=8:raise ValueError('Choose 2–8 fact cards')
    for f in facts:
        if not isinstance(f,dict) or set(f)!={'label','value','detail'}:raise ValueError('Invalid fact card')
        literal(f['label'],48);literal(f['value'],18);literal(f['detail'],130)
        lines(f['label'],32,2);lines(f['detail'],43,4)
    return s

def generate(s):
    checked(s);rows=(len(s['facts'])+1)//2;h=210+rows*190+88
    root=ET.Element(SVG+'svg',{'width':str(W),'height':str(h),'viewBox':f'0 0 {W} {h}','role':'img','aria-labelledby':'infographic-title infographic-desc'})
    ET.SubElement(root,SVG+'title',{'id':'infographic-title'}).text=s['title']
    ET.SubElement(root,SVG+'desc',{'id':'infographic-desc'}).text=s['subtitle']
    def rect(x,y,w,height,fill,rx=0):
        return ET.SubElement(root,SVG+'rect',{'x':str(x),'y':str(y),'width':str(w),'height':str(height),'fill':fill,'rx':str(rx)})
    expected=[]
    def text(role,index,x,y,content,size,fill,weight='normal'):
        attrs={'x':str(x),'y':str(y),'font-family':'Arial, sans-serif','font-size':str(size),'fill':fill,
               'font-weight':weight,'data-role':role,'data-card':str(index)}
        n=ET.SubElement(root,SVG+'text',attrs);n.text=content
        expected.append((role,str(index),content))
    rect(0,0,W,h,'#f4f6f8');rect(0,0,W,12,s['accent'])
    for i,t in enumerate(lines(s['title'],38,2)):text('title',-1,48,61+i*42,t,35,'#182330','bold')
    for i,t in enumerate(lines(s['subtitle'],76,2)):text('subtitle',-1,48,151+i*23,t,18,'#435064')
    for i,f in enumerate(s['facts']):
        x=48+(i%2)*444;y=210+(i//2)*190
        rect(x,y,420,174,'#ffffff',12);rect(x,y,6,174,s['accent'],3)
        for j,t in enumerate(lines(f['label'],32,2)):text('label',i,x+24,y+25+j*20,t,16,'#435064','bold')
        text('value',i,x+24,y+81,f['value'],30,'#182330','bold')
        for j,t in enumerate(lines(f['detail'],43,4)):text('detail',i,x+24,y+104+j*18,t,14,'#435064')
    for i,t in enumerate(lines(s['source_note'],100,2)):text('source',-1,48,210+rows*190+26+i*18,t,13,'#435064')
    payload=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    parsed=ET.fromstring(payload)
    actual=[(n.get('data-role'),n.get('data-card'),n.text) for n in parsed if n.tag==SVG+'text']
    if parsed.tag!=SVG+'svg' or parsed.attrib!=root.attrib or actual!=expected or parsed[0].text!=s['title'] or parsed[1].text!=s['subtitle']:
        raise ValueError('Infographic text verification failed')
    return payload,{'width':W,'height':h,'facts':len(s['facts']),'text_elements':len(actual),'exact_layout_text_verified':True,
                    'source_claims_verified':False,'visual_render_verified':False,'font_fit_verified':False}
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.svg')
    _,r=generate(s)
    return plan,dict(s,verification=r,scope='Editable infographic from supplied claims. No independent research or visual acceptance.')
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.svg')
def execute(root,plan):
    s,dst,_=validate(root,plan);payload,r=generate(s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-infographic-result-v1','status':'infographic_text_verified','output':plan['output'],'sha256':sha,
            **r,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Infographic unavailable; inspect supplied facts and layout bounds'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
