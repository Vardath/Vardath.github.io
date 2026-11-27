"""Native browser automation of a reviewed inert local form replay; no live website."""
from __future__ import annotations
import argparse
import html
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.structured_source import strict_json
from deepthort_local.browser_devtools import runtime,native_connection,inspect,call,MAX_MESSAGE
from deepthort_local.website_form_completion import SCHEMA as FORM_SCHEMA
from deepthort_local.rest_api import key

SCHEMA='janus-browser-form-replay-v1'
EXTRA=('form_receipt','.json')
TYPES={'text','email','url','tel','search',None}
IDS=re.compile(r'[A-Za-z0-9-]{1,80}')
METHODS={'Target.attachToTarget','Page.getFrameTree','Page.setDocumentContent','DOM.getDocument',
         'DOM.querySelector','DOM.focus','Input.insertText','Runtime.evaluate','Page.createIsolatedWorld'}
# Fixed host-owned expression, never constructed from page or model instructions.
VERIFY="Array.from(document.querySelectorAll('input[data-janus]'), e => e.value)"

def checked(s):
    if not isinstance(s,dict) or set(s)!={'browser','form_receipt'} or s['browser'] not in ('chrome','edge') or not isinstance(s['form_receipt'],str):
        raise ValueError('Choose a browser and reviewed static form receipt')
    return s

def fields(report):
    if (not isinstance(report,dict) or report.get('schema')!=FORM_SCHEMA or report.get('submitted') is not False
        or report.get('browser_used') is not False or report.get('form_filled_in_browser') is not False
        or not isinstance(report.get('fields'),list) or not 1<=len(report['fields'])<=24):
        raise ValueError('Expected prior static form preparation receipt')
    rows=[];names=set()
    for f in report['fields']:
        if not isinstance(f,dict) or set(f)!={'locator','name','value','type'} or f['type'] not in TYPES:
            raise ValueError('Only simple text-like replay controls supported')
        name=key(f['name']);v=f['value']
        if name in names or not isinstance(v,str) or len(v)>2000 or any(ord(c)<32 or 0xD800<=ord(c)<=0xDFFF for c in v):
            raise ValueError('Duplicate name or unsupported value')
        names.add(name);rows.append({'name':name,'value':v})
    return rows

def document(rows):
    # Reconstruct only the reviewed names, never raw website HTML or scripts.
    parts=['<!doctype html><html><head><meta charset="utf-8">',
           '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; form-action \'none\'; base-uri \'none\'">',
           '<title>JANUS inert form replay</title></head><body><main>']
    for i,row in enumerate(rows):
        parts.append(f'<label for="f{i}">{html.escape(row["name"])}</label><input id="f{i}" data-janus="1" type="text" autocomplete="off">')
    return ''.join(parts)+'</main></body></html>'

def exchange(ws,ident,method,params=None,session=None):
    if method not in METHODS or type(ident) is not int or not 3<=ident<=100:
        raise ValueError('Unapproved browser automation command')
    if session is not None and (not isinstance(session,str) or not IDS.fullmatch(session)):
        raise ValueError('Invalid attached session')
    message={'id':ident,'method':method}
    if params is not None:message['params']=params
    if session is not None:message['sessionId']=session
    ws.send(json.dumps(message,separators=(',',':'),ensure_ascii=True))
    for _ in range(30):
        raw=ws.recv()
        if not isinstance(raw,str) or not 1<=len(raw)<=MAX_MESSAGE:raise ValueError('Invalid CDP reply')
        reply=strict_json(raw)
        if not isinstance(reply,dict):raise ValueError('Invalid CDP message')
        if reply.get('id')==ident:
            if reply.get('sessionId')!=session or 'error' in reply or not isinstance(reply.get('result'),dict):
                raise ValueError('CDP session or result mismatch')
            return reply['result']
        if 'id' in reply:raise ValueError('Unexpected CDP response ID')
    raise ValueError('No matching CDP reply')

def identifier(v):
    if not isinstance(v,str) or not IDS.fullmatch(v):raise ValueError('Invalid browser identity')
    return v

def node(v):
    if type(v) is not int or v<=0:raise ValueError('DOM node unavailable')
    return v

def replay(ws,rows):
    base=inspect(ws)
    targets=call(ws,'Target.getTargets',3)
    pages=[x for x in targets['targetInfos'] if x.get('type')=='page']
    if len(pages)!=1 or pages[0].get('url')!='about:blank':raise ValueError('Disposable page changed')
    target=identifier(pages[0].get('targetId'))
    attached=exchange(ws,4,'Target.attachToTarget',{'targetId':target,'flatten':True})
    session=identifier(attached.get('sessionId'))
    frame=exchange(ws,5,'Page.getFrameTree',session=session)['frameTree']['frame']
    if frame.get('url')!='about:blank':raise ValueError('Unexpected page navigation')
    frame_id=identifier(frame.get('id'))
    exchange(ws,6,'Page.setDocumentContent',{'frameId':frame_id,'html':document(rows)},session)
    root=node(exchange(ws,7,'DOM.getDocument',{'depth':1},session)['root']['nodeId'])
    ident=8
    for i,row in enumerate(rows):
        field=node(exchange(ws,ident,'DOM.querySelector',{'nodeId':root,'selector':'#f'+str(i)},session)['nodeId'])
        ident+=1
        exchange(ws,ident,'DOM.focus',{'nodeId':field},session);ident+=1
        if row['value']:
            exchange(ws,ident,'Input.insertText',{'text':row['value']},session);ident+=1
    observed=exchange(ws,ident,'Runtime.evaluate',{'expression':VERIFY,'returnByValue':True},session)
    if observed.get('exceptionDetails') or observed.get('result',{}).get('value')!=[x['value'] for x in rows]:
        raise ValueError('Native DOM values do not match reviewed literals')
    return {'version':base['version'],'controls_filled':len(rows),'dom_values_verified':True,
            'native_browser_input_used':True,'live_website_filled':False,'submitted':False,'external_site_tested':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=3:
        raise ValueError('Missing reviewed form and browser guards')
    s,dst,src=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    if plan['guards'][2]!=runtime(root,{'browser':s['browser']}):raise ValueError('Reviewed browser changed')
    return s,dst,fields(strict_json(guard.exact(src,plan['guards'][1],guard.MAX_INPUT).decode('utf-8-sig')))

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    plan['guards'].append(runtime(root,{'browser':s['browser']}))
    _,_,rows=validate(root,plan)
    return plan,dict(s,fields=rows,scope='Start a disposable headless browser under the existing cap, construct inert local text inputs from reviewed names only, enter exact values using native CDP input and verify DOM values. No original website HTML, network navigation, personal profile, authentication or submission. This is local browser replay, not live website completion.')

def execute(root,plan):
    s,dst,rows=validate(root,plan)
    with native_connection(plan,dst.parent) as ws:r=replay(ws,rows)
    r.update(schema=SCHEMA,browser=s['browser'],disposable_profile=True,shared_root_cap_verified=True,
             cleanup_scope_closed=True,personal_profile_used=False)
    sha=guard.publish(json.dumps(r,sort_keys=True,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'native_local_form_replayed','output':plan['output'],'sha256':sha,
            'controls_filled':r['controls_filled'],'dom_values_verified':True,'submitted':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Native local browser replay unavailable; check reviewed receipt, browser, optional websocket-client and resources'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
