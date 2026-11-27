"""Reviewed local text-content conversion; deliberately not layout-preserving."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import zipfile
from xml.etree import ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local.action_guards import snapshot_file
from deepthort_local.source_security import exclusions,excluded,linked
from deepthort_local.disk_gate import require_storage
from deepthort_local.document_knowledge import _extract,MAX_BYTES,MAX_PDF_BYTES,W
from deepthort_local.pdf_document import checked,render

SCHEMA='janus-document-conversion-v1'
INPUTS={'.txt','.md','.docx','.pdf'}
OUTPUTS={'.txt','.docx','.pdf'}
MAX_OUTPUT=16*1024*1024
MAX_LINES=20000

def path_for(root,relative,exclude,*,source):
    if not isinstance(relative,str) or not 1<=len(relative)<=300:
        raise ValueError('Use a bounded project-relative filename')
    suffix=Path(relative).suffix.casefold()
    parts=relative.split('/')
    if suffix not in (INPUTS if source else OUTPUTS) or excluded(relative,set(exclude)) or any(
        not x or x in ('.','..') or '\\' in x or ':' in x or '\0' in x or x.endswith((' ','.')) for x in parts):
        raise ValueError('Unsupported or protected document path')
    path=root
    for part in parts:
        path=path/part
        if path.exists() or path.is_symlink():
            if linked(path):raise ValueError('Linked document paths refused')
    if path.resolve(strict=False)!=path or not path.parent.is_dir():
        raise ValueError('Document must be inside an existing project folder')
    if source and not path.is_file():raise ValueError('Source document missing')
    if not source and (path.exists() or path.is_symlink()):raise ValueError('Output already exists')
    return path

def review(root,source,output,exclude=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude)
    a=path_for(root,source,exclude,source=True);b=path_for(root,output,exclude,source=False)
    if a.suffix.casefold()==b.suffix.casefold():raise ValueError('Choose a different output format')
    if a.stat().st_size>(MAX_PDF_BYTES if a.suffix.casefold()=='.pdf' else MAX_BYTES):
        raise ValueError('Source exceeds conversion size limit')
    return {'schema':SCHEMA,'root':str(root),'source':source,'output':output,'exclude':exclude,
            'source_guard':snapshot_file(a),'expires_at':int(time.time())+1800}

def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if (not isinstance(plan,dict) or set(plan)!={'schema','root','source','output','exclude','source_guard','expires_at'}
        or plan['schema']!=SCHEMA or plan['root']!=str(root)
        or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800
        or exclusions(plan['exclude'])!=plan['exclude']):
        raise ValueError('Invalid or expired conversion approval')
    a=path_for(root,plan['source'],plan['exclude'],source=True)
    b=path_for(root,plan['output'],plan['exclude'],source=False)
    if a.suffix.casefold()==b.suffix.casefold() or snapshot_file(a)!=plan['source_guard']:
        raise ValueError('Reviewed source changed or invalid conversion')
    return a,b

def source_lines(raw,suffix):
    if not raw or len(raw)>(MAX_PDF_BYTES if suffix=='.pdf' else MAX_BYTES):
        raise ValueError('Source exceeds conversion limit or is empty')
    if suffix=='.pdf':
        # Use the existing pinned parser directly inside the supervised worker.
        # Reject pages without text instead of silently dropping scanned pages.
        from deepthort_local.pdf_knowledge_worker import extract
        from pypdf import PdfReader
        rows=extract(raw);reader=PdfReader(io.BytesIO(raw),strict=True)
        if set(row[0] for row in rows)!=set(range(1,len(reader.pages)+1)):
            raise ValueError('At least one PDF page lacks extractable text; OCR is not supported')
        lines=[row[2] for row in rows]
    else:
        _,lines=_extract(raw,suffix)
    if not lines or not any(x.strip() for x in lines) or len(lines)>MAX_LINES or sum(map(len,lines))>MAX_BYTES:
        raise ValueError('No usable text or source exceeds text budget')
    if any(any(ord(c)<32 and c!='\t' or ord(c)==127 or ord(c) in (0xfffe,0xffff) for c in line) for line in lines):
        raise ValueError('Unsupported control characters in source text')
    return lines

def docx_bytes(lines):
    # Minimal valid, editable OOXML package. No macros, external relationships,
    # templates, fields or executable content. Each input line is a paragraph.
    doc=ET.Element(W+'document');body=ET.SubElement(doc,W+'body')
    for line in lines:
        para=ET.SubElement(body,W+'p');run=ET.SubElement(para,W+'r')
        # Preserve literal tabs with native tab nodes and text with xml:space.
        for i,part in enumerate(line.split('\t')):
            if i:ET.SubElement(run,W+'tab')
            node=ET.SubElement(run,W+'t',{'{http://www.w3.org/XML/1998/namespace}space':'preserve'})
            node.text=part
    sect=ET.SubElement(body,W+'sectPr')
    ET.SubElement(sect,W+'pgSz',{W+'w':'11906',W+'h':'16838'})
    ET.SubElement(sect,W+'pgMar',{W+'top':'1440',W+'right':'1440',W+'bottom':'1440',W+'left':'1440'})
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        archive.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        archive.writestr('word/document.xml',ET.tostring(doc,encoding='utf-8',xml_declaration=True))
    raw=stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.testzip() is not None:raise ValueError('DOCX archive verification failed')
        body=ET.fromstring(archive.read('word/document.xml')).find(W+'body')
        actual=[''.join('\t' if n.tag==W+'tab' else n.text or '' for n in p.iter() if n.tag in (W+'t',W+'tab'))
                for p in body.findall(W+'p')]
        if actual!=lines:raise ValueError('DOCX text roundtrip failed')
    return raw

def convert(lines,suffix,title):
    if suffix=='.txt':
        data=('\n'.join(lines)+'\n').encode('utf-8')
        if data.decode('utf-8').splitlines()!=lines:raise ValueError('Text roundtrip failed')
        return data
    if suffix=='.docx':return docx_bytes(lines)
    if suffix=='.pdf':
        # This intentionally uses the bounded existing PDF producer, with an
        # explicit filename title and normalized nonempty text paragraphs.
        blocks=[{'type':'paragraph','text':line.replace('\t',' ')} for line in lines if line.strip()]
        doc=checked({'title':title,'subtitle':'Text-content conversion','theme':'graphite','page_size':'A4','blocks':blocks})
        return render(doc)[0]
    raise ValueError('Unsupported output format')

def execute(root,plan):
    a,b=validate(root,plan);require_storage(a.parent,b.parent)
    limit=MAX_PDF_BYTES if a.suffix.casefold()=='.pdf' else MAX_BYTES
    with a.open('rb') as f:raw=f.read(limit+1)
    if len(raw)>limit or hashlib.sha256(raw).hexdigest()!=plan['source_guard']['expected']:
        raise ValueError('Reviewed source bytes changed')
    lines=source_lines(raw,a.suffix.casefold())
    payload=convert(lines,b.suffix.casefold(),a.stem[:160])
    if not payload or len(payload)>MAX_OUTPUT:raise ValueError('Converted output exceeds limit')
    a,b=validate(root,plan);require_storage(a.parent,b.parent)
    fd,tmp=tempfile.mkstemp(prefix='.janus-conversion-',suffix='.tmp',dir=b.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(payload);f.flush();os.fsync(f.fileno())
        validate(root,plan);os.link(tmp,b)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return {'schema':'janus-document-conversion-result-v1','status':'text_content_verified','output':plan['output'],
            'sha256':hashlib.sha256(payload).hexdigest(),'source_format':a.suffix.casefold(),'output_format':b.suffix.casefold(),
            'source_text_lines':len(lines),'source_unchanged':True,'layout_preserved':False,
            'scope':'Extracted main text only; images, formatting, fields, links and other document structures not preserved. Markdown syntax is literal. PDF text order is parser-dependent.'}

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
        print(json.dumps({'schema':'janus-document-conversion-result-v1','status':'blocked','error_type':type(exc).__name__,
                          'reason':'Conversion unavailable; inspect source text, format, limits and installed tools'}),flush=True)
        return 1

if __name__=='__main__':sys.exit(main())
