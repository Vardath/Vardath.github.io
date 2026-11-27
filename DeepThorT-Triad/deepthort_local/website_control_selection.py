"""Reviewed static control selection and exact public link navigation.

A source locator is never treated as a live browser selector. Only explicitly
reviewed GET link navigation is implemented; buttons and form fields are
identified but not activated.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.structured_source import strict_json
from deepthort_local.website_monitor import checked_url
from deepthort_local.website_crawling import safe_path,allowed_link,robots_policy
from deepthort_local.webpage_retrieval import fetch_page
from deepthort_local.webpage_elements import extract_elements,MAX_RESULTS

SCHEMA='janus-static-control-selection-v1'
EXTRA=('inspection','.json')
HASH=re.compile(r'[a-f0-9]{64}\Z')
LOCATOR=re.compile(r'(?:/[a-z][a-z0-9-]*\[[1-9][0-9]*\]){1,80}\Z')
TAGS={'a','button','input','textarea','select','label','form'}

def checked(s):
    if not isinstance(s,dict) or set(s)!={'inspection','locator','tag','action','path_prefix','destination'}:
        raise ValueError('Expected exact static control selection specification')
    if not isinstance(s['inspection'],str) or not isinstance(s['locator'],str) or len(s['locator'])>2000 or not LOCATOR.fullmatch(s['locator']):
        raise ValueError('Invalid inspection or structural locator')
    if s['tag'] not in TAGS or s['action'] not in ('identify','read_link'):
        raise ValueError('Unsupported static control or action')
    prefix=safe_path(s['path_prefix'])
    if not prefix.endswith('/'):raise ValueError('Review an exact directory prefix')
    if s['action']=='identify':
        if s['destination'] is not None:raise ValueError('Identification must not specify a destination')
    else:
        if s['tag']!='a':raise ValueError('Only public anchor navigation supported')
        checked_url(s['destination'])
    return s

def selected(s,report):
    if (not isinstance(report,dict) or report.get('schema')!='janus-static-elements-v1'
        or report.get('script_executed') is not False or report.get('controls_activated') is not False
        or report.get('rendered_dom_verified') is not False or report.get('reference_only') is not True
        or not isinstance(report.get('response_sha256'),str) or not HASH.fullmatch(report['response_sha256'])
        or not isinstance(report.get('elements'),list) or len(report['elements'])>MAX_RESULTS):
        raise ValueError('Invalid static inspection evidence')
    url=report['url'];host,_=checked_url(url)
    if not allowed_link(url,host,s['path_prefix']):raise ValueError('Source outside reviewed directory')
    rows=[r for r in report['elements'] if isinstance(r,dict) and r.get('locator')==s['locator']]
    if len(rows)!=1 or rows[0].get('tag')!=s['tag']:raise ValueError('Exact control not uniquely observed')
    row=rows[0]
    if s['action']=='read_link':
        if row.get('href')!=s['destination'] or row.get('disabled_attribute') is not False:
            raise ValueError('Reviewed anchor destination or enabled state mismatch')
        if not allowed_link(s['destination'],host,s['path_prefix']) or s['destination']==url:
            raise ValueError('Only a distinct same-host in-scope destination is supported')
    return {'url':url,'response_sha256':report['response_sha256'],'control':row}

def read_review(root,plan):
    s,dst,src=guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    report=strict_json(guard.exact(src,plan['guards'][1],guard.MAX_INPUT).decode('utf-8-sig'))
    return s,dst,selected(s,report)

def run(s,evidence,*,approved=False,cancelled=None,retrieve=fetch_page,clock=time.monotonic,sleep=time.sleep):
    checked(s)
    if approved is not True:raise ValueError('Explicit approval required')
    # Re-reading an exact source and its reviewed destination is the only
    # permitted network interaction. No cookie jar, credentials or forms.
    source=evidence['url'];host,source_path=checked_url(source);prefix=s['path_prefix']
    if not allowed_link(source,host,prefix):raise ValueError('Source outside scope')
    if s['action']=='identify':
        if cancelled and cancelled():raise TimeoutError('Selection cancelled')
        return {'status':'historical_control_identified','source':evidence,'destination':None,
                'source_rechecked':False,'link_read':False,'control_activated':False,'rendered_browser_verified':False}
    target=s['destination']
    if not allowed_link(target,host,prefix) or target==source:raise ValueError('Destination outside scope')
    deadline=clock()+90
    def stop():return bool((cancelled and cancelled()) or clock()>=deadline)
    def check():
        if stop():raise TimeoutError('Selection cancelled')
    def wait(delay):
        until=clock()+delay
        while clock()<until:
            check();sleep(min(.25,until-clock()))
    check();robots_url='https://'+host+'/robots.txt'
    robots=retrieve(robots_url,approved=True,cancelled=stop)
    if robots.get('url')!=robots_url or robots.get('mime')!='text/plain':raise ValueError('Exact robots text required')
    permit,delay=robots_policy(robots['text'])
    if not permit(source_path) or not permit(checked_url(target)[1]):raise ValueError('Robots policy forbids reviewed read')
    wait(delay);check()
    observed=selected(s,retrieve(source,approved=True,cancelled=stop,extractor=extract_elements))
    if observed!=evidence:raise ValueError('Source response or selected control changed since approval')
    wait(delay);check()
    page=retrieve(target,approved=True,cancelled=stop)
    check()
    if (page.get('url')!=target or page.get('schema')!='janus-webpage-evidence-v1'
        or page.get('script_executed') is not False or page.get('reference_only') is not True
        or page.get('links_followed') is not False):raise ValueError('Destination evidence mismatch')
    return {'status':'reviewed_link_read','source':observed,'destination':page,
            'robots_response_sha256':robots['response_sha256'],'source_rechecked':True,'link_read':True,
            'control_activated':False,'rendered_browser_verified':False}

def review(root,source,output,exclude=()):
    plan,_=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    s,_,evidence=read_review(root,plan)
    return plan,dict(s,selected_control=evidence,network_consent=(
        'Offline identification of historical inspected control only.' if s['action']=='identify' else
        'Read exact host robots.txt, recheck exact source HTML bytes and control, then read this reviewed same-host HTTPS destination once. No live click, script, form, cookie, redirect or credentials.'))
def execute(root,plan):
    s,dst,evidence=read_review(root,plan);r=run(s,evidence,approved=True)
    payload=json.dumps({'schema':'janus-static-control-result-v1',**r},ensure_ascii=True,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:read_review(root,plan))
    return {'schema':SCHEMA,'status':r['status'],'output':plan['output'],'sha256':digest,
            'source_rechecked':r['source_rechecked'],'link_read':r['link_read'],'rendered_browser_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Control selection unavailable; verify approved source and destination'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
