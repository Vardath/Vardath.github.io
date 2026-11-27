"""Goal-directed static HTTPS navigation within an explicitly reviewed public scope."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.website_crawling import checked as crawl_checked,allowed_link,robots_policy
from deepthort_local.website_monitor import checked_url
from deepthort_local.webpage_retrieval import fetch_page
from deepthort_local.webpage_elements import extract_elements
from deepthort_local.search_interpretation import terms
from deepthort_local.long_form_writing import literal

SCHEMA='janus-static-navigation-v1'
MAX_SECONDS=120
MAX_FRONTIER=100
HEADINGS={'h1','h2','h3','h4','h5','h6'}

def scope(s):return {k:s[k] for k in ('seed','path_prefix','max_pages','max_depth')}
def checked(s):
    if not isinstance(s,dict) or set(s)!={'seed','path_prefix','max_pages','max_depth','target_heading'}:raise ValueError('Expected navigation scope and exact target heading')
    crawl_checked(scope(s));literal(s['target_heading'],160)
    if not terms(s['target_heading']):raise ValueError('Choose a searchable target heading')
    return s
def norm(s):return ' '.join(s.casefold().split())
def score(row,goal):
    label=terms(row['text']+' '+row['aria_label'])
    path=terms(checked_url(row['href'])[1].replace('/',' ').replace('-',' ').replace('_',' '))
    return 3*len(goal&label)+len(goal&path)

def navigate(s,*,approved=False,cancelled=None,retrieve=fetch_page,clock=time.monotonic,sleep=time.sleep):
    checked(s)
    if approved is not True:raise ValueError('Explicit navigation scope approval required')
    host,_=checked_url(s['seed']);prefix=s['path_prefix'];deadline=clock()+MAX_SECONDS
    goal=terms(s['target_heading'])
    def stop():return bool((cancelled and cancelled()) or clock()>=deadline)
    def check():
        if stop():raise TimeoutError('Navigation stopped')
    def wait(delay):
        until=clock()+delay
        while clock()<until:
            check();sleep(min(.25,until-clock()))
    robots_url='https://'+host+'/robots.txt';check()
    robots=retrieve(robots_url,approved=True,cancelled=stop)
    if robots.get('url')!=robots_url or robots.get('mime')!='text/plain':raise ValueError('Exact robots text required')
    permit,delay=robots_policy(robots['text'])
    pending=[{'url':s['seed'],'depth':0,'parent':None,'link_locator':None,'link_text':None,'score':0}]
    seen={s['seed']};attempts=[];blocked=[];matched=None
    while pending and len(attempts)<s['max_pages']:
        check();pending.sort(key=lambda r:(-r['score'],r['depth'],r['url']))
        current=pending.pop(0);url=current['url'];_,path=checked_url(url)
        if not permit(path):
            blocked.append({'url':url,'reason':'robots_disallow'});continue
        wait(delay);check()
        try:
            page=retrieve(url,approved=True,cancelled=stop,extractor=extract_elements)
            if page.get('url')!=url or page.get('schema')!='janus-static-elements-v1' or page.get('script_executed') is not False or page.get('controls_activated') is not False:
                raise ValueError('Inspection identity mismatch')
        except (OSError,ValueError,UnicodeError):
            check();attempts.append({**current,'status':'unavailable'});continue
        check()
        attempt={**current,'status':'retrieved','response_sha256':page['response_sha256'],'elements_truncated':page['elements_truncated']}
        attempts.append(attempt)
        matches=[r for r in page['elements'] if r['tag'] in HEADINGS and norm(r['text'])==norm(s['target_heading'])]
        if matches:
            matched={'url':url,'response_sha256':page['response_sha256'],'headings':[{'tag':r['tag'],'locator':r['locator'],'text':r['text']} for r in matches]}
            break
        if current['depth']>=s['max_depth']:continue
        options=[]
        for row in page['elements']:
            link=row.get('href')
            if row['tag']!='a' or not link or link in seen or not allowed_link(link,host,prefix):continue
            options.append((score(row,goal),link,row))
        for rank,link,row in sorted(options,key=lambda x:(-x[0],x[1],x[2]['locator'])):
            if len(seen)>=MAX_FRONTIER:break
            if link in seen:continue
            seen.add(link);pending.append({'url':link,'depth':current['depth']+1,'parent':url,
                'link_locator':row['locator'],'link_text':row['text'],'score':rank})
    check()
    path=[]
    if matched:
        lookup={r['url']:r for r in attempts};url=matched['url']
        while url is not None:
            row=lookup[url];path.append({'url':url,'link_locator':row['link_locator'],'link_text':row['link_text']});url=row['parent']
        path.reverse()
    return {'schema':'janus-static-navigation-result-v1','reviewed_scope':scope(s),'target_heading':s['target_heading'],
        'status':'heading_observed' if matched else 'heading_not_observed_within_budget',
        'match':matched,'navigation_path':path,'attempts':attempts,'robots_blocked':blocked,
        'robots_response_sha256':robots['response_sha256'],'minimum_delay_seconds':delay,'frontier_remaining':len(pending),
        'script_executed':False,'controls_activated':False,'rendered_browser_verified':False,
        'limitations':'Read-only static HTTPS path finding, ranked by link text and URL terms. Exact source heading observation only; absence does not establish site-wide absence. No authentication, JavaScript, redirect or external navigation.'}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,network_consent='Read robots.txt and autonomously visit up to the reviewed page budget within this public host and directory; rank static links and stop on exact heading. No forms, credentials, scripts or external links.')
def execute(root,plan):
    s,dst,_=validate(root,plan);r=navigate(s,approved=True)
    payload=json.dumps(r,ensure_ascii=True,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':r['status'],'output':plan['output'],'sha256':digest,
            'attempts':len(r['attempts']),'target_observed':r['match'] is not None,'rendered_browser_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Navigation unavailable; inspect reviewed scope, robots and network'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
