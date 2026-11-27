"""Reviewed contract/policy evidence checklist; not a legal opinion."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.document_knowledge import _extract,MAX_BYTES,MAX_PDF_BYTES
from deepthort_local.pdf_diagrams import limits
from deepthort_local.long_form_writing import ID,literal
SCHEMA='janus-contract-policy-review-v1'
EXTRA=('document',('.txt','.md','.docx','.pdf'))
MAX_ROWS=20000
MAX_HITS=12
TOPICS={
    'obligations':['shall','must','required','agrees to','obligated'],
    'prohibitions':['must not','shall not','prohibited','may not'],
    'payment':['payment','fees','invoice','interest','refund'],
    'termination':['termination','terminate','cancellation','notice period'],
    'renewal':['renewal','automatically renew','expiration'],
    'liability':['liability','indemnity','indemnify','limitation of liability'],
    'privacy':['personal data','privacy','confidentiality','retention'],
    'disputes':['dispute','arbitration','jurisdiction','governing law']}
def checked(s):
    if not isinstance(s,dict) or set(s)!={'document','topics','custom_checks'} or not isinstance(s['document'],str):
        raise ValueError('Expected document, topics and custom checks')
    topics=s['topics'];custom=s['custom_checks']
    if not isinstance(topics,list) or any(not isinstance(x,str) or x not in TOPICS for x in topics) or len(set(topics))!=len(topics):
        raise ValueError('Unknown or duplicate review topic')
    if not isinstance(custom,list) or len(custom)>12 or not topics and not custom:raise ValueError('Choose review checks')
    ids=set(topics)
    for c in custom:
        if not isinstance(c,dict) or set(c)!={'id','label','phrases'} or not isinstance(c['id'],str) or not ID.fullmatch(c['id']) or c['id'] in ids:
            raise ValueError('Invalid custom check')
        ids.add(c['id']);literal(c['label'],120)
        if not isinstance(c['phrases'],list) or not 1<=len(c['phrases'])<=8:raise ValueError('Choose 1–8 literal phrases')
        for phrase in c['phrases']:literal(phrase,80)
        if len(set(p.casefold() for p in c['phrases']))!=len(c['phrases']):raise ValueError('Duplicate phrase')
    return s

def extracted_rows(raw,suffix):
    if not raw or len(raw)>(MAX_PDF_BYTES if suffix=='.pdf' else MAX_BYTES):
        raise ValueError('Source outside review byte budget')
    if suffix=='.pdf':
        import io
        from pypdf import PdfReader
        from deepthort_local.pdf_knowledge_worker import extract
        rows=extract(raw)
        missing=sorted(set(range(1,len(PdfReader(io.BytesIO(raw),strict=True).pages)+1))-{x[0] for x in rows})
        return [(f'page {p}, extracted line {n}',text) for p,n,text in rows],missing
    _,lines=_extract(raw,suffix)
    kind='paragraph' if suffix=='.docx' else 'line'
    return [(f'{kind} {i}',v) for i,v in enumerate(lines,1)],[]

def analyze(raw,s):
    checked(s)
    rows,missing=extracted_rows(raw,Path(s['document']).suffix.casefold())
    if not rows or len(rows)>MAX_ROWS or sum(len(v) for _,v in rows)>MAX_BYTES:
        raise ValueError('Review text exceeds budget or unavailable')
    checks=[{'id':x,'label':x.replace('_',' '),'phrases':TOPICS[x]} for x in s['topics']]+s['custom_checks']
    result=[]
    for check in checks:
        patterns=[(phrase,re.compile(r'(?<!\w)'+re.escape(phrase)+r'(?!\w)',re.IGNORECASE)) for phrase in check['phrases']]
        hits=[];count=0
        for location,text in rows:
            found=[(phrase,m) for phrase,p in patterns for m in p.finditer(text)]
            if not found:continue
            count+=1
            if len(hits)>=MAX_HITS:continue
            phrase,m=min(found,key=lambda v:(v[1].start(),-len(v[0])))
            start=max(0,m.start()-200);end=min(len(text),max(m.end(),start+500))
            hits.append({'location':location,'start':start,'quote':text[start:end],'matched_phrase':phrase,
                         'match_offset':m.start()})
        result.append({'id':check['id'],'label':check['label'],'matched_rows':count,'examples':hits,
                       'omitted_rows':count-len(hits),'status':'literal_evidence_found' if count else 'no_literal_match_not_proof_of_absence'})
    return {'schema':'janus-contract-policy-evidence-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'document':s['document'],'checks':result,'unreadable_pdf_pages':missing,
            'legal_conclusions_verified':False,'compliance_verified':False,
            'scope':'Literal phrase evidence only; review surrounding clauses, definitions, exceptions and jurisdiction separately. Missing matches are not proof of absence.'}
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    _,_,doc=validate(root,plan)
    if doc.stat().st_size>(MAX_PDF_BYTES if doc.suffix.casefold()=='.pdf' else MAX_BYTES):raise ValueError('Source exceeds review byte budget')
    return plan,dict(s,scope='Locate literal clause evidence; not a legal or compliance verdict.')
def execute(root,plan):
    s,dst,doc=validate(root,plan);raw=guard.exact(doc,plan['guards'][1],MAX_PDF_BYTES if doc.suffix.casefold()=='.pdf' else MAX_BYTES)
    r=analyze(raw,s);payload=json.dumps(r,ensure_ascii=True,allow_nan=False,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'clause_evidence_reviewed','output':plan['output'],'sha256':digest,
            'checks':len(r['checks']),'legal_conclusions_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        limits();print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Clause evidence review unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
