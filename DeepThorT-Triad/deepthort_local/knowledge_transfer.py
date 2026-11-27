"""Portable project knowledge enrollment manifests; rebuild from matching local files."""
from __future__ import annotations
import json
from pathlib import Path
import re
from . import typed_project_tool as guard
from .document_knowledge import (_key,_name,_read,_digest,_extract,_fragments,SUFFIXES,
    MAX_DOCUMENTS,MAX_PROJECT_POSTINGS,MAX_BYTES,TEXT_SUFFIXES)
from .source_security import exclusions
from .structured_source import strict_json

SCHEMA='janus-knowledge-transfer-v1'
HASH=re.compile(r'[0-9a-f]{64}\Z')
MAX_MANIFEST=65536
MAX_TRANSFER=12

def checked(m):
    if not isinstance(m,dict) or set(m)!={'schema','documents'} or m['schema']!=SCHEMA:
        raise ValueError('Expected a portable knowledge enrollment manifest')
    docs=m['documents']
    if not isinstance(docs,list) or not 1<=len(docs)<=MAX_TRANSFER:
        raise ValueError('Select 1–12 documents per transfer')
    seen=set()
    for d in docs:
        if not isinstance(d,dict) or set(d)!={'path','sha256'} or not isinstance(d['path'],str) or not isinstance(d['sha256'],str) or not HASH.fullmatch(d['sha256']):
            raise ValueError('Invalid knowledge enrollment row')
        p=d['path']
        if not 1<=len(p)<=300 or '\\' in p or any(not x or x in ('.','..') or ':' in x or any(ord(c)<32 for c in x) for x in p.split('/')) or Path(p).suffix.casefold() not in SUFFIXES or p.casefold() in seen:
            raise ValueError('Invalid or duplicate relative document path')
        seen.add(p.casefold())
    return m

def source(root,row,exclude):
    path=guard.path_for(root,row['path'],exclude,SUFFIXES,exists=True)
    rel,target=_name(root,row['path'])
    if rel!=row['path'] or target!=path:raise ValueError('Document path identity differs')
    raw=_read(path,large_text=True)
    if _digest(raw)!=row['sha256']:raise ValueError('Document differs from transfer manifest: '+rel)
    return path,raw

def stop(cancelled):
    if cancelled and cancelled():raise ValueError('Knowledge transfer cancelled or inspection scope changed')

def export_manifest(index,root,paths,output,exclude=(),cancelled=None):
    root=Path(root).resolve(strict=True);ex=exclusions(exclude)
    if not isinstance(paths,(list,tuple)) or not 1<=len(paths)<=MAX_TRANSFER:
        raise ValueError('Select 1–12 enrolled documents')
    enrolled={r['path']:r for r in index.documents(root)}
    rows=[]
    for p in paths:
        stop(cancelled)
        if p not in enrolled or not enrolled[p]['current']:raise ValueError('Select only current enrolled documents')
        rows.append({'path':p,'sha256':enrolled[p]['sha256']})
    m=checked({'schema':SCHEMA,'documents':rows})
    dst=guard.path_for(root,output,ex,{'.json'},exists=False)
    def revalidate():
        stop(cancelled)
        guard.path_for(root,output,ex,{'.json'},exists=False)
        for row in rows:source(root,row,ex)
    revalidate()
    payload=json.dumps(m,ensure_ascii=True,sort_keys=True,indent=2).encode('utf-8')
    if len(payload)>MAX_MANIFEST:raise ValueError('Manifest exceeds bound')
    sha=guard.publish(payload,dst,revalidate)
    return {'documents':len(rows),'sha256':sha,'output':output,'contains_document_bodies':False}

def read_manifest(root,relative,exclude=()):
    root=Path(root).resolve(strict=True)
    path=guard.path_for(root,relative,exclusions(exclude),{'.json'},exists=True)
    raw=guard.read_bound(path,MAX_MANIFEST)
    return checked(strict_json(raw.decode('utf-8-sig'))),_digest(raw)

def import_manifest(index,root,relative,expected_sha256,exclude=(),cancelled=None):
    root=Path(root).resolve(strict=True);ex=exclusions(exclude)
    m,sha=read_manifest(root,relative,ex)
    if sha!=expected_sha256:raise ValueError('Reviewed manifest changed')
    key=_key(root);prepared=[]
    for row in m['documents']:
        stop(cancelled)
        path,raw=source(root,row,ex)
        locator,lines=_extract(raw,path.suffix.casefold());fragments=_fragments(lines,
            large_text=path.suffix.casefold() in TEXT_SUFFIXES and len(raw)>MAX_BYTES,cancelled=cancelled)
        if not fragments:raise ValueError('No supported searchable text: '+row['path'])
        prepared.append((row,locator,fragments))
    # One transaction: no partial batch enrollment, no imported posting data.
    with index._db() as db:
        db.execute('BEGIN IMMEDIATE')
        existing={p for (p,) in db.execute('SELECT path FROM knowledge_docs_v1 WHERE project=?',(key,))}
        incoming={row['path'] for row,_,_ in prepared}
        if len(existing|incoming)>MAX_DOCUMENTS:raise ValueError('Project document quota reached')
        marks=','.join('?' for _ in incoming)
        other=db.execute(f'SELECT count(*) FROM knowledge_terms_v1 WHERE project=? AND path NOT IN ({marks})',(key,*sorted(incoming))).fetchone()[0]
        if other+sum(len(terms) for _,_,fragments in prepared for _,_,_,terms in fragments)>MAX_PROJECT_POSTINGS:
            raise ValueError('Project posting quota reached')
        for row,locator,fragments in prepared:
            stop(cancelled);source(root,row,ex);p=row['path']
            index._delete(db,key,p)
            db.execute('INSERT INTO knowledge_docs_v1 VALUES (?,?,?,?,?,?)',(key,p,row['sha256'],locator,'explicit',len(fragments)))
            db.executemany('INSERT INTO knowledge_terms_v1 VALUES (?,?,?,?,?,?)',
                ((key,p,n,start,end,term) for n,start,end,terms in fragments for term in terms))
            db.execute('DELETE FROM knowledge_removed_v1 WHERE project=? AND path=?',(key,p))
        stop(cancelled)
        if read_manifest(root,relative,ex)[1]!=sha:raise ValueError('Reviewed manifest changed during import')
        for row,_,_ in prepared:source(root,row,ex)
        stop(cancelled)
    return {'documents':len(prepared),'manifest_sha256':sha,'index_rebuilt':True,'source_unchanged':True}
