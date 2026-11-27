"""Reviewed creation of editable, formatted Word documents using native OOXML."""
from __future__ import annotations
import argparse
import io
import json
from pathlib import Path
import sys
from xml.etree import ElementTree as ET
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import literal

SCHEMA='janus-word-document-v1'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
ET.register_namespace('w',W[1:-1])
THEMES={'navy':'24466B','graphite':'363B42','forest':'315C48'}
PAGES={'A4':(11906,16838),'Letter':(12240,15840)}
def checked(spec):
    if (not isinstance(spec,dict) or set(spec)!={'title','subtitle','theme','page_size','blocks'}
        or not isinstance(spec['theme'],str) or spec['theme'] not in THEMES
        or not isinstance(spec['page_size'],str) or spec['page_size'] not in PAGES):
        raise ValueError('Expected title, subtitle, theme, page size and document blocks')
    literal(spec['title'],200)
    if spec['subtitle']!='':literal(spec['subtitle'],300)
    blocks=spec['blocks']
    if not isinstance(blocks,list) or not 1<=len(blocks)<=500:raise ValueError('Expected bounded blocks')
    count=0;chars=0;level=0
    for block in blocks:
        if not isinstance(block,dict):raise ValueError('Invalid block')
        kind=block.get('type')
        if kind=='paragraph' and set(block)=={'type','text'}:
            texts=[literal(block['text'],10000)]
        elif kind=='heading' and set(block)=={'type','level','text'}:
            n=block['level']
            if type(n) is not int or not 1<=n<=3 or n>level+1:raise ValueError('Invalid heading hierarchy')
            level=n;texts=[literal(block['text'],200)]
        elif kind=='bullets' and set(block)=={'type','items'}:
            items=block['items']
            if not isinstance(items,list) or not 1<=len(items)<=100:raise ValueError('Invalid bullet list')
            texts=[literal(x,2000) for x in items]
        elif kind=='table' and set(block)=={'type','headers','rows'}:
            headers=block['headers'];rows=block['rows']
            if (not isinstance(headers,list) or not 1<=len(headers)<=8 or not isinstance(rows,list)
                or not 1<=len(rows)<=100):raise ValueError('Invalid table dimensions')
            texts=[literal(x,150) for x in headers]
            if len(set(headers))!=len(headers):raise ValueError('Duplicate table headers')
            for row in rows:
                if not isinstance(row,list) or len(row)!=len(headers):raise ValueError('Nonrectangular table')
                texts.extend(literal(x,2000) if x!='' else '' for x in row)
        else:raise ValueError('Unsupported document block')
        count+=len(texts);chars+=sum(map(len,texts))
    if count>4000 or chars>200000:raise ValueError('Document content exceeds bounds')
    return spec

def el(parent,name,**attrs):
    return ET.SubElement(parent,W+name,{W+k:str(v) for k,v in attrs.items()})
def serialize(node):return ET.tostring(node,encoding='utf-8',xml_declaration=True)
def para(parent,text,style):
    p=el(parent,'p');props=el(p,'pPr');el(props,'pStyle',val=style)
    if style=='ListBullet':
        num=el(props,'numPr');el(num,'ilvl',val=0);el(num,'numId',val=1)
    run=el(p,'r');t=el(run,'t');t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');t.text=text
    return p

def styles(color):
    root=ET.Element(W+'styles')
    specs=[('Normal','Normal',22,'252A30',False,0,120,None),
           ('Title','Title',52,color,True,0,180,None),
           ('Subtitle','Subtitle',26,'59636D',False,0,240,None),
           ('Heading1','heading 1',34,color,True,280,120,0),
           ('Heading2','heading 2',28,color,True,220,100,1),
           ('Heading3','heading 3',24,color,True,180,80,2),
           ('ListBullet','List Bullet',22,'252A30',False,0,80,None),
           ('TableHeader','Table Header',20,'FFFFFF',True,0,60,None),
           ('TableBody','Table Body',20,'252A30',False,0,60,None)]
    for key,name,size,ink,bold,before,after,outline in specs:
        s=el(root,'style',type='paragraph',styleId=key,**({'default':'1'} if key=='Normal' else {}))
        el(s,'name',val=name)
        if key!='Normal':el(s,'basedOn',val='Normal');el(s,'next',val='Normal')
        el(s,'qFormat');p=el(s,'pPr')
        if key in ('Title','Subtitle') or outline is not None:el(p,'keepNext')
        el(p,'spacing',before=before,after=after,line=276,lineRule='auto')
        if outline is not None:el(p,'outlineLvl',val=outline)
        r=el(s,'rPr');el(r,'rFonts',ascii='Calibri',hAnsi='Calibri',eastAsia='Calibri',cs='Calibri')
        if bold:el(r,'b')
        el(r,'color',val=ink);el(r,'sz',val=size);el(r,'szCs',val=size)
    return root
