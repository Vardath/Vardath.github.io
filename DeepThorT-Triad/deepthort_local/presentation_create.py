"""Create editable PPTX slides from bounded typed content, with conservative layouts."""
from __future__ import annotations
import argparse
import io
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.presentation_edit import literal,package,slide_parts

SCHEMA='janus-presentation-create-v1'
THEMES={'navy':('183A56','F4F7FA','192834','4F7189'),
        'graphite':('35404A','F7F8FA','18232D','697D8B'),
        'forest':('27584B','F3F7F4','19382F','628B75')}

def bounded(value,length):
    if len(literal(value))>length:raise ValueError('Text exceeds conservative slide layout budget')
    return value

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'theme','slides'} or spec['theme'] not in THEMES or not isinstance(spec['slides'],list) or not 1<=len(spec['slides'])<=40:
        raise ValueError('Expected theme and 1 to 40 slides')
    slides=[]
    for slide in spec['slides']:
        if not isinstance(slide,dict) or set(slide)!={'layout','title','body'}:
            raise ValueError('Invalid slide specification')
        layout=slide['layout'];title=bounded(slide['title'],75);body=slide['body']
        if layout=='title':
            if not isinstance(body,list) or len(body)>2:raise ValueError('Title slide supports up to two subtitle lines')
            content=[bounded(x,100) for x in body]
        elif layout=='bullets':
            if not isinstance(body,list) or not 1<=len(body)<=5:raise ValueError('Bullet slide supports 1 to 5 points')
            content=[bounded(x,110) for x in body]
        elif layout=='two_columns':
            if not isinstance(body,list) or len(body)!=2:raise ValueError('Two-column slide requires two columns')
            content=[]
            for column in body:
                if not isinstance(column,dict) or set(column)!={'heading','points'} or not isinstance(column['points'],list) or not 1<=len(column['points'])<=4:
                    raise ValueError('Invalid slide column')
                content.append({'heading':bounded(column['heading'],45),'points':[bounded(x,65) for x in column['points']]})
        else:raise ValueError('Unsupported slide layout')
        slides.append({'layout':layout,'title':title,'body':content})
    return {'theme':spec['theme'],'slides':slides}

def create(spec):
    import pptx
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR
    from pptx.util import Inches,Pt
    if pptx.__version__!='1.0.2':raise ValueError('Install pinned presentation tools first')
    accent,paper,ink,muted=THEMES[spec['theme']]
    prs=Presentation();prs.slide_width=Inches(13.333333);prs.slide_height=Inches(7.5)
    expected=[]
    def rgb(v):return RGBColor.from_string(v)
    def rect(slide,x,y,w,h,color):
        s=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
        s.fill.solid();s.fill.fore_color.rgb=rgb(color);s.line.fill.background()
    def textbox(slide,x,y,w,h,text,size,color,bold=False):
        s=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
        tf=s.text_frame;tf.clear();tf.word_wrap=True;tf.margin_left=Pt(0);tf.margin_right=Pt(0)
        tf.margin_top=Pt(0);tf.margin_bottom=Pt(0);tf.vertical_anchor=MSO_ANCHOR.TOP
        p=tf.paragraphs[0];r=p.add_run();r.text=text
        r.font.name='Calibri';r.font.size=Pt(size);r.font.bold=bold;r.font.color.rgb=rgb(color)
        return s
    for i,item in enumerate(spec['slides'],1):
        slide=prs.slides.add_slide(prs.slide_layouts[6]);slide.background.fill.solid()
        slide.background.fill.fore_color.rgb=rgb(accent if item['layout']=='title' else paper)
        texts=[]
        def put(x,y,w,h,t,size,color,bold=False):
            textbox(slide,x,y,w,h,t,size,color,bold);texts.append(t)
        if item['layout']=='title':
            rect(slide,.8,1.3,.12,3.3,'FFFFFF')
            put(1.2,1.45,11.1,2.15,item['title'],38,'FFFFFF',True)
            for k,line in enumerate(item['body']):put(1.24,3.9+k*.65,10.5,.6,line,21,'FFFFFF')
        else:
            rect(slide,0,0,13.33,.12,accent)
            put(.7,.55,12,1.05,item['title'],30,accent,True)
            if item['layout']=='bullets':
                for k,point in enumerate(item['body']):
                    rect(slide,.86,1.82+k*.91,.10,.10,accent)
                    put(1.15,1.64+k*.91,11.2,.88,point,21,ink)
            else:
                for k,column in enumerate(item['body']):
                    x=.7+k*6.18
                    rect(slide,x,1.7,5.85,.065,muted)
                    put(x,1.94,5.85,.62,column['heading'],21,accent,True)
                    for n,point in enumerate(column['points']):
                        rect(slide,x+.1,2.83+n*.89,.08,.08,muted)
                        put(x+.35,2.66+n*.89,5.45,.86,point,18,ink)
        put(12.05,7.03,.75,.3,str(i),11,'FFFFFF' if item['layout']=='title' else muted)
        expected.append(texts)
    stream=io.BytesIO();prs.save(stream);payload=stream.getvalue()
    actual=Presentation(io.BytesIO(payload))
    if len(actual.slides)!=len(expected) or actual.slide_width!=prs.slide_width or actual.slide_height!=prs.slide_height:
        raise ValueError('Reopened slide count or size mismatch')
    for slide,texts in zip(actual.slides,expected):
        if [s.text for s in slide.shapes if s.has_text_frame and s.text]!=texts:
            raise ValueError('Reopened slide text mismatch')
        if any(s.left<0 or s.top<0 or s.left+s.width>actual.slide_width or s.top+s.height>actual.slide_height for s in slide.shapes):
            raise ValueError('Slide shape outside page bounds')
    if len(slide_parts(package(payload)))!=len(expected):raise ValueError('Slide package verification failed')
    return payload

def review(root,source,output,exclude=()):
    return guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.pptx')
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.pptx')
def execute(root,plan):
    spec,dst,_=validate(root,plan);payload=create(spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-presentation-create-result-v1','status':'presentation_structure_verified','output':plan['output'],
            'sha256':sha,'slides':len(spec['slides']),'editable_text':True,'visual_render_verified':False,'text_fit_verified':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(768*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Presentation creation unavailable; inspect typed slide specification and installed tools'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
