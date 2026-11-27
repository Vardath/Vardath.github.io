"""Bounded, user-reviewed same-origin static website crawl; conservative robots handling."""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.website_monitor import checked_url,stopped
from deepthort_local.webpage_retrieval import fetch_page

SCHEMA='janus-website-crawling-v1'
MAX_PAGES=5
MAX_DEPTH=2
MAX_SECONDS=120
USER_AGENT='JANUS-local-research'
def safe_path(path):
    if (not isinstance(path,str) or not re.fullmatch(r'/(?:[A-Za-z0-9._~-]+/)*[A-Za-z0-9._~-]*',path)
            or any(p in ('.','..') for p in path.split('/'))):
        raise ValueError('Crawl paths must be plain ASCII path segments, no encoded escapes or traversal')
    return path
def checked(s):
    if not isinstance(s,dict) or set(s)!={'seed','path_prefix','max_pages','max_depth'}:
        raise ValueError('Expected seed, explicit directory prefix, page limit and depth')
    _,path=checked_url(s['seed']);safe_path(path)
    prefix=safe_path(s['path_prefix'])
    if not prefix.endswith('/') or not path.startswith(prefix):
        raise ValueError('Seed must be inside an explicitly reviewed directory prefix')
    if type(s['max_pages']) is not int or not 1<=s['max_pages']<=MAX_PAGES or type(s['max_depth']) is not int or not 0<=s['max_depth']<=MAX_DEPTH:
        raise ValueError('Choose 1–5 page attempts and depth 0–2')
    return s

def robots_policy(text):
    """Conservatively combine relevant groups; unsupported rules fail closed.
    A successful, parseable text robots response is required, even if a server
    would conventionally treat a missing robots file as allowing access.
    """
    if not isinstance(text,str) or not text or len(text)>100000:raise ValueError('No readable robots policy')
    groups=[];agents=[];rules=[];has_rule=False
    def save():
        if agents:groups.append((tuple(agents),tuple(rules)))
    for line in text.splitlines():
        line=line.partition('#')[0].strip()
        if not line:continue
        key,sep,value=line.partition(':')
        if not sep:raise ValueError('Unrecognized robots policy line')
        key=key.strip().casefold();value=value.strip()
        if key=='user-agent':
            if not value or not re.fullmatch(r'[A-Za-z0-9_*.-]+',value):raise ValueError('Unsupported robots user-agent')
            if has_rule:
                save();agents=[];rules=[];has_rule=False
            agents.append(value.casefold())
        elif key in ('allow','disallow','crawl-delay','request-rate'):
            if not agents:raise ValueError('Robots directive without agent')
            rules.append((key,value));has_rule=True
        # Sitemap and other directives do not authorize fetching them.
    save()
    if not groups:raise ValueError('No robots agent groups')
    matching=[r for a,r in groups if any(x=='*' or x in USER_AGENT.casefold() for x in a)]
    deny=[];delay=2.0
    for group in matching:
        for key,value in group:
            if key=='request-rate':raise ValueError('Unsupported robots request rate')
            if key=='crawl-delay':
                if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?',value):raise ValueError('Invalid crawl delay')
                delay=max(delay,float(value))
                if delay>10:raise ValueError('Site requires a longer delay than this bounded crawl supports')
            if key=='disallow' and value:
                if not value.startswith('/') or '%' in value or any(ord(c)>126 for c in value):
                    raise ValueError('Unsupported robots path encoding')
                # Ignoring Allow overrides is intentionally more restrictive.
                if '$' in value[:-1]:raise ValueError('Unsupported robots rule')
                anchored=value.endswith('$');pattern=value[:-1] if anchored else value
                deny.append(re.compile('^'+re.escape(pattern).replace(r'\*','.*')+('$' if anchored else '')))
    return lambda path:not any(p.match(path) for p in deny),delay

def allowed_link(url,host,prefix):
    try:
        h,p=checked_url(url);safe_path(p)
    except (TypeError,ValueError):return False
    return h==host and p.startswith(prefix)

def crawl(s,*,approved=False,cancelled=None,retrieve=fetch_page,clock=time.monotonic,sleep=time.sleep):
    checked(s)
    if approved is not True:raise ValueError('Explicit crawl scope consent required')
    host,_=checked_url(s['seed']);prefix=s['path_prefix'];deadline=clock()+MAX_SECONDS
    def stop():return bool((cancelled and cancelled()) or clock()>deadline)
    def check():
        if stop():raise TimeoutError('Crawl stopped')
    def wait(delay):
        until=clock()+delay
        while clock()<until:
            check();sleep(min(.25,until-clock()))
    robots_url='https://'+host+'/robots.txt';check()
    robots=retrieve(robots_url,approved=True,cancelled=stop)
    if robots.get('url')!=robots_url or robots.get('mime')!='text/plain':
        raise ValueError('Expected exact plain-text robots response')
    permit,delay=robots_policy(robots['text'])
    pending=deque([(s['seed'],0,None)]);seen={s['seed']};attempts=[];pages=[];blocked=[]
    while pending and len(attempts)<s['max_pages']:
        check();url,depth,parent=pending.popleft();_,path=checked_url(url)
        if not permit(path):
            blocked.append({'url':url,'reason':'robots_disallow'});continue
        wait(delay);check()
        try:
            page=retrieve(url,approved=True,cancelled=stop);check()
            if page.get('url')!=url or page.get('reference_only') is not True or page.get('script_executed') is not False:
                raise ValueError('Page identity mismatch')
        except (OSError,ValueError,UnicodeError):
            check();attempts.append({'url':url,'depth':depth,'status':'failed'});continue
        attempts.append({'url':url,'depth':depth,'status':'retrieved'})
        pages.append({'depth':depth,'discovered_from':parent,'evidence':page})
        if depth<s['max_depth']:
            for link in page['discovered_links']:
                if len(seen)>=100:break
                if link not in seen and allowed_link(link,host,prefix):
                    seen.add(link);pending.append((link,depth+1,url))
    return {'schema':'janus-website-crawl-result-v1','seed':s['seed'],'path_prefix':prefix,
            'robots_url':robots_url,'robots_response_sha256':robots['response_sha256'],'minimum_delay_seconds':delay,
            'attempts':attempts,'pages':pages,'robots_blocked':blocked,'queued_not_visited':len(pending),
            'page_limit':s['max_pages'],'depth_limit':s['max_depth'],'external_links_followed':False,
            'site_completeness_verified':False,'claims_verified':False,'reference_only':True,
            'limitations':'Bounded static same-host crawl; requires successful plain-text robots.txt; conservative disallow rules override allows. No query URLs, scripts, redirects, authentication or site completeness guarantee.'}

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,network_consent='Read same-host robots.txt and up to the reviewed number of pages inside this directory prefix, following permitted discovered static links; write new JSON. No external host or query URL.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def execute(root,plan,*,run=crawl):
    s,dst,_=validate(root,plan);r=run(s,approved=True)
    if r.get('seed')!=s['seed'] or r.get('path_prefix')!=s['path_prefix'] or r.get('external_links_followed') is not False:raise ValueError('Crawl receipt mismatch')
    payload=json.dumps(r,ensure_ascii=True,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'bounded_crawl_recorded','output':plan['output'],'sha256':digest,'pages':len(r['pages']),
            'attempts':len(r['attempts']),'site_completeness_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Crawl unavailable; check reviewed scope, robots permission and public network'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
