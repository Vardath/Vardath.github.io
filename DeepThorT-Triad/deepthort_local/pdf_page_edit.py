"""Reviewed, non-overwriting PDF page operations using the existing pinned parser."""
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

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local.action_guards import snapshot_file
from deepthort_local.pdf_knowledge_worker import PARSER_VERSION,MAX_PDF_BYTES,MAX_PAGES
from deepthort_local.source_security import exclusions,excluded,linked
from deepthort_local.disk_gate import require_storage

MAX_OUTPUT=16*1024*1024
MAX_CONTENT=8*1024*1024
SCHEMA='janus-pdf-page-edit-v1'

def target(root,relative,exclude,*,exists):
    if not isinstance(relative,str) or not 1<=len(relative)<=300:
        raise ValueError('Use a bounded project-relative PDF filename')
    parts=relative.split('/')
    if any(not part or part in ('.','..') or '\\' in part or ':' in part or '\0' in part or part.endswith((' ','.')) for part in parts):
        raise ValueError('Unsafe project-relative PDF filename')
    if excluded(relative,set(exclude)) or not relative.casefold().endswith('.pdf'):
        raise ValueError('Protected path or not PDF')
    current=root
    for part in parts:
        current=current/part
        if current.exists() or current.is_symlink():
            if linked(current):raise ValueError('Linked PDF path refused')
    if current.resolve(strict=False)!=current or not current.parent.is_dir():
        raise ValueError('Choose an existing unlinked project folder')
    if exists and not current.is_file():raise ValueError('Source PDF missing')
    if not exists and (current.exists() or current.is_symlink()):raise ValueError('Output already exists')
    return current

def page_plan(spec):
    if not isinstance(spec,str) or not 1<=len(spec)<=1500:raise ValueError('Invalid page list')
    pages=[]
    for item in spec.split(','):
        match=re.fullmatch(r'\s*([1-9][0-9]{0,2})(?::(0|90|180|270))?\s*',item)
        if not match:raise ValueError('Use comma-separated pages, optionally page:rotation, e.g. 3:90,1,2')
        page=int(match[1]);rotation=int(match[2] or 0)
        if page>MAX_PAGES or len(pages)>=MAX_PAGES:raise ValueError('Page limit exceeded')
        pages.append([page,rotation])
    return pages

def review(root,source,output,spec,exclude=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude)
    a=target(root,source,exclude,exists=True)
    target(root,output,exclude,exists=False)
    if a.stat().st_size>MAX_PDF_BYTES:raise ValueError('Source exceeds 4 MiB PDF limit')
    return {'schema':SCHEMA,'root':str(root),'source':source,'output':output,'pages':page_plan(spec),
            'exclude':exclude,'source_guard':snapshot_file(a),'expires_at':int(time.time())+1800}

def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if (not isinstance(plan,dict) or set(plan)!={'schema','root','source','output','pages','exclude','source_guard','expires_at'}
        or plan['schema']!=SCHEMA or plan['root']!=str(root)
        or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800
        or exclusions(plan['exclude'])!=plan['exclude']):
        raise ValueError('Invalid or expired PDF review')
    pages=plan['pages']
    if not isinstance(pages,list) or not 1<=len(pages)<=MAX_PAGES or any(
        not isinstance(x,list) or len(x)!=2 or type(x[0]) is not int or type(x[1]) is not int
        or not 1<=x[0]<=MAX_PAGES or x[1] not in (0,90,180,270) for x in pages):
        raise ValueError('Invalid reviewed page operations')
    a=target(root,plan['source'],plan['exclude'],exists=True)
    b=target(root,plan['output'],plan['exclude'],exists=False)
    if a.stat().st_size>MAX_PDF_BYTES or snapshot_file(a)!=plan['source_guard']:
        raise ValueError('Reviewed source changed')
    return a,b

