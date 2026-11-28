"""Explicit read-only Google Drive folder inventory and verified small-file download."""
from __future__ import annotations
import hashlib
import re
import socket
import time
from urllib.parse import urlencode
from .gmail_read import EMAIL, token_checked
from .website_monitor import PinnedHTTPS, resolve_public, stopped
from .structured_source import strict_json

HOST='www.googleapis.com'
BASE='/drive/v3'
LIMIT=1024*1024
ID=re.compile(r'[A-Za-z0-9_-]{1,128}')
MD5=re.compile(r'[a-f0-9]{32}')
FIELDS='id,name,mimeType,size,md5Checksum,version,trashed'
FOLDER='application/vnd.google-apps.folder'

def checked(s):
    if not isinstance(s,dict) or s.get('operation') not in ('list','download'):
        raise ValueError('Choose list or download')
    if not isinstance(s.get('account'),str) or not EMAIL.fullmatch(s['account']):
        raise ValueError('Choose exact Google account address')
    op=s['operation']; key='folder_id' if op=='list' else 'file_id'
    expected={'operation','account',key,'limit'} if op=='list' else {'operation','account',key}
    if set(s)!=expected or not isinstance(s.get(key),str) or not ID.fullmatch(s[key]):
        raise ValueError('Choose exact Drive identifier')
    if op=='list' and (type(s['limit']) is not int or not 1<=s['limit']<=20):
        raise ValueError('Choose 1–20 files')
    return dict(s)

def fetch(path,token,cancelled,*,binary=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    token_checked(token);deadline=time.monotonic()+25
    stopped(cancelled,deadline);ip=resolve_public(HOST,resolver);stopped(cancelled,deadline)
    conn=connection(HOST,ip)
    try:
        conn.request('GET',BASE+path,headers={'Authorization':'Bearer '+token,'Accept':'*/*' if binary else 'application/json',
            'Accept-Encoding':'identity','User-Agent':'JANUS-reviewed-drive/1.0','Connection':'close'})
        r=conn.getresponse();stopped(cancelled,deadline)
        if r.status!=200 or r.getheader('Content-Encoding','identity').lower()!='identity':
            raise ValueError('Drive response refused; redirects not followed')
        if not binary and r.headers.get_content_type()!='application/json':
            raise ValueError('Invalid Drive metadata format')
        length=r.getheader('Content-Length')
        if length is not None and (not length.isdecimal() or not 0<=int(length)<=LIMIT):
            raise ValueError('Drive response exceeds bound')
        chunks=[];size=0
        while True:
            stopped(cancelled,deadline);part=r.read1(min(32768,LIMIT-size+1));stopped(cancelled,deadline)
            if not part:break
            size+=len(part)
            if size>LIMIT:raise ValueError('Drive response exceeds bound')
            chunks.append(part)
        if length is not None and size!=int(length):raise ValueError('Incomplete Drive response')
        raw=b''.join(chunks)
        return raw if binary else strict_json(raw.decode('utf-8'))
    finally:conn.close()

def identity(s,row):
    user=row.get('user') if isinstance(row,dict) else None
    account=user.get('emailAddress') if isinstance(user,dict) else None
    if not isinstance(account,str) or account.casefold()!=s['account'].casefold():
        raise ValueError('Drive account mismatch')
    return account

def metadata(row,ident=None):
    if not isinstance(row,dict) or not isinstance(row.get('id'),str) or not ID.fullmatch(row['id']) or (ident is not None and row['id']!=ident):
        raise ValueError('Drive file identity mismatch')
    if row.get('trashed') is not False:raise ValueError('Trashed or unverified Drive file')
    for key in ('name','mimeType'):
        if not isinstance(row.get(key),str) or not 1<=len(row[key])<=1024 or any(not c.isprintable() for c in row[key]):
            raise ValueError('Invalid Drive file metadata')
    result={k:row[k] for k in ('id','name','mimeType')}
    for key in ('size','version'):
        if key in row:
            value=row[key]
            if not isinstance(value,str) or not re.fullmatch(r'[0-9]{1,20}',value):raise ValueError('Invalid Drive numeric metadata')
            result[key]=value
    if 'md5Checksum' in row:
        if not isinstance(row['md5Checksum'],str) or not MD5.fullmatch(row['md5Checksum']):raise ValueError('Invalid checksum')
        result['md5Checksum']=row['md5Checksum']
    return result

def inspect(s,token,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise PermissionError('Explicit Drive read approval required')
    s=checked(s)
    def get(path,*,binary=False):
        return fetch(path,token,cancelled,binary=binary,resolver=resolver,connection=connection)
    def account():return identity(s,get('/about?fields=user(emailAddress)'))
    def file(ident):return metadata(get('/files/'+ident+'?'+urlencode({'fields':FIELDS,'supportsAllDrives':'true'})),ident)
    owner=account()
    receipt={'schema':'janus-drive-read-v1','operation':s['operation'],'account':owner,'remote_changed':False,
             'untrusted_content':True,'model_dispatched':False}
    if s['operation']=='list':
        folder=s['folder_id']
        if folder!='root' and file(folder)['mimeType']!=FOLDER:raise ValueError('Not a Drive folder')
        page=get('/files?'+urlencode({'q':"'"+folder+"' in parents and trashed = false",'pageSize':s['limit'],
            'fields':'nextPageToken,files('+FIELDS+')','supportsAllDrives':'true','includeItemsFromAllDrives':'true'}))
        if not isinstance(page,dict) or not isinstance(page.get('files'),list) or len(page['files'])>s['limit']:
            raise ValueError('Invalid bounded Drive listing')
        rows=[metadata(row) for row in page['files']]
        if len({r['id'] for r in rows})!=len(rows):raise ValueError('Duplicate Drive IDs')
        receipt.update(files=rows,more_results=bool(page.get('nextPageToken')))
        raw=None
    else:
        ident=s['file_id'];before=file(ident)
        if before['mimeType'].startswith('application/vnd.google-apps.') or 'size' not in before or 'version' not in before or 'md5Checksum' not in before or int(before['size'])>LIMIT:
            raise ValueError('Only existing binary Drive files up to 1 MiB with checksum and version')
        raw=get('/files/'+ident+'?alt=media&supportsAllDrives=true',binary=True)
        if len(raw)!=int(before['size']) or hashlib.md5(raw,usedforsecurity=False).hexdigest()!=before['md5Checksum'] or file(ident)!=before:
            raise ValueError('Drive bytes or metadata changed during download')
        receipt.update(file=before,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
    if account()!=owner:raise ValueError('Account changed during Drive read')
    return receipt,raw

def save_download(path,receipt,raw,*,approved=False):
    if approved is not True:raise PermissionError('Explicit local file save approval required')
    if not isinstance(raw,bytes) or len(raw)>LIMIT or receipt.get('schema')!='janus-drive-read-v1' or receipt.get('operation')!='download' or receipt.get('bytes')!=len(raw) or receipt.get('sha256')!=hashlib.sha256(raw).hexdigest():
        raise ValueError('Download receipt mismatch')
    # Exclusive creation; no remote filename or path is automatically trusted.
    with open(path,'xb') as out:
        out.write(raw)
    return receipt['sha256']
