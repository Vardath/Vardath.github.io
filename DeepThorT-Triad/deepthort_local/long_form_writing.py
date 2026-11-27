"""Assemble a reviewed, complete long-form manuscript from independently drafted sections."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard

SCHEMA='janus-long-form-writing-v1'
ID=re.compile(r'[a-z][a-z0-9_-]{0,39}\Z')
def literal(value,limit):
    if (not isinstance(value,str) or not 1<=len(value)<=limit or value!=value.strip()
        or any(ord(c)<32 or 127<=ord(c)<=159 or c in '\u2028\u2029' or 0xd800<=ord(c)<=0xdfff for c in value)):
        raise ValueError('Expected bounded single-paragraph literal text')
    return value

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'title','outline','drafts'}:
        raise ValueError('Expected title, ordered outline and section drafts')
    literal(spec['title'],200)
    outline=spec['outline'];drafts=spec['drafts']
    if not isinstance(outline,list) or not 1<=len(outline)<=100 or not isinstance(drafts,dict):
        raise ValueError('Expected 1–100 outline entries and keyed drafts')
    ids=set();previous=0;total=0
    for entry in outline:
        if not isinstance(entry,dict) or set(entry)!={'id','heading','level','min_words'}:
            raise ValueError('Invalid outline entry')
        key=entry['id'];level=entry['level'];minimum=entry['min_words']
        if (not isinstance(key,str) or not ID.fullmatch(key) or key in ids
            or type(level) is not int or not 1<=level<=3 or level>previous+1
            or type(minimum) is not int or not 1<=minimum<=10000):
            raise ValueError('Invalid section ID, hierarchy or word requirement')
        previous=level;ids.add(key);literal(entry['heading'],200)
        paragraphs=drafts.get(key)
        if not isinstance(paragraphs,list) or not 1<=len(paragraphs)<=300:
            raise ValueError('Missing or invalid section draft: '+key)
        words=0
        for paragraph in paragraphs:
            literal(paragraph,10000);total+=len(paragraph);words+=len(paragraph.split())
        if words<minimum:raise ValueError('Section below reviewed word minimum: '+key)
    if ids!=set(drafts) or total>200000:
        raise ValueError('Unlisted section drafts or manuscript exceeds text budget')
    return spec

def assemble(spec):
    lines=[spec['title'],''];counts=[0,0,0];sections=[]
    for entry in spec['outline']:
        level=entry['level'];counts[level-1]+=1
        counts[level:]=[0]*(3-level)
        number='.'.join(str(n) for n in counts[:level])
        paragraphs=spec['drafts'][entry['id']]
        first=len(lines)+1
        lines.extend([number+' '+entry['heading'],''])
        for paragraph in paragraphs:lines.extend([paragraph,''])
        sections.append({'id':entry['id'],'number':number,'heading_line':first,
            'paragraphs':len(paragraphs),'words':sum(len(p.split()) for p in paragraphs),
            'draft_sha256':hashlib.sha256(json.dumps(paragraphs,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()})
    payload=('\n'.join(lines)+'\n').encode('utf-8')
    actual=payload.decode('utf-8').splitlines()
    if actual!=lines:raise ValueError('Manuscript text roundtrip failed')
    for entry,section in zip(spec['outline'],sections):
        index=section['heading_line']-1
        if actual[index]!=section['number']+' '+entry['heading'] or actual[index+2:index+2+2*section['paragraphs']:2]!=spec['drafts'][entry['id']]:
            raise ValueError('Section coverage verification failed')
    return payload,sections

def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.txt')
    _,sections=assemble(spec)
    return plan,dict(spec,section_receipts=sections)

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.txt')

def execute(root,plan):
    spec,dst,_=validate(root,plan);payload,sections=assemble(spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-long-form-writing-result-v1','status':'manuscript_structure_verified','output':plan['output'],
        'sha256':sha,'sections':len(sections),'words':sum(s['words'] for s in sections),
        'section_receipts':sections,'source_unchanged':True,'semantic_quality_verified':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        receipt=execute(a.root,json.loads(a.plan))
        # Keep process logs compact; the full exact section preview was reviewed.
        receipt.pop('section_receipts')
        print(json.dumps(receipt,sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Manuscript unavailable; inspect complete outline and section drafts'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
