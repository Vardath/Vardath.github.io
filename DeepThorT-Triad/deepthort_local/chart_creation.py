"""Create editable, standalone vector charts from exact reviewed CSV data."""
from __future__ import annotations
import argparse
from decimal import Decimal,localcontext
import hashlib
import json
from pathlib import Path
import sys
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.csv_processing import parse,DELIMITERS
from deepthort_local.data_transformation import numeric
from deepthort_local.long_form_writing import literal

SCHEMA='janus-chart-creation-v1'
EXTRA=('csv','.csv')
SVG='{http://www.w3.org/2000/svg}'
PALETTE=('#245e9e','#b55524','#24826a','#7854a3')
WIDTH=1000;HEIGHT=620;LEFT=110;RIGHT=940;TOP=110;BOTTOM=475
ET.register_namespace('',SVG[1:-1])

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'csv','delimiter','type','title','x','series','y_label'}:
        raise ValueError('Expected CSV, delimiter, chart type, title, x, series and y label')
    if not isinstance(spec['csv'],str) or not isinstance(spec['delimiter'],str) or spec['delimiter'] not in DELIMITERS or spec['type'] not in ('bar','line','scatter'):
        raise ValueError('Unsupported chart type or CSV delimiter')
    literal(spec['title'],100);literal(spec['x'],80);literal(spec['y_label'],80)
    series=spec['series']
    if not isinstance(series,list) or not 1<=len(series)<=4:raise ValueError('Select 1–4 series')
    for s in series:literal(s,60)
    if len(set(series))!=len(series) or spec['x'] in series:raise ValueError('Chart columns must be distinct')
    return spec

def dataset(raw,spec):
    headers,rows=parse(raw,spec['delimiter'])
    limit=40 if spec['type']=='bar' else 300
    if not 1<=len(rows)<=limit:raise ValueError('Chart row count exceeds type bound; project the CSV first')
    try:xi=headers.index(spec['x']);yi=[headers.index(s) for s in spec['series']]
    except ValueError as exc:raise ValueError('Selected chart column missing') from exc
    x=[r[xi] for r in rows]
    for value in x:
        if spec['type']=='scatter':numeric(value)
        else:literal(value,80)
    if spec['type']!='scatter' and len(set(x))!=len(x):
        raise ValueError('Category labels must be unique; aggregate explicitly first')
    values=[[r[i] for r in rows] for i in yi]
    for series in values:
        for v in series:numeric(v)
    return {'x':x,'series':dict(zip(spec['series'],values))}

def domain(values,zero=False):
    a=min(values);b=max(values)
    if zero:a=min(a,Decimal(0));b=max(b,Decimal(0))
    if a==b:
        pad=abs(a)*Decimal('.1') if a else Decimal(1);a-=pad;b+=pad
        if zero and min(values)>=0:a=Decimal(0)
    return a,b

def ticks(a,b):
    return [a+(b-a)*Decimal(i)/Decimal(5) for i in range(6)]
def fmt(v):
    if not v:return '0'
    # Keep small and large values legible; coordinates retain full decimal arithmetic.
    if abs(v)>=Decimal('1e7') or abs(v)<Decimal('.001'):
        return format(v,'.3E')
    return format(v,'.6g')
def coord(v):return format(v.quantize(Decimal('.001')),'f')
def element(parent,name,**attrs):
    return ET.SubElement(parent,SVG+name,{k.replace('_','-'):str(v) for k,v in attrs.items()})
def label(parent,x,y,text,**kw):
    node=element(parent,'text',x=x,y=y,**kw);node.text=text;return node
def mark(parent,kind,series,index,x_value,y_value,**attrs):
    return element(parent,kind,data_series=series,data_row=index,data_x=x_value,data_y=y_value,**attrs)

def render_data(data,spec):
    with localcontext() as ctx:
        ctx.prec=50
        return _render_data(data,spec)

