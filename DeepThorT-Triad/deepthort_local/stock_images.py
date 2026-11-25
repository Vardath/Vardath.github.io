"""Explicitly opted-in Commons search: no credentials, general URL fetch, or shell.
Metadata is untrusted. Only specific permissive license candidates are offered;
source-page rights, attribution and other rights remain for publication review.
"""
import html
import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from datetime import datetime,timezone

API='https://commons.wikimedia.org/w/api.php'
MAX_IMAGE=12*1024**2
MAX_JSON=512*1024
LICENSES={'CC0':'https://creativecommons.org/publicdomain/zero/1.0/',
          **{'CC BY '+v:'https://creativecommons.org/licenses/by/'+v+'/' for v in ('2.0','2.5','3.0','4.0')}}
class _Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[]
    def handle_data(self,data):self.parts.append(data)
def plain(value,limit):
    if not isinstance(value,str) or len(value)>16000:return ''
    p=_Text();p.feed(value);p.close()
    return ' '.join(html.unescape(' '.join(p.parts)).split())[:limit]
def checked_url(url,host):
    if not isinstance(url,str) or len(url)>2000 or any(ord(c)<33 for c in url):raise ValueError('Invalid Commons URL')
    p=urllib.parse.urlsplit(url)
    if (p.scheme!='https' or p.hostname!=host or p.netloc!=host or p.username or p.password or p.fragment):
        raise ValueError('Unexpected Commons URL origin')
    if host=='upload.wikimedia.org' and not p.path.startswith('/wikipedia/commons/'):raise ValueError('Unexpected image path')
    if host=='commons.wikimedia.org' and not (p.path=='/w/api.php' or p.path.startswith('/wiki/File:')):raise ValueError('Unexpected Commons page path')
    return url

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):raise ValueError('Commons redirect refused; no external host requested')

def get(url,host,limit,cancelled=None):
    import time
    checked_url(url,host)
    if cancelled and cancelled():raise ValueError('Stock image request cancelled')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    req=urllib.request.Request(url,headers={'User-Agent':'DeepThorTriad/29 (local user-directed media workflow; https://github.com/Vardath/Vardath.github.io)'})
    deadline=time.monotonic()+35
    chunks=[];total=0
    with opener.open(req,timeout=8) as response:
        if response.status!=200 or response.geturl()!=url:raise ValueError('Unexpected Commons response')
        while True:
            if (cancelled and cancelled()) or time.monotonic()>deadline:raise TimeoutError('Stock image request stopped')
            chunk=response.read(min(65536,limit-total+1))
            if not chunk:break
            total+=len(chunk)
            if total>limit:raise ValueError('Stock image response exceeds size limit')
            chunks.append(chunk)
    return b''.join(chunks)

def candidates(data):
    pages=data.get('query',{}).get('pages',{})
    if not isinstance(pages,dict):raise ValueError('Invalid Commons search results')
    out=[]
    for page in sorted(pages.values(),key=lambda p:(p.get('index',999),p.get('pageid',0)))[:12]:
        try:
            ident=page['pageid'];title=page['title'];info=page['imageinfo'][0];meta=info['extmetadata']
            if type(ident) is not int or ident<=0 or not isinstance(title,str) or not title.startswith('File:'):continue
            if info['mime'] not in ('image/jpeg','image/png') or not 0<info['size']<=MAX_IMAGE:continue
            w,h=info['width'],info['height']
            if type(w) is not int or type(h) is not int or not 1<=w<=8192 or not 1<=h<=8192 or w*h>24000000:continue
            def field(k,limit):return plain(meta.get(k,{}).get('value',''),limit)
            license=field('LicenseShortName',60);license_url=field('LicenseUrl',300)
            if license not in LICENSES or license_url.replace('http://','https://',1).rstrip('/')!=LICENSES[license].rstrip('/'):continue
            creator=field('Artist',300)
            if license!='CC0' and not creator:continue
            source=checked_url(info['descriptionurl'],'commons.wikimedia.org')
            download=checked_url(info['url'],'upload.wikimedia.org')
            out.append({'id':ident,'title':title[:260],'creator':creator or 'Not stated',
                'license':license,'license_url':LICENSES[license],'source_url':source,'download_url':download,
                'description':field('ImageDescription',220),'credit':field('Credit',300),
                'attribution_required':license!='CC0','original_bytes':info['size'],'width':w,'height':h,
                'mime':info['mime'],'provider_sha1':info.get('sha1','')})
        except (KeyError,TypeError,ValueError,IndexError):continue
    return out[:6]

def search(query,cancelled=None):
    if not isinstance(query,str) or not query.strip() or len(query)>450:raise ValueError('Invalid visual search phrase')
    # Send only the scene's approved visual description, not the project brief,
    # chat, local file paths or credentials. No arbitrary URL from the model.
    params={'action':'query','generator':'search','gsrsearch':query,'gsrnamespace':'6','gsrlimit':'12',
            'prop':'imageinfo','iiprop':'url|size|mime|sha1|extmetadata',
            'iiextmetadatafilter':'LicenseShortName|LicenseUrl|Artist|Credit|ImageDescription',
            'format':'json'}
    from .structured_source import strict_json
    return candidates(strict_json(get(API+'?'+urllib.parse.urlencode(params),'commons.wikimedia.org',MAX_JSON,cancelled).decode('utf-8')))

def download(candidate,cancelled=None):
    import hashlib
    data=get(candidate['download_url'],'upload.wikimedia.org',MAX_IMAGE,cancelled)
    if len(data)!=candidate['original_bytes']:raise ValueError('Commons image size changed since search')
    digest=hashlib.sha1(data).hexdigest()
    expected=candidate['provider_sha1']
    # MediaWiki may expose a hexadecimal or base36 SHA-1.
    if not isinstance(expected,str) or not re.fullmatch(r'[0-9a-z]{1,40}',expected):raise ValueError('Missing source digest')
    try:
        matched=(digest==expected.lower()) if len(expected)==40 else (int(expected,36)==int(digest,16))
    except ValueError:matched=False
    if not matched:raise ValueError('Commons image bytes changed since search')
    return data
