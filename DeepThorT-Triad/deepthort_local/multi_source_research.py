"""Collect reviewed independent URL reads and build a traceable lexical evidence matrix."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import literal
from deepthort_local.search_interpretation import terms
from deepthort_local.website_monitor import checked_url
from deepthort_local.webpage_retrieval import fetch_page,MAX_BODY,MAX_TEXT,MAX_LINKS

SCHEMA='janus-multi-source-research-v1'
REPORT_SCHEMA='janus-multi-source-evidence-v1'
MAX_SOURCES=5
MAX_EXCERPTS=5
MAX_SECONDS=150
HASH=re.compile(r'[0-9a-f]{64}\Z')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'question','urls'}:raise ValueError('Expected exact research question and explicit URLs')
    literal(s['question'],600)
    if not terms(s['question']):raise ValueError('Question has no searchable terms')
    urls=s['urls']
    if not isinstance(urls,list) or not 2<=len(urls)<=MAX_SOURCES:raise ValueError('Choose 2–5 exact public page URLs')
    keys=[]
    for url in urls:keys.append(checked_url(url))
    if len(set(keys))!=len(keys):raise ValueError('Repeated source URL')
    return s

def validated_page(url,p):
    if (not isinstance(p,dict) or p.get('schema')!='janus-webpage-evidence-v1' or p.get('url')!=url
            or p.get('reference_only') is not True or p.get('content_verified_as_factual') is not False
            or p.get('script_executed') is not False or p.get('links_followed') is not False
            or p.get('mime') not in ('text/html','text/plain') or not isinstance(p.get('title'),str) or len(p['title'])>500
            or not isinstance(p.get('text'),str) or not 1<=len(p['text'])<=MAX_TEXT
            or not isinstance(p.get('response_sha256'),str) or not HASH.fullmatch(p['response_sha256'])
            or type(p.get('response_bytes')) is not int or not 1<=p['response_bytes']<=MAX_BODY
            or not isinstance(p.get('discovered_links'),list) or len(p['discovered_links'])>MAX_LINKS
            or any(not isinstance(link,str) or len(link)>2000 for link in p['discovered_links'])
            or hashlib.sha256(p['text'].encode('utf-8')).hexdigest()!=p.get('text_sha256')):
        raise ValueError('Invalid or inconsistent page evidence')
    return p

def excerpts(text,q):
    """Literal spans of exact source lines, ranked only for lexical relevance."""
    hits=[]
    for line_no,line in enumerate(text.split('\n'),1):
        # Bound even minified text and retain exact source position.
        for start in range(0,len(line),480):
            part=line[start:start+480];matched=terms(part)&q
            if matched:hits.append({'line':line_no,'start':start,'text':part,'matched_terms':sorted(matched)})
    hits.sort(key=lambda e:(-len(e['matched_terms']),e['line'],e['start']))
    return hits[:MAX_EXCERPTS]

def assemble(s,observations):
    checked(s)
    if not isinstance(observations,list) or len(observations)!=len(s['urls']):raise ValueError('Every reviewed URL needs an observation')
    q=terms(s['question']);sources=[];matrix={t:[] for t in sorted(q)};digests={};hosts=set()
    for i,(url,p) in enumerate(zip(s['urls'],observations),1):
        ident='S'+str(i);host,_=checked_url(url)
        if p is None:
            sources.append({'id':ident,'url':url,'hostname':host,'status':'unavailable'});continue
        validated_page(url,p);hosts.add(host)
        digest=p['text_sha256'];duplicate=digests.get(digest);digests.setdefault(digest,ident)
        found=sorted(q&terms(p['text']))
        if not duplicate:
            for t in found:matrix[t].append(ident)
        sources.append({'id':ident,'url':url,'hostname':host,'status':'retrieved',
                        'duplicate_text_of':duplicate,'matched_terms':found,'excerpts':excerpts(p['text'],q),'evidence':p})
    return {'schema':REPORT_SCHEMA,'question':s['question'],'reviewed_urls':s['urls'],
            'sources':sources,'term_source_matrix':matrix,'uncovered_terms':[t for t,ids in matrix.items() if not ids],
            'retrieved_count':sum(r['status']=='retrieved' for r in sources),'distinct_text_count':len(digests),
            'hostname_count':len(hosts),'source_independence_verified':False,'claims_verified':False,
            'reference_only':True,
            'limitations':'Exact static page observations and literal term coverage only. Identical text is grouped; different text/hosts do not prove independent sources. Excerpts do not establish claim support, truth, completeness or credibility.'}

def collect(s,*,approved=False,cancelled=None,retrieve=fetch_page,clock=time.monotonic):
    checked(s)
    if approved is not True:raise ValueError('Explicit approval for all listed URL reads required')
    deadline=clock()+MAX_SECONDS
    def stop():return bool((cancelled and cancelled()) or clock()>deadline)
    observations=[]
    for url in s['urls']:
        if stop():raise TimeoutError('Research stopped')
        try:
            p=retrieve(url,approved=True,cancelled=stop)
            validated_page(url,p)
        except (OSError,ValueError,UnicodeError):
            p=None
        if stop():raise TimeoutError('Research stopped')
        observations.append(p)
    return assemble(s,observations)

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,network_consent='Read each of these exact public HTTPS URLs once and record text and hashes; question remains local. No discovered link will be followed.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def execute(root,plan,*,run=collect):
    s,dst,_=validate(root,plan);r=run(s,approved=True)
    if r.get('question')!=s['question'] or r.get('reviewed_urls')!=s['urls'] or r.get('claims_verified') is not False:raise ValueError('Research receipt mismatch')
    payload=json.dumps(r,ensure_ascii=True,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'multi_source_evidence_recorded','output':plan['output'],'sha256':digest,
            'retrieved_count':r['retrieved_count'],'distinct_text_count':r['distinct_text_count'],'claims_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Research evidence unavailable; inspect exact approved URLs and report scope'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