def _render_data(data,spec):
    x=data['x'];series=spec['series'];kind=spec['type']
    ys={s:[numeric(v) for v in data['series'][s]] for s in series}
    lo,hi=domain([v for values in ys.values() for v in values],kind=='bar')
    def y(v):return coord(Decimal(BOTTOM)-(v-lo)*Decimal(BOTTOM-TOP)/(hi-lo))
    if kind=='scatter':
        xs=[numeric(v) for v in x];xl,xh=domain(xs)
        def xp(i):return Decimal(LEFT)+(xs[i]-xl)*Decimal(RIGHT-LEFT)/(xh-xl)
    else:
        step=Decimal(RIGHT-LEFT)/Decimal(len(x))
        def xp(i):return Decimal(LEFT)+step*(Decimal(i)+Decimal('.5'))
    root=ET.Element(SVG+'svg',{'width':str(WIDTH),'height':str(HEIGHT),'viewBox':f'0 0 {WIDTH} {HEIGHT}','role':'img','aria-labelledby':'chart-title chart-desc'})
    element(root,'title',id='chart-title').text=spec['title']
    element(root,'desc',id='chart-desc').text=kind.capitalize()+' chart. '+spec['x']+' versus '+spec['y_label']+'. Exact literal values on data marks.'
    element(root,'rect',x=0,y=0,width=WIDTH,height=HEIGHT,fill='#ffffff')
    g=element(root,'g',font_family='Arial, sans-serif',font_size=14,fill='#243142')
    label(g,LEFT,44,spec['title'],font_size=25,font_weight='bold')
    for v in ticks(lo,hi):
        pos=y(v);element(g,'line',x1=LEFT,y1=pos,x2=RIGHT,y2=pos,stroke='#dbe2ea')
        label(g,LEFT-12,coord(Decimal(pos)+4),fmt(v),text_anchor='end')
    element(g,'line',x1=LEFT,y1=TOP,x2=LEFT,y2=BOTTOM,stroke='#64748b')
    element(g,'line',x1=LEFT,y1=BOTTOM,x2=RIGHT,y2=BOTTOM,stroke='#64748b')
    if kind=='bar':
        zero=Decimal(y(Decimal(0)));element(g,'line',x1=LEFT,y1=zero,x2=RIGHT,y2=zero,stroke='#64748b')
    if kind=='scatter':
        for v in ticks(xl,xh):
            pos=coord(Decimal(LEFT)+(v-xl)*Decimal(RIGHT-LEFT)/(xh-xl))
            element(g,'line',x1=pos,y1=BOTTOM,x2=pos,y2=BOTTOM+6,stroke='#64748b')
            label(g,pos,BOTTOM+24,fmt(v),text_anchor='middle',font_size=12)
    else:
        stride=max(1,(len(x)+9)//10)
        for i in range(0,len(x),stride):
            short=x[i] if len(x[i])<=12 else x[i][:11]+'…'
            node=label(g,coord(xp(i)),BOTTOM+24,short,text_anchor='middle',font_size=12)
            element(node,'title').text=x[i]
    label(g,(LEFT+RIGHT)//2,BOTTOM+58,spec['x'],text_anchor='middle',font_weight='bold')
    label(g,24,(TOP+BOTTOM)//2,spec['y_label'],text_anchor='middle',transform=f'rotate(-90 24 {(TOP+BOTTOM)//2})',font_weight='bold')
    for j,s in enumerate(series):
        color=PALETTE[j];marks=element(g,'g',id='series-'+str(j))
        if kind=='line' and len(x)>1:
            element(marks,'polyline',points=' '.join(coord(xp(i))+','+y(v) for i,v in enumerate(ys[s])),fill='none',stroke=color,stroke_width=2.5)
        for i,v in enumerate(ys[s]):
            if kind=='bar':
                bw=step*Decimal('.75')/Decimal(len(series))
                center=xp(i)+(Decimal(j)-Decimal(len(series)-1)/2)*bw
                yy=Decimal(y(v));top=min(yy,zero);h=abs(yy-zero)
                node=mark(marks,'rect',s,i,x[i],data['series'][s][i],x=coord(center-bw*Decimal('.43')),y=coord(top),
                          width=coord(bw*Decimal('.86')),height=coord(h),fill=color)
            else:
                node=mark(marks,'circle',s,i,x[i],data['series'][s][i],cx=coord(xp(i)),cy=y(v),r=4,fill=color)
            element(node,'title').text=s+': '+x[i]+' = '+data['series'][s][i]
        lx=LEFT+(j%2)*420;ly=568+(j//2)*24
        element(g,'rect',x=lx,y=ly-11,width=15,height=15,fill=color)
        label(g,lx+23,ly+1,s if len(s)<=40 else s[:39]+'…')
    payload=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    parsed=ET.fromstring(payload)
    actual=[(n.get('data-series'),n.get('data-row'),n.get('data-x'),n.get('data-y')) for n in parsed.iter() if n.get('data-series') is not None]
    expected=[(s,str(i),x[i],data['series'][s][i]) for s in series for i in range(len(x))]
    if actual!=expected or parsed.tag!=SVG+'svg':raise ValueError('Chart mark verification failed')
    return payload,{'chart_type':kind,'rows':len(x),'series':len(series),'marks':len(actual),
                    'y_domain':[str(lo),str(hi)],'category_labels_sampled':kind!='scatter' and len(x)>10}
def render(raw,spec):return render_data(dataset(raw,spec),spec)
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.svg',extra=EXTRA)
    _,_,path=validate(root,plan);data=dataset(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    return plan,dict(spec,exact_chart_data=data)
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.svg',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);payload,receipt=render(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-chart-result-v1','status':'chart_marks_verified','output':plan['output'],'sha256':sha,
        **receipt,'source_unchanged':True,'visual_render_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Chart unavailable; inspect selected columns, decimal values and bounds'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
