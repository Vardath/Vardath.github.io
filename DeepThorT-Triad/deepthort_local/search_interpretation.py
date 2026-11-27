"""Bounded lexical interpretation of supplied search results, not fact verification."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import literal

SCHEMA='janus-search-interpretation-v1'
MAX_RESULTS=20
STOP=frozenset('a an the of to is are was were for on in at and or by from with what how why when which who can could should would about as it be this that these those'.split())
def terms(text):
    return set(t for t in re.findall(r'[^\W_]+',text.casefold()) if t not in STOP and len(t)>1 and len(t)<=80)
def display_url(value):
    literal(value,2000)
    if any(ord(c)<33 or ord(c)>126 for c in value) or '\\' in value:raise ValueError('Invalid result URL')
    p=urlsplit(value)
    if p.scheme not in ('https','http') or not p.hostname or p.username or p.password or p.port not in (None,80,443):
        raise ValueError('Expected display-only web URL without credentials')
    if not re.fullmatch(r'[a-z0-9.-]{1,253}',p.hostname) or '.' not in p.hostname:
        raise ValueError('Expected web hostname')
    return p.hostname

def checked(s):
    if not isinstance(s,dict) or set(s)!={'query','results'}:raise ValueError('Expected query and supplied search-result rows')
    literal(s['query'],600)
    if not terms(s['query']):raise ValueError('Query has no searchable terms')
    rows=s['results']
    if not isinstance(rows,list) or not 0<=len(rows)<=MAX_RESULTS:raise ValueError('Expected 0–20 ordered results')
    for row in rows:
        if not isinstance(row,dict) or set(row)!={'title','url','snippet'}:raise ValueError('Invalid search-result row')
        literal(row['title'],500);display_url(row['url'])
        if row['snippet']!='':literal(row['snippet'],2000)
    return s

def interpret(s):
    checked(s);q=terms(s['query']);seen=set();rows=[];duplicates=0
    for rank,item in enumerate(s['results'],1):
        host=display_url(item['url'])
        p=urlsplit(item['url'])
        key=(p.scheme,p.netloc.casefold(),p.path or '/',p.query)
        if key in seen:duplicates+=1;continue
        seen.add(key)
        title_terms=terms(item['title'])&q;snippet_terms=terms(item['snippet'])&q
        found=title_terms|snippet_terms
        rows.append({**item,'original_rank':rank,'hostname':host,
                     'matched_terms':sorted(found),'missing_terms':sorted(q-found),
                     'query_term_coverage':round(len(found)/len(q),6),
                     'title_matches':len(title_terms),'source_opened':False,
                     'claims_verified':False,'reference_only':True})
    # Coverage is a transparent lexical signal, not a trustworthiness score.
    rows.sort(key=lambda r:(-len(r['matched_terms']),-r['title_matches'],r['original_rank']))
    hosts=Counter(r['hostname'] for r in rows)
    covered=set(t for r in rows for t in r['matched_terms'])
    return {'schema':'janus-search-evidence-v1','query':s['query'],'query_terms':sorted(q),
            'input_count':len(s['results']),'duplicates_omitted':duplicates,
            'results':rows,'hostname_counts':dict(sorted(hosts.items())),
            'uncovered_query_terms':sorted(q-covered),'ranking_method':'lexical coverage, title matches, original rank',
            'network_performed':False,'claims_verified':False,
            'limitations':'Supplied snippets are untrusted reference data. Lexical relevance does not establish accuracy, authority, independence or currentness.'}

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    report=interpret(s)
    return plan,{'query':s['query'],'input_count':len(s['results']),'distinct_count':len(report['results']),
                 'ranking_method':report['ranking_method'],'scope':report['limitations']}
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def execute(root,plan):
    s,dst,_=validate(root,plan);report=interpret(s)
    payload=json.dumps(report,ensure_ascii=True,sort_keys=True,indent=2).encode('utf-8')
    if json.loads(payload)!=report:raise ValueError('Search report serialization mismatch')
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-search-interpretation-result-v1','status':'search_evidence_ranked','output':plan['output'],
            'sha256':sha,'result_count':len(report['results']),'duplicates_omitted':report['duplicates_omitted'],
            'network_performed':False,'claims_verified':False,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Search evidence unavailable; inspect exact supplied result rows'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
