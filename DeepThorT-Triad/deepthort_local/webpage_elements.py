"""Inspect static public HTML elements without browser execution or form interaction."""
from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.parse import urljoin
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.website_monitor import checked_url
from deepthort_local.webpage_retrieval import fetch_page,MAX_BODY,clean

SCHEMA='janus-webpage-elements-v1'
MAX_NODES=12000
MAX_RESULTS=300
MAX_DEPTH=80
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
HIDDEN={'script','style','template','noscript','svg','iframe','object','head','textarea','select','option'}
TARGET={'a','button','input','form','textarea','select','label','h1','h2','h3','h4','h5','h6','img'}
ROLES={'button','link','checkbox','radio','textbox','combobox','switch','tab','menuitem'}

def checked(s):
    if not isinstance(s,dict) or set(s)!={'url'}:raise ValueError('Expected one exact public HTTPS URL')
    checked_url(s['url']);return s

def bounded(value,limit=160):
    return clean(value)[:limit] if isinstance(value,str) else ''

class Elements(HTMLParser):
    def __init__(self,url):
        super().__init__(convert_charrefs=True)
        self.url=url;self.stack=[];self.rows=[];self.count=0;self.root_counts={};self.truncated=False
    def handle_starttag(self,tag,attrs):
        self.count+=1
        if self.count>MAX_NODES or len(self.stack)>=MAX_DEPTH:raise ValueError('Static HTML structure exceeds bound')
        a=dict(attrs);parent=self.stack[-1] if self.stack else None
        counts=parent['counts'] if parent else self.root_counts
        counts[tag]=counts.get(tag,0)+1
        locator=(parent['locator'] if parent else '')+'/'+tag+'['+str(counts[tag])+']'
        hidden=bool(parent and parent['hidden']) or tag in HIDDEN or 'hidden' in a or a.get('aria-hidden')=='true'
        row=None
        # Report controls even when their contents are deliberately suppressed.
        suppressed=bool(parent and parent['hidden']) or 'hidden' in a or a.get('aria-hidden')=='true'
        if not suppressed and (tag in TARGET or a.get('role') in ROLES):
            typ=bounded(a.get('type'),40).casefold()
            if not(tag=='input' and typ=='hidden'):
                if len(self.rows)<MAX_RESULTS:
                    row={'locator':locator,'tag':tag,'role':a.get('role') if a.get('role') in ROLES else None,
                         'id':bounded(a.get('id')),'name':bounded(a.get('name')),
                         'aria_label':bounded(a.get('aria-label')),'type':typ or None,
                         'disabled_attribute':'disabled' in a,'required_attribute':'required' in a,
                         'label_for':bounded(a.get('for')) if tag=='label' else '',
                         'text':'','href':None,'form_method':None}
                    if tag=='a' and a.get('href'):
                        target=urljoin(self.url,a['href'])
                        try:checked_url(target);row['href']=target
                        except (ValueError,TypeError):pass
                    if tag=='form':row['form_method']='post' if a.get('method','').casefold()=='post' else 'get_or_other'
                    self.rows.append(row)
                else:self.truncated=True
        if tag not in VOID:self.stack.append({'tag':tag,'locator':locator,'counts':{},'hidden':hidden,'row':row})
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID:self.handle_endtag(tag)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i]['tag']==tag:
                del self.stack[i:];break
    def handle_data(self,data):
        if not self.stack or self.stack[-1]['hidden']:return
        for frame in self.stack:
            row=frame['row']
            if row is not None and row['tag'] in ('a','button','label','h1','h2','h3','h4','h5','h6') and len(row['text'])<160:
                row['text']=bounded(row['text']+' '+data)

def extract_elements(url,raw,mime,charset):
    checked_url(url)
    if mime!='text/html' or not isinstance(raw,bytes) or not 1<=len(raw)<=MAX_BODY:
        raise ValueError('Expected bounded static HTML')
    charset=(charset or 'utf-8').casefold()
    if charset not in ('utf-8','utf8','us-ascii','ascii','iso-8859-1','windows-1252','cp1252'):raise ValueError('Unsupported charset')
    text=raw.decode('utf-8-sig' if charset in ('utf-8','utf8') else charset,errors='strict')
    if '\0' in text:raise ValueError('Binary HTML refused')
    parser=Elements(url);parser.feed(text);parser.close()
    return {'schema':'janus-static-elements-v1','url':url,'response_sha256':hashlib.sha256(raw).hexdigest(),
            'response_bytes':len(raw),'elements':parser.rows,'elements_truncated':parser.truncated,
            'static_nodes_seen':parser.count,'script_executed':False,'controls_activated':False,
            'rendered_dom_verified':False,'reference_only':True,
            'limitations':'Source parser locators, not live browser DOM or CSS/XPath selectors. Browser HTML correction, CSS visibility, JavaScript, accessibility tree and actionability not verified. Input values, hidden controls, scripts and option contents are omitted.'}

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,network_consent='Read exact approved public HTTPS HTML once and inspect static controls/headings/links. No page scripts, credentials, redirect, form submission or subsequent navigation.')
def execute(root,plan):
    s,dst,_=validate(root,plan)
    r=fetch_page(s['url'],approved=True,extractor=extract_elements)
    if r['url']!=s['url'] or r['controls_activated'] is not False or r['script_executed'] is not False:raise ValueError('Inspection receipt mismatch')
    payload=json.dumps(r,ensure_ascii=True,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'static_elements_inspected','output':plan['output'],'sha256':digest,
            'elements':len(r['elements']),'rendered_dom_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Static webpage inspection unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