def reader_for(raw):
    from pypdf import PdfReader,__version__
    if __version__!=PARSER_VERSION:raise ValueError('Install the existing pinned PDF tools first')
    if not raw.startswith(b'%PDF-'):raise ValueError('Not PDF')
    reader=PdfReader(io.BytesIO(raw),strict=True)
    if reader.is_encrypted or not 1<=len(reader.pages)<=MAX_PAGES:
        raise ValueError('Encrypted or oversized page count unsupported')
    catalog=reader.trailer['/Root']
    if any(key in catalog for key in ('/AcroForm','/Perms','/OpenAction','/AA','/Names','/Outlines','/StructTreeRoot','/OCProperties','/PageLabels','/Collection','/Metadata','/OutputIntents')):
        raise ValueError('Interactive, signed, tagged, bookmarked or advanced PDF unsupported')
    for page in reader.pages:
        if any(key in page for key in ('/Annots','/AA','/Metadata','/StructParents','/PieceInfo','/Trans')):
            raise ValueError('Annotated or advanced PDF page unsupported')
    return reader

def page_signature(page):
    content=page.get_contents()
    data=content.get_data() if content is not None else b''
    if len(data)>MAX_CONTENT:raise ValueError('Decoded content exceeds bound')
    boxes=[list(map(float,getattr(page,key))) for key in ('mediabox','cropbox','bleedbox','trimbox','artbox')]
    return {'rotation':int(page.rotation)%360,'boxes':boxes,'content_sha':hashlib.sha256(data).hexdigest()}

def execute(root,plan):
    a,b=validate(root,plan)
    require_storage(a.parent,b.parent)
    with a.open('rb') as src:raw=src.read(MAX_PDF_BYTES+1)
    if len(raw)>MAX_PDF_BYTES or hashlib.sha256(raw).hexdigest()!=plan['source_guard']['expected']:
        raise ValueError('Reviewed PDF bytes changed')
    reader=reader_for(raw)
    if any(number>len(reader.pages) for number,_ in plan['pages']):
        raise ValueError('Requested page exceeds source page count')
    from pypdf import PdfWriter
    writer=PdfWriter()
    expected=[]
    for number,rotation in plan['pages']:
        original=reader.pages[number-1]
        sig=page_signature(original)
        writer.reset_translation(reader)
        page=writer.add_page(original)
        if rotation:page.rotate(rotation)
        sig['rotation']=(sig['rotation']+rotation)%360
        expected.append(sig)
    if reader.metadata:
        metadata={k:str(v) for k,v in reader.metadata.items() if isinstance(v,str) and len(v)<=2000}
        if metadata:writer.add_metadata(metadata)
    stream=io.BytesIO();writer.write(stream);output=stream.getvalue()
    if len(output)>MAX_OUTPUT:raise ValueError('Output exceeds bound')
    result=reader_for(output)
    if [page_signature(page) for page in result.pages]!=expected:
        raise ValueError('Reopened PDF failed page count/order/content/geometry verification')
    a,b=validate(root,plan);require_storage(a.parent,b.parent)
    fd,tmp=tempfile.mkstemp(prefix='.janus-pdf-',suffix='.tmp',dir=b.parent)
    try:
        with os.fdopen(fd,'wb') as handle:
            handle.write(output);handle.flush();os.fsync(handle.fileno())
        validate(root,plan)
        # Atomic non-overwriting publication on hard-link-capable filesystems.
        os.link(tmp,b)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return {'schema':'janus-pdf-page-edit-result-v1','status':'structurally_verified',
            'output':plan['output'],'pages':len(expected),'sha256':hashlib.sha256(output).hexdigest(),
            'source_unchanged':True,'visual_render_verified':False,'full_pdf_fidelity_verified':False}

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
        print(json.dumps({'schema':'janus-pdf-page-edit-result-v1','status':'blocked','error_type':type(exc).__name__,
                          'reason':str(exc)[:300] if isinstance(exc,ValueError) else 'PDF edit unavailable; inspect source and installed pinned PDF tools'}),flush=True)
        return 1

if __name__=='__main__':sys.exit(main())
