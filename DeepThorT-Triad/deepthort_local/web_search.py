"""User-directed general web search via the fixed Brave Search API endpoint."""
from __future__ import annotations
from hashlib import sha256
from html.parser import HTMLParser
import json
import re
import socket
import time
from urllib.parse import urlencode
from .website_monitor import PinnedHTTPS,resolve_public,stopped
from .search_interpretation import checked,interpret,display_url,terms
from .long_form_writing import literal
from .structured_source import strict_json

HOST='api.search.brave.com'
ENDPOINT='/res/v1/web/search'
MAX_RESPONSE=512*1024

class Plain(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.parts=[];self.hidden=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','template'):self.hidden.append(tag)
    def handle_endtag(self,tag):
        if self.hidden and tag==self.hidden[-1]:self.hidden.pop()
    def handle_data(self,data):
        if not self.hidden:self.parts.append(data)

def plain(s,limit):
    if not isinstance(s,str) or len(s)>16000:return ''
    p=Plain();p.feed(s);p.close()
    value=' '.join(' '.join(p.parts).split())
    value=''.join(c for c in value if 32<=ord(c) and not 127<=ord(c)<=159 and not 0xd800<=ord(c)<=0xdfff)
    return value[:limit].strip()

def query_checked(query,count):
    literal(query,600)
    if len(query.split())>75 or not terms(query) or type(count) is not int or not 1<=count<=20:
        raise ValueError('Enter a meaningful query of at most 75 words and choose 1–20 results')
    return query

def token_checked(token):
    if not isinstance(token,str) or not re.fullmatch(r'[A-Za-z0-9._~-]{8,512}',token):
        raise ValueError('Enter a valid API token; it is not stored')
    return token

def normalize(query,count,raw):
    query_checked(query,count)
    if not isinstance(raw,bytes) or not raw or len(raw)>MAX_RESPONSE:
        raise ValueError('Search response missing or exceeds bound')
    data=strict_json(raw.decode('utf-8'))
    if not isinstance(data,dict) or data.get('type')!='search':
        raise ValueError('Unexpected search response')
    web=data.get('web')
    if web is None:rows=[]
    elif isinstance(web,dict) and web.get('type')=='search' and isinstance(web.get('results'),list):
        rows=web['results']
    else:raise ValueError('Invalid web-result envelope')
    if len(rows)>20:raise ValueError('Provider returned too many results')
    results=[];omitted=0
    for row in rows[:count]:
        try:
            if not isinstance(row,dict):raise ValueError('Invalid result')
            title=plain(row.get('title'),500);url=row.get('url');snippet=plain(row.get('description'),2000)
            if not title:raise ValueError('Missing title')
            display_url(url)
            results.append({'title':title,'url':url,'snippet':snippet})
        except (ValueError,TypeError):omitted+=1
    if rows and not results:raise ValueError('No usable web results in response')
    spec=checked({'query':query,'results':results})
    evidence=interpret(spec)
    evidence.update({'network_performed':True,'provider':'Brave Search API','provider_response_sha256':sha256(raw).hexdigest(),
                     'provider_rows_omitted':omitted,'provider_returned_count':len(rows),'requested_count':count,
                     'provider_query_may_be_modified':bool(isinstance(data.get('query'),dict) and data['query'].get('altered')),
                     'limitations':'Search API snippets only. Pages were not opened; claims, date, authority and result completeness are not independently verified.'})
    return {'schema':'janus-web-search-result-v1','supplied_results':spec,'interpretation':evidence}

def search(query,count,token,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise ValueError('Explicit approval for network query required')
    query_checked(query,count);token_checked(token)
    deadline=time.monotonic()+25
    stopped(cancelled,deadline)
    ip=resolve_public(HOST,resolver);stopped(cancelled,deadline)
    conn=connection(HOST,ip)
    path=ENDPOINT+'?'+urlencode({'q':query,'count':str(count),'safesearch':'moderate','result_filter':'web'})
    try:
        conn.request('GET',path,headers={'Accept':'application/json','Accept-Encoding':'identity',
            'X-Subscription-Token':token,'User-Agent':'JANUS-local-research/1.0','Connection':'close'})
        response=conn.getresponse();stopped(cancelled,deadline)
        if response.status!=200:raise ValueError('Search provider rejected the request or returned a non-success response')
        if response.headers.get_content_type()!='application/json' or response.getheader('Content-Encoding','identity').lower()!='identity':
            raise ValueError('Unsupported search response format')
        length=response.getheader('Content-Length')
        if length is not None and (not length.isdecimal() or not 0<int(length)<=MAX_RESPONSE):
            raise ValueError('Search response exceeds bound')
        chunks=[];size=0
        while True:
            stopped(cancelled,deadline);part=response.read1(min(32768,MAX_RESPONSE-size+1));stopped(cancelled,deadline)
            if not part:break
            size+=len(part)
            if size>MAX_RESPONSE:raise ValueError('Search response exceeds bound')
            chunks.append(part)
        if length is not None and size!=int(length):raise ValueError('Incomplete search response')
        return normalize(query,count,b''.join(chunks))
    finally:conn.close()
