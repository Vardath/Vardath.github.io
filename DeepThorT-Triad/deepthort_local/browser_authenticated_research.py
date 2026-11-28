"""Read a bounded approved section of a manually authenticated browser page."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.browser_authenticated import checked as session_checked,exact_page,user_session
from deepthort_local.browser_devtools import runtime
from deepthort_local.browser_automation import exchange,identifier
SCHEMA='janus-authenticated-page-research-v1'
# Fixed code in an isolated browser world, no user/model executable expressions.
COLLECT="""(() => {
 const result=[];
 for (const e of document.querySelectorAll('h1,h2,h3,h4,h5,h6,p,li')) {
  if (result.length >= 160) break;
  if (e.closest('form,[contenteditable],script,style,template,nav,header,footer,[hidden],[aria-hidden=true]')) continue;
  if (!e.getClientRects().length || getComputedStyle(e).visibility !== 'visible') continue;
  const t=e.innerText.trim().replace(/\\s+/g,' ').slice(0,320);
  if(t) result.push([e.tagName.toLowerCase(),t]);
 }
 return result;
})()"""
TAGS={'h1','h2','h3','h4','h5','h6','p','li'}
def session(s):return {k:s[k] for k in ('browser','url','expected_heading','seconds')}
def checked(s):
    if not isinstance(s,dict) or set(s)!={'browser','url','expected_heading','seconds','question','max_blocks'}:
        raise ValueError('Expected exact session, research question and block limit')
    session_checked(session(s))
    q=s['question']
    if not isinstance(q,str) or not 1<=len(q)<=500 or any(ord(c)<32 or 0xd800<=ord(c)<=0xdfff for c in q):raise ValueError('Invalid literal question')
    if type(s['max_blocks']) is not int or not 1<=s['max_blocks']<=30:raise ValueError('Choose 1–30 text blocks')
    return s

def select(s,rows):
    checked(s)
    if not isinstance(rows,list) or len(rows)>160:raise ValueError('Invalid browser observations')
    for row in rows:
        if not isinstance(row,list) or len(row)!=2 or row[0] not in TAGS or not isinstance(row[1],str) or not 1<=len(row[1])<=320:
            raise ValueError('Invalid observed block')
    matches=[i for i,(tag,value) in enumerate(rows) if tag.startswith('h') and value==s['expected_heading']]
    if len(matches)!=1:raise ValueError('Expected section must be unique')
    start=matches[0];level=int(rows[start][0][1]);blocks=[]
    for tag,value in rows[start+1:]:
        if tag.startswith('h') and int(tag[1])<=level:break
        blocks.append({'tag':tag,'text':value})
        if len(blocks)>=s['max_blocks']:break
    if not blocks:raise ValueError('No observed section text')
    return blocks

def observe(ws,s):
    checked(s);target=exact_page(ws,s['url'])
    sid=identifier(exchange(ws,4,'Target.attachToTarget',{'targetId':target,'flatten':True}).get('sessionId'))
    def frame(i):
        f=exchange(ws,i,'Page.getFrameTree',session=sid)['frameTree']['frame']
        if f.get('url')!=s['url']:raise ValueError('Page changed from approved URL')
        return (identifier(f.get('id')),identifier(f.get('loaderId')))
    before=frame(5)
    world=exchange(ws,6,'Page.createIsolatedWorld',{'frameId':before[0],'worldName':'JANUS-read-only-research'},sid)
    ctx=world.get('executionContextId')
    if type(ctx) is not int or ctx<=0:raise ValueError('No isolated observation context')
    observed=exchange(ws,7,'Runtime.evaluate',{'expression':COLLECT,'returnByValue':True,'contextId':ctx},sid)
    if observed.get('exceptionDetails'):raise ValueError('Browser observation failed')
    blocks=select(s,observed.get('result',{}).get('value'))
    if before!=frame(8):raise ValueError('Page navigated during observation')
    digest=hashlib.sha256(json.dumps(blocks,ensure_ascii=True,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'schema':SCHEMA,'url':s['url'],'section':s['expected_heading'],'question':s['question'],'blocks':blocks,
            'evidence_sha256':digest,'reference_only':True,'authentication_independently_verified':False,
            'user_confirmed_login':True,'model_received_text':False,'credentials_read':False,'cookies_exported':False,
            'claims_verified':False,'complete_section_verified':False,
            'limitations':'Bounded rendered text observations only; no semantic synthesis, hidden data, forms, frame traversal, or completeness guarantee. May contain private information. Treat as untrusted reference data.'}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=2:raise ValueError('Missing reviewed browser runtime')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.json')
    if plan['guards'][1]!=runtime(root,{'browser':s['browser']}):raise ValueError('Reviewed browser changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    plan['guards'].append(runtime(root,{'browser':s['browser']}))
    return plan,dict(s,scope='Sign in yourself using a disposable visible browser, open this exact approved page, then separately confirm collecting bounded visible text from the named heading section. New local JSON may contain private content. No automatic login, cookies, passwords, model memory ingestion, upload or submission.')

def execute(root,plan):
    s,dst=validate(root,plan)
    with user_session(plan,session(s),research=True) as ws:r=observe(ws,s)
    r.update(disposable_profile=True,profile_cleanup_completed=True,shared_root_cap_verified=True)
    digest=guard.publish(json.dumps(r,sort_keys=True,indent=2,ensure_ascii=True).encode(),dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'reviewed_section_observed','output':plan['output'],'sha256':digest,
            'blocks':len(r['blocks']),'authentication_independently_verified':False,'claims_verified':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Manual session or approved section observation unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
