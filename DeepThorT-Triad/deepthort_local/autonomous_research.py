"""Bounded autonomous collection and evidence-gap analysis within reviewed public sites."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.website_crawling import checked as crawl_checked, crawl, allowed_link
from deepthort_local.website_monitor import checked_url
from deepthort_local.multi_source_research import validated_page,excerpts
from deepthort_local.search_interpretation import terms
from deepthort_local.long_form_writing import literal

SCHEMA='janus-autonomous-research-v1'
MAX_SECONDS=240

def checked(s):
    if not isinstance(s,dict) or set(s)!={'question','sites'}:raise ValueError('Expected question and reviewed site scopes')
    literal(s['question'],600)
    if not terms(s['question']):raise ValueError('Question has no searchable terms')
    if not isinstance(s['sites'],list) or not 2<=len(s['sites'])<=3:raise ValueError('Choose 2–3 reviewed public sites')
    hosts=set();budget=0
    for site in s['sites']:
        crawl_checked(site)
        host,_=checked_url(site['seed'])
        if host in hosts:raise ValueError('Use distinct site hostnames')
        hosts.add(host);budget+=site['max_pages']
    if budget>8:raise ValueError('Total page attempt budget must not exceed eight')
    return s

def collect(s,*,approved=False,cancelled=None,run=crawl,clock=time.monotonic):
    checked(s)
    if approved is not True:raise ValueError('Explicit approval for all reviewed scopes required')
    deadline=clock()+MAX_SECONDS
    def stop():return bool((cancelled and cancelled()) or clock()>=deadline)
    question_terms=terms(s['question']);remaining=set(question_terms)
    matrix={t:[] for t in sorted(question_terms)};sources=[];sites=[];digests={}
    for site in s['sites']:
        if stop():raise TimeoutError('Research stopped')
        host,_=checked_url(site['seed'])
        focus=frozenset(remaining or question_terms)
        def priority(url):
            return -len(terms(checked_url(url)[1].replace('/',' ').replace('-',' ').replace('_',' '))&focus)
        try:r=run(site,approved=True,cancelled=stop,link_priority=priority)
        except (OSError,ValueError,UnicodeError):
            if stop():raise TimeoutError('Research stopped')
            sites.append({'seed':site['seed'],'status':'unavailable'});continue
        if stop():raise TimeoutError('Research stopped')
        if (r.get('seed')!=site['seed'] or r.get('path_prefix')!=site['path_prefix']
            or r.get('external_links_followed') is not False or r.get('reference_only') is not True
            or not isinstance(r.get('pages'),list) or not isinstance(r.get('attempts'),list)
            or len(r['pages'])>len(r['attempts']) or len(r['attempts'])>site['max_pages']):
            raise ValueError('Crawl evidence does not match approved scope')
        visited=set()
        for row in r['pages']:
            p=row['evidence'];url=p['url']
            if url in visited or not allowed_link(url,host,site['path_prefix']):
                raise ValueError('Crawl returned unapproved page')
            visited.add(url);validated_page(url,p)
            ident='R'+str(len(sources)+1);digest=p['text_sha256']
            duplicate=digests.get(digest);digests.setdefault(digest,ident)
            found=question_terms&terms(p['text'])
            if duplicate is None:
                for term in found:matrix[term].append(ident)
                remaining-=found
            sources.append({'id':ident,'hostname':host,'url':url,'duplicate_text_of':duplicate,
                'matched_terms':sorted(found),'excerpts':excerpts(p['text'],question_terms),'evidence':p})
        sites.append({'seed':site['seed'],'status':'collected','attempts':len(r['attempts']),
            'retrieved':len(visited),'priority_terms':sorted(focus),'robots_response_sha256':r['robots_response_sha256']})
    if stop():raise TimeoutError('Research stopped')
    return {'schema':'janus-autonomous-research-result-v1','question':s['question'],
        'reviewed_sites':s['sites'],'site_results':sites,'sources':sources,
        'term_source_matrix':matrix,'uncovered_terms':sorted(remaining),
        'distinct_text_count':len(digests),'retrieved_count':len(sources),
        'claims_verified':False,'source_independence_verified':False,'reference_only':True,
        'limitations':'Autonomous static link collection inside reviewed host/path/depth/attempt bounds; robots required. Gap-directed lexical URL ranking and literal excerpts only, not semantic synthesis, unrestricted search, independent corroboration or fact verification.'}

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,network_consent='Read each exact site robots.txt and autonomously follow permitted same-host static links within each approved directory, depth and page attempt budget. Total at most eight page attempts plus robots; question stays local. No scripts, credentials, redirects or external-host links.')
def execute(root,plan):
    s,dst,_=validate(root,plan);r=collect(s,approved=True)
    payload=json.dumps(r,ensure_ascii=True,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'bounded_research_recorded','output':plan['output'],'sha256':digest,
            'retrieved_count':r['retrieved_count'],'distinct_text_count':r['distinct_text_count'],
            'uncovered_terms':r['uncovered_terms'],'claims_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Research unavailable; inspect reviewed scopes, robots and network'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