def numbering():
    root=ET.Element(W+'numbering');abstract=el(root,'abstractNum',abstractNumId=0)
    el(abstract,'multiLevelType',val='singleLevel');lvl=el(abstract,'lvl',ilvl=0)
    el(lvl,'start',val=1);el(lvl,'numFmt',val='bullet');el(lvl,'lvlText',val='•');el(lvl,'lvlJc',val='left')
    p=el(lvl,'pPr');tabs=el(p,'tabs');el(tabs,'tab',val='num',pos=360);el(p,'ind',left=360,hanging=180)
    num=el(root,'num',numId=1);el(num,'abstractNumId',val=0)
    return root
def table(parent,block,width,color):
    tbl=el(parent,'tbl');pr=el(tbl,'tblPr');el(pr,'tblW',w=width,type='dxa')
    borders=el(pr,'tblBorders')
    for name in ('top','left','bottom','right','insideH','insideV'):el(borders,name,val='single',sz=4,color='CED6DE')
    el(pr,'tblLayout',type='fixed');grid=el(tbl,'tblGrid')
    n=len(block['headers']);widths=[width//n]*n;widths[-1]+=width-sum(widths)
    for w in widths:el(grid,'gridCol',w=w)
    for i,row in enumerate([block['headers'],*block['rows']]):
        tr=el(tbl,'tr');trpr=el(tr,'trPr')
        if i==0:el(trpr,'tblHeader')
        for j,value in enumerate(row):
            cell=el(tr,'tc');tcpr=el(cell,'tcPr');el(tcpr,'tcW',w=widths[j],type='dxa')
            if i==0 or i%2==0:el(tcpr,'shd',val='clear',color='auto',fill=color if i==0 else 'F0F3F6')
            para(cell,value,'TableHeader' if i==0 else 'TableBody')
    return tbl

CONTENT_TYPES='''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
</Types>'''
ROOT_RELS='''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''
DOC_RELS='''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
</Relationships>'''

def render(spec):
    color=THEMES[spec['theme']];width,height=PAGES[spec['page_size']]
    doc=ET.Element(W+'document');body=el(doc,'body');expected=[]
    def add(text,style):
        para(body,text,style);expected.append((text,style))
    add(spec['title'],'Title')
    if spec['subtitle']:add(spec['subtitle'],'Subtitle')
    tables=0;bullets=0
    for block in spec['blocks']:
        kind=block['type']
        if kind=='heading':add(block['text'],'Heading'+str(block['level']))
        elif kind=='paragraph':add(block['text'],'Normal')
        elif kind=='bullets':
            for item in block['items']:add(item,'ListBullet');bullets+=1
        else:
            table(body,block,width-2880,color);tables+=1
            for i,row in enumerate([block['headers'],*block['rows']]):
                expected.extend((value,'TableHeader' if i==0 else 'TableBody') for value in row)
    sect=el(body,'sectPr');el(sect,'pgSz',w=width,h=height)
    el(sect,'pgMar',top=1440,right=1440,bottom=1440,left=1440,header=720,footer=720,gutter=0)
    parts={'[Content_Types].xml':CONTENT_TYPES,'_rels/.rels':ROOT_RELS,
           'word/document.xml':serialize(doc),'word/styles.xml':serialize(styles(color)),
           'word/numbering.xml':serialize(numbering()),'word/_rels/document.xml.rels':DOC_RELS}
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in parts.items():z.writestr(name,data)
    payload=stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(parts):raise ValueError('Invalid DOCX package')
        parsed={name:ET.fromstring(z.read(name)) for name in parts}
        b=parsed['word/document.xml'].find(W+'body')
        actual=[(''.join(t.text or '' for t in p.iter(W+'t')),p.find(W+'pPr/'+W+'pStyle').get(W+'val')) for p in b.iter(W+'p')]
        known={s.get(W+'styleId') for s in parsed['word/styles.xml'].findall(W+'style')}
        if (actual!=expected or not {s for _,s in actual}<=known or len(b.findall(W+'tbl'))!=tables
            or len(list(b.iter(W+'numId')))!=bullets or b.find(W+'sectPr/'+W+'pgSz').attrib!={W+'w':str(width),W+'h':str(height)}):
            raise ValueError('Word content or formatting structure verification failed')
    return payload,{'paragraphs':len(expected),'tables':tables,'bullet_items':bullets}

def review(root,source,output,exclude=()):
    return guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.docx')
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.docx')
def execute(root,plan):
    spec,dst,_=validate(root,plan);payload,counts=render(spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-word-document-result-v1','status':'word_structure_verified','output':plan['output'],'sha256':sha,
            **counts,'source_unchanged':True,'visual_render_verified':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Word document unavailable; inspect reviewed blocks and output limits'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
