"""Explicit reviewed public HTTPS document retrieval; no browser or script execution."""
from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import socket
import sys
import time
from urllib.parse import urljoin
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.website_monitor import checked_url,PinnedHTTPS,resolve_public,stopped
from deepthort_local.search_interpretation import display_url

SCHEMA='janus-webpage-retrieval-v1'
MAX_BODY=512*1024
MAX_TEXT=100000
MAX_LINKS=100
HIDDEN=frozenset({'script','style','template','noscript','svg','iframe','object','head'})
BLOCKS=frozenset({'p','div','section','article','main','header','footer','nav','aside','h1','h2','h3','h4','h5','h6','li','br','tr','blockquote','pre','hr','table','ul','ol','dl','dt','dd'})

def checked(s):
    if not isinstance(s,dict) or set(s)!={'url'}:raise ValueError('Expected one exact public HTTPS page URL')
    checked_url(s['url'])
    return s

def clean(text):
    return ' '.join(''.join(c if c in '\t\r\n' or ord(c)>=32 and not 127<=ord(c)<=159 else ' ' for c in text).split())

class Page(HTMLParser):
    def __init__(self,url):
        super().__init__(convert_charrefs=True)
        self.url=url;self.parts=[];self.title=[];self.hidden=[];self.in_title=False;self.links=[];self.seen=set()
    def handle_starttag(self,tag,attrs):
        if tag=='title' and self.hidden==['head']:self.in_title=True
        if tag in HIDDEN:self.hidden.append(tag)
        if self.hidden:return
        if tag in BLOCKS:self.parts.append('\n')
        if tag=='a' and len(self.links)<MAX_LINKS:
            href=dict(attrs).get('href')
            if not isinstance(href,str) or not href or len(href)>1600 or href.startswith('#'):return
            url=urljoin(self.url,href)
            try:display_url(url)
            except ValueError:return
            if url not in self.seen:self.seen.add(url);self.links.append(url)
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs);self.handle_endtag(tag)
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
        if self.hidden:
            if tag==self.hidden[-1]:self.hidden.pop()
            return
        if tag in BLOCKS:self.parts.append('\n')
    def handle_data(self,data):
        if self.in_title:self.title.append(data)
        if not self.hidden:self.parts.append(data)
def extract(url,raw,mime,charset):
    if not isinstance(raw,bytes) or not raw or len(raw)>MAX_BODY:raise ValueError('Page missing or exceeds bound')
    if mime not in ('text/html','text/plain'):raise ValueError('Unsupported page type')
    charset=(charset or 'utf-8').casefold()
    if charset not in ('utf-8','utf8','us-ascii','ascii','iso-8859-1','windows-1252','cp1252'):
        raise ValueError('Unsupported declared page charset')
    text=raw.decode('utf-8-sig' if charset in ('utf-8','utf8') else charset,errors='strict')
    if '\0' in text:raise ValueError('Binary data in text page')
    if mime=='text/html':
        parser=Page(url);parser.feed(text);parser.close()
        title=clean(' '.join(parser.title))[:500]
        lines=[clean(x) for x in ''.join(parser.parts).splitlines()]
        links=parser.links
    else:
        title='';lines=[clean(x) for x in text.splitlines()];links=[]
    content='\n'.join(x for x in lines if x)
    if not content:raise ValueError('No readable text in response')
    if len(content)>MAX_TEXT:raise ValueError('Extracted text exceeds bound; no partial page claimed')
    return {'schema':'janus-webpage-evidence-v1','url':url,'title':title,'mime':mime,'charset':charset,
            'response_bytes':len(raw),'response_sha256':hashlib.sha256(raw).hexdigest(),
            'text':content,'text_sha256':hashlib.sha256(content.encode('utf-8')).hexdigest(),
            'discovered_links':links,'links_followed':False,'content_verified_as_factual':False,
            'script_executed':False,'reference_only':True,
            'limitations':'Extracted static response text, not rendered browser content. No authentication, redirects, scripts, subresources or factual verification.'}

def fetch_page(url,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS,extractor=extract):
    if approved is not True:raise ValueError('Explicit approval for exact page read required')
    host,path=checked_url(url);deadline=time.monotonic()+25
    stopped(cancelled,deadline);ip=resolve_public(host,resolver);stopped(cancelled,deadline)
    conn=connection(host,ip)
    try:
        conn.request('GET',path,headers={'User-Agent':'JANUS-local-research/1.0','Accept':'text/html, text/plain',
                                        'Accept-Encoding':'identity','Connection':'close'})
        response=conn.getresponse();stopped(cancelled,deadline)
        if response.status!=200:raise ValueError('Only exact HTTP 200 accepted; redirects refused')
        mime=response.headers.get_content_type();charset=response.headers.get_content_charset()
        if mime not in ('text/html','text/plain') or response.getheader('Content-Encoding','identity').lower()!='identity':
            raise ValueError('Unsupported response format')
        length=response.getheader('Content-Length')
        if length is not None and (not length.isdecimal() or not 0<int(length)<=MAX_BODY):
            raise ValueError('Page response exceeds byte bound')
        chunks=[];total=0
        while True:
            stopped(cancelled,deadline);chunk=response.read1(min(32768,MAX_BODY-total+1));stopped(cancelled,deadline)
            if not chunk:break
            total+=len(chunk)
            if total>MAX_BODY:raise ValueError('Page response exceeds byte bound')
            chunks.append(chunk)
        if length is not None and total!=int(length):raise ValueError('Incomplete page response')
        return extractor(url,b''.join(chunks),mime,charset)
    finally:conn.close()

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,{'url':s['url'],'network_consent':'Read this exact public HTTPS URL once. Remote server receives normal request and IP; response text is saved in new JSON.',
                 'scope':'No redirects, credentials, queries, page scripts, subresources or automatic link following. No network at review time.'}
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def execute(root,plan,*,retrieve=fetch_page):
    s,dst,_=validate(root,plan)
    result=retrieve(s['url'],approved=True)
    if result.get('url')!=s['url'] or result.get('reference_only') is not True or result.get('content_verified_as_factual') is not False:
        raise ValueError('Page receipt identity mismatch')
    payload=json.dumps(result,ensure_ascii=True,sort_keys=True,indent=2).encode('utf-8')
    if json.loads(payload)!=result:raise ValueError('Page report serialization mismatch')
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-webpage-publication-v1','status':'webpage_text_retrieved','output':plan['output'],
            'sha256':sha,'response_sha256':result['response_sha256'],'text_sha256':result['text_sha256'],
            'content_verified_as_factual':False,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Webpage retrieval unavailable; inspect exact URL, public network and response format'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
