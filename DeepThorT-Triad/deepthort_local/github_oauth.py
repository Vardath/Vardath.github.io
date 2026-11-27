"""GitHub OAuth device authorization for a user-provided registered public client."""
from __future__ import annotations
from dataclasses import dataclass,field
import re
import socket
import time
from urllib.parse import urlencode
from .website_monitor import PinnedHTTPS,resolve_public,stopped
from .structured_source import strict_json
from .web_search import token_checked
from .github_pull_request import _request
VERIFY='https://github.com/login/device'
SCOPE='read:user'
MAX_RESPONSE=32768
def client_id(v):
    if not isinstance(v,str) or not re.fullmatch(r'[A-Za-z0-9.]{8,100}',v):raise ValueError('Enter registered GitHub OAuth client ID')
    return v
def _post(path,fields,cancelled,*,resolver,connection):
    if path not in ('/login/device/code','/login/oauth/access_token'):raise ValueError('Invalid OAuth endpoint')
    deadline=time.monotonic()+25
    stopped(cancelled,deadline);ip=resolve_public('github.com',resolver);stopped(cancelled,deadline)
    conn=connection('github.com',ip)
    try:
        conn.request('POST',path,body=urlencode(fields).encode('ascii'),headers={'Accept':'application/json',
            'Accept-Encoding':'identity','Content-Type':'application/x-www-form-urlencoded','Connection':'close','User-Agent':'JANUS-device-auth/1'})
        response=conn.getresponse();stopped(cancelled,deadline)
        if response.status!=200 or response.headers.get_content_type()!='application/json' or response.getheader('Content-Encoding','identity').lower()!='identity':
            raise ValueError('OAuth provider refused request')
        data=bytearray()
        while True:
            stopped(cancelled,deadline);part=response.read1(min(8192,MAX_RESPONSE-len(data)+1));stopped(cancelled,deadline)
            if not part:break
            data.extend(part)
            if len(data)>MAX_RESPONSE:raise ValueError('OAuth response exceeds bound')
        result=strict_json(data.decode('utf-8'))
        if not isinstance(result,dict):raise ValueError('Invalid OAuth response')
        return result
    finally:conn.close()
@dataclass(repr=False)
class Session:
    login:str
    account_id:int
    expires:float
    _token:str=field(repr=False)
    def token(self,now=None):
        if not self._token or (time.monotonic() if now is None else now)>=self.expires:
            self.disconnect();raise ValueError('OAuth session expired or disconnected')
        return self._token
    def disconnect(self):self._token=''
def connect(client,display_code,cancelled,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS,clock=time.monotonic,wait=time.sleep):
    if approved is not True:raise PermissionError('Explicit device authorization approval required')
    client=client_id(client)
    def post(path,fields):
        return _post(path,fields,cancelled,resolver=resolver,connection=connection)
    initial=post('/login/device/code',{'client_id':client,'scope':SCOPE})
    device=initial.get('device_code');token_checked(device)
    user=initial.get('user_code');interval=initial.get('interval');expires=initial.get('expires_in')
    if not isinstance(user,str) or not re.fullmatch(r'[A-Z0-9]{4}-[A-Z0-9]{4}',user) or initial.get('verification_uri')!=VERIFY or type(interval) is not int or not 1<=interval<=30 or type(expires) is not int or not 30<=expires<=1800:
        raise ValueError('Invalid device authorization challenge')
    end=clock()+min(expires,300)
    display_code(user)
    for _ in range(60):
        if cancelled and cancelled():raise ValueError('Authorization cancelled')
        if clock()+interval>=end:raise TimeoutError('Device authorization expired')
        wait(interval)
        if cancelled and cancelled() or clock()>=end:raise TimeoutError('Authorization stopped')
        reply=post('/login/oauth/access_token',{'client_id':client,'device_code':device,'grant_type':'urn:ietf:params:oauth:grant-type:device_code'})
        if 'error' in reply:
            if reply['error']=='authorization_pending':continue
            if reply['error']=='slow_down':
                interval=min(60,interval+5);continue
            raise ValueError('Device authorization refused or expired')
        token=token_checked(reply.get('access_token'))
        if str(reply.get('token_type','')).casefold()!='bearer' or set(str(reply.get('scope','')).split(','))!={SCOPE}:
            raise ValueError('Unexpected granted OAuth scope')
        account,_=_request('GET','/user',None,token,cancelled,resolver=resolver,connection=connection,expected=200)
        if not isinstance(account,dict) or not isinstance(account.get('login'),str) or not re.fullmatch(r'[A-Za-z0-9-]{1,39}',account['login']) or type(account.get('id')) is not int or account['id']<=0:
            raise ValueError('Invalid GitHub account identity')
        return Session(account['login'],account['id'],clock()+900,token)
    raise TimeoutError('Device authorization polling limit')
