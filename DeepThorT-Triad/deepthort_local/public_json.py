"""Bounded HTTPS JSON transport for fixed public research-provider adapters."""
from __future__ import annotations
import socket
import time
from urllib.parse import urlsplit
from .website_monitor import PinnedHTTPS,resolve_public,stopped
from .structured_source import strict_json

MAX_JSON=512*1024

def retrieve(host,path,*,cancelled=None,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    # Host/path supplied only by fixed provider adapters, not user or model URLs.
    if host not in ('commons.wikimedia.org','api.crossref.org'):
        raise ValueError('Unsupported research provider')
    if not isinstance(path,str) or len(path)>4000 or not path.startswith('/') or path.startswith('//') or '#' in path or any(ord(c)<33 or ord(c)>126 for c in path):
        raise ValueError('Invalid provider request path')
    if urlsplit(path).netloc:raise ValueError('Invalid provider origin')
    deadline=time.monotonic()+25;stopped(cancelled,deadline)
    ip=resolve_public(host,resolver);stopped(cancelled,deadline)
    conn=connection(host,ip)
    try:
        conn.request('GET',path,headers={'Accept':'application/json','Accept-Encoding':'identity',
            'User-Agent':'JANUS-local-research/1.0 (https://github.com/Vardath/Vardath.github.io)','Connection':'close'})
        response=conn.getresponse();stopped(cancelled,deadline)
        if response.status!=200:raise ValueError('Provider did not return HTTP 200; redirects refused')
        allowed_types=('application/json','application/vnd.crossref-api-message+json') if host=='api.crossref.org' else ('application/json',)
        if response.headers.get_content_type() not in allowed_types or response.getheader('Content-Encoding','identity').lower()!='identity':
            raise ValueError('Unsupported provider response format')
        length=response.getheader('Content-Length')
        if length is not None and (not length.isdecimal() or not 0<int(length)<=MAX_JSON):
            raise ValueError('Provider response exceeds bound')
        chunks=[];total=0
        while True:
            stopped(cancelled,deadline);part=response.read1(min(32768,MAX_JSON-total+1));stopped(cancelled,deadline)
            if not part:break
            total+=len(part)
            if total>MAX_JSON:raise ValueError('Provider response exceeds bound')
            chunks.append(part)
        if not total or (length is not None and total!=int(length)):raise ValueError('Incomplete provider response')
        raw=b''.join(chunks)
        return strict_json(raw.decode('utf-8')),raw
    finally:conn.close()
