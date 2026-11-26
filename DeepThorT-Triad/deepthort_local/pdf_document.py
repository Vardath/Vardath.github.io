"""Bounded, reviewed PDF document production from typed JSON; no executable markup."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from xml.sax.saxutils import escape

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local.action_guards import snapshot_file
from deepthort_local.pdf_page_edit import target,MAX_OUTPUT
from deepthort_local.pdf_knowledge_worker import PARSER_VERSION,MAX_PAGES
from deepthort_local.source_security import exclusions,excluded,linked
from deepthort_local.disk_gate import require_storage
from deepthort_local.structured_source import strict_json

SCHEMA='janus-pdf-document-v1'
REPORTLAB_VERSION='4.4.3'
MAX_SPEC=100000

def text(value,limit):
    if not isinstance(value,str) or not value.strip() or len(value)>limit:
        raise ValueError('Invalid document text length')
    if any(ord(c)<32 or ord(c)==127 for c in value):
        raise ValueError('Use separate blocks instead of embedded control characters')
    try:value.encode('cp1252')
    except UnicodeEncodeError as exc:raise ValueError('Initial PDF producer supports Western Latin text only') from exc
    return ' '.join(value.split())

def checked(data):
    if not isinstance(data,dict) or set(data)!={'title','subtitle','theme','page_size','blocks'}:
        raise ValueError('Expected title, subtitle, theme, page_size and blocks')
    if data['theme'] not in ('navy','graphite','forest') or data['page_size'] not in ('A4','Letter'):
        raise ValueError('Unsupported document theme or page size')
    title=text(data['title'],160)
    sub=text(data['subtitle'],240) if data['subtitle']!='' else ''
    blocks=data['blocks']
    if not isinstance(blocks,list) or not 1<=len(blocks)<=160:raise ValueError('Invalid block count')
    out=[];chars=len(title)+len(sub)
    for block in blocks:
        if not isinstance(block,dict):raise ValueError('Invalid document block')
        kind=block.get('type')
        if kind in ('heading','paragraph','bullet') and set(block)=={'type','text'}:
            value=text(block['text'],180 if kind=='heading' else 3000)
            chars+=len(value);out.append({'type':kind,'text':value})
        elif kind=='table' and set(block)=={'type','headers','rows'}:
            headers=block['headers'];rows=block['rows']
            if not isinstance(headers,list) or not 2<=len(headers)<=5 or not isinstance(rows,list) or not 1<=len(rows)<=60:
                raise ValueError('Invalid table dimensions')
            headers=[text(c,80) for c in headers];clean=[]
            for row in rows:
                if not isinstance(row,list) or len(row)!=len(headers):raise ValueError('Table column count mismatch')
                clean.append([text(c,200) for c in row])
            chars+=sum(map(len,headers))+sum(len(c) for row in clean for c in row)
            out.append({'type':kind,'headers':headers,'rows':clean})
        else:raise ValueError('Unknown block or unexpected fields')
        if chars>55000:raise ValueError('Document text exceeds budget')
    return {'title':title,'subtitle':sub,'theme':data['theme'],'page_size':data['page_size'],'blocks':out}

def spec_path(root,relative,exclude):
    if not isinstance(relative,str) or not relative.casefold().endswith('.json') or len(relative)>300:
        raise ValueError('Choose a project JSON document specification')
    parts=relative.split('/')
    if any(not p or p in ('.','..') or '\\' in p or ':' in p or '\0' in p or p.endswith((' ','.')) for p in parts) or excluded(relative,set(exclude)):
        raise ValueError('Protected or unsafe specification path')
    current=root
    for part in parts:
        current=current/part
        if linked(current):raise ValueError('Linked specification path refused')
    if current.resolve(strict=True)!=current or not current.is_file():raise ValueError('Specification missing')
    return current

def read_spec(path):
    with path.open('rb') as f:raw=f.read(MAX_SPEC+1)
    if len(raw)>MAX_SPEC:raise ValueError('Specification too large')
    try:data=checked(strict_json(raw.decode('utf-8')))
    except (UnicodeError,RecursionError,TypeError) as exc:raise ValueError('Invalid document specification') from exc
    return data,hashlib.sha256(raw).hexdigest()

def review(root,source,output,exclude=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude)
    path=spec_path(root,source,exclude);target(root,output,exclude,exists=False)
    guard=snapshot_file(path)
    doc,digest=read_spec(path)
    if digest!=guard['expected']:raise ValueError('Specification changed during review')
    return {'schema':SCHEMA,'root':str(root),'source':source,'output':output,'exclude':exclude,
            'source_guard':guard,'expires_at':int(time.time())+1800},doc

def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if (not isinstance(plan,dict) or set(plan)!={'schema','root','source','output','exclude','source_guard','expires_at'}
        or plan['schema']!=SCHEMA or plan['root']!=str(root)
        or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800
        or exclusions(plan['exclude'])!=plan['exclude']):
        raise ValueError('Invalid or expired document approval')
    path=spec_path(root,plan['source'],plan['exclude'])
    output=target(root,plan['output'],plan['exclude'],exists=False)
    if snapshot_file(path)!=plan['source_guard']:raise ValueError('Reviewed document specification changed')
    doc,digest=read_spec(path)
    if digest!=plan['source_guard']['expected']:raise ValueError('Reviewed document bytes changed')
    return doc,output

def render(doc):
    import reportlab
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4,letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
    from pypdf import PdfReader,__version__
    if reportlab.Version!=REPORTLAB_VERSION or __version__!=PARSER_VERSION:
        raise ValueError('Install pinned PDF production tools first')
    accent=colors.HexColor({'navy':'#183A56','graphite':'#35404A','forest':'#27584B'}[doc['theme']])
    ink=colors.HexColor('#18232D');muted=colors.HexColor('#546574')
    size=A4 if doc['page_size']=='A4' else letter
    stream=io.BytesIO()
    template=SimpleDocTemplate(stream,pagesize=size,leftMargin=48,rightMargin=48,topMargin=52,bottomMargin=52,
                               title=doc['title'],author='JANUS',pageCompression=1)
    def style(name,font,pt,lead,color,**kw):
        return ParagraphStyle(name,fontName=font,fontSize=pt,leading=lead,textColor=color,**kw)
    title=style('title','Helvetica-Bold',24,29,accent,spaceAfter=10,keepWithNext=True)
    subtitle=style('subtitle','Helvetica',12,17,muted,spaceAfter=16)
    heading=style('heading','Helvetica-Bold',14,18,accent,spaceBefore=12,spaceAfter=6,keepWithNext=True)
    body=style('body','Helvetica',10.5,15,ink,spaceAfter=7)
    bullet=style('bullet','Helvetica',10.5,15,ink,leftIndent=13,firstLineIndent=-10,spaceAfter=5)
    cell=style('cell','Helvetica',9,12,ink)
    header=style('header','Helvetica-Bold',9,12,colors.white)
    story=[Paragraph(escape(doc['title']),title)];expected=[doc['title']]
    if doc['subtitle']:story.append(Paragraph(escape(doc['subtitle']),subtitle));expected.append(doc['subtitle'])
    for block in doc['blocks']:
        kind=block['type']
        if kind=='table':
            rows=[block['headers'],*block['rows']]
            data=[[Paragraph(escape(c),header if i==0 else cell) for c in row] for i,row in enumerate(rows)]
            tbl=Table(data,colWidths=[(size[0]-108)/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT')
            tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),accent),('VALIGN',(0,0),(-1,-1),'TOP'),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F1F5F7')]),
                ('LINEBELOW',(0,0),(-1,0),.7,accent),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#DCE4E8')),
                ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
                ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            story.extend([tbl,Spacer(1,9)])
            expected.extend(c for row in rows for c in row)
        else:
            value=block['text'];expected.append(value)
            story.append(Paragraph(escape(('- ' if kind=='bullet' else '')+value),
                         heading if kind=='heading' else bullet if kind=='bullet' else body))
    def footer(canvas,document):
        canvas.setStrokeColor(accent);canvas.setLineWidth(.6)
        canvas.line(48,38,size[0]-48,38)
        canvas.setFillColor(muted);canvas.setFont('Helvetica',9)
        canvas.drawRightString(size[0]-48,25,'Page '+str(document.page))
        if document.page>MAX_PAGES:raise ValueError('PDF page limit exceeded')
    template.build(story,onFirstPage=footer,onLaterPages=footer)
    raw=stream.getvalue()
    if len(raw)>MAX_OUTPUT:raise ValueError('PDF output exceeds bound')
    reader=PdfReader(io.BytesIO(raw),strict=True)
    if reader.is_encrypted or not 1<=len(reader.pages)<=MAX_PAGES:raise ValueError('Invalid generated PDF page count')
    if any(abs(float(page.mediabox.width)-size[0])>.01 or abs(float(page.mediabox.height)-size[1])>.01 for page in reader.pages):
        raise ValueError('Generated PDF page geometry mismatch')
    def normalized(value):return re.sub(r'\s+','',value)
    extracted=normalized(' '.join(re.sub(r'(?m)^Page \d+\s*$','',page.extract_text() or '') for page in reader.pages))
    if any(normalized(value) not in extracted for value in expected):
        raise ValueError('Generated PDF did not preserve all requested text')
    return raw,len(reader.pages)

def execute(root,plan):
    doc,output=validate(root,plan)
    require_storage(output.parent)
    raw,pages=render(doc)
    doc,output=validate(root,plan);require_storage(output.parent)
    fd,tmp=tempfile.mkstemp(prefix='.janus-document-',suffix='.tmp',dir=output.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        validate(root,plan)
        os.link(tmp,output)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return {'schema':'janus-pdf-document-result-v1','status':'structurally_verified','output':plan['output'],
            'pages':pages,'sha256':hashlib.sha256(raw).hexdigest(),'text_presence_verified':True,
            'visual_render_verified':False,'content_accuracy_verified':False}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--plan',required=True)
    args=parser.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2)
            resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(args.root,json.loads(args.plan)),sort_keys=True),flush=True)
        return 0
    except Exception as exc:
        print(json.dumps({'schema':'janus-pdf-document-result-v1','status':'blocked','error_type':type(exc).__name__,
                          'reason':str(exc)[:300] if isinstance(exc,ValueError) else 'PDF production unavailable; inspect source and installed tools'}),flush=True)
        return 1

if __name__=='__main__':sys.exit(main())
