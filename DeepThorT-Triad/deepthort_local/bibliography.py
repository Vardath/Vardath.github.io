"""Resolve explicit manuscript citation markers using reviewed bibliography records."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import literal,ID

SCHEMA='janus-bibliography-v1'
EXTRA=('manuscript','.txt')
MARKER=re.compile(r'\[\[cite:([a-z][a-z0-9_-]{0,39})\]\]')
MAX_TEXT=512*1024
def checked(spec):
    if (not isinstance(spec,dict) or set(spec)!={'manuscript','style','references'}
        or not isinstance(spec['manuscript'],str) or spec['style'] not in ('numeric','author_year')
        or not isinstance(spec['references'],list) or not 1<=len(spec['references'])<=300):
        raise ValueError('Expected manuscript, citation style and explicit references')
    ids=set();labels=set()
    for r in spec['references']:
        if not isinstance(r,dict) or set(r)!={'id','authors','year','title','publication','locator'}:
            raise ValueError('Invalid reference record')
        key=r['id'];authors=r['authors'];year=r['year']
        if (not isinstance(key,str) or not ID.fullmatch(key) or key in ids
            or not isinstance(authors,list) or not 1<=len(authors)<=20
            or (year is not None and (type(year) is not int or not 1<=year<=9999))):
            raise ValueError('Invalid reference ID, authors or year')
        ids.add(key)
        for a in authors:literal(a,150)
        literal(r['title'],500)
        for field in ('publication','locator'):
            if r[field]!='':literal(r[field],500)
        if spec['style']=='author_year':
            label=author_year(r)
            if label.casefold() in labels:raise ValueError('Ambiguous author-year labels; use numeric style')
            labels.add(label.casefold())
    return spec

def author_year(r):
    return r['authors'][0]+(' et al.' if len(r['authors'])>1 else '')+', '+(str(r['year']) if r['year'] is not None else 'n.d.')

def compose(raw,spec):
    if not raw or len(raw)>MAX_TEXT:raise ValueError('Manuscript exceeds text limit')
    text=raw.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n')
    if any((ord(c)<32 and c not in '\n\t') or 127<=ord(c)<=159 for c in text):
        raise ValueError('Unsupported manuscript control characters')
    refs={r['id']:r for r in spec['references']};used={};pieces=[];matches=list(MARKER.finditer(text))
    if not 1<=len(matches)<=2000:raise ValueError('Expected bounded explicit citation markers')
    if '[[cite' in MARKER.sub('',text):raise ValueError('Malformed citation marker')
    cursor=0
    for match in matches:
        key=match.group(1)
        if key not in refs:raise ValueError('Unknown citation ID: '+key)
        if key not in used:used[key]=len(used)+1
        label='['+str(used[key])+']' if spec['style']=='numeric' else '('+author_year(refs[key])+')'
        pieces.append(text[cursor:match.start()]);pieces.append(label);cursor=match.end()
    pieces.append(text[cursor:])
    if set(used)!=set(refs):raise ValueError('Unused reference records')
    if spec['style']=='numeric':ordered=list(used)
    else:ordered=sorted(used,key=lambda k:(author_year(refs[k]).casefold(),k))
    entries=[]
    for key in ordered:
        r=refs[key];label='['+str(used[key])+'] ' if spec['style']=='numeric' else ''
        entry=label+'; '.join(r['authors'])+' ('+(str(r['year']) if r['year'] is not None else 'n.d.')+'). '+r['title']+'.'
        for field in ('publication','locator'):
            if r[field]:entry+=' '+r[field]+'.'
        entries.append(entry)
    body=''.join(pieces)
    # Preserve all non-marker characters (apart from documented BOM/newline normalization).
    separator='' if body.endswith('\n\n') else '\n' if body.endswith('\n') else '\n\n'
    output=body+separator+'References\n\n'+'\n\n'.join(entries)+'\n'
    payload=output.encode('utf-8')
    if payload.decode('utf-8')!=output or len(entries)!=len(refs):
        raise ValueError('Bibliography text verification failed')
    return payload,{'references':len(entries),'citation_occurrences':len(matches),'reference_order':ordered,
                    'source_sha256':hashlib.sha256(raw).hexdigest(),'metadata_independently_verified':False}

def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.txt',extra=EXTRA)
    _,_,path=validate(root,plan)
    raw=guard.exact(path,plan['guards'][1],MAX_TEXT)
    payload,receipt=compose(raw,spec)
    # Every resolved citation and bibliography entry can be reviewed before approval.
    return plan,dict(spec,resolved_document=payload.decode('utf-8'),receipt=receipt)

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.txt',extra=EXTRA)

def execute(root,plan):
    spec,dst,path=validate(root,plan);raw=guard.exact(path,plan['guards'][1],MAX_TEXT)
    payload,receipt=compose(raw,spec);sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-bibliography-result-v1','status':'citation_structure_verified','output':plan['output'],
        'sha256':sha,**receipt,'source_unchanged':True,'claim_support_verified':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        result=execute(a.root,json.loads(a.plan));result.pop('reference_order')
        print(json.dumps(result,sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Bibliography unavailable; inspect citation markers, references and source review'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
