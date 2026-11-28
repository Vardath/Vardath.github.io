"""Reviewed single-recipient plain-text Gmail send, no automatic retry."""
from __future__ import annotations
import base64
import hashlib
import json
import re
import socket
import time
from email.message import EmailMessage
from email.policy import SMTP
from .gmail_read import BASE,HOST,ID,EMAIL,MAX_RESPONSE,profile,request,token_checked
from .website_monitor import PinnedHTTPS,resolve_public,stopped
from .structured_source import strict_json

SCHEMA='janus-gmail-send-v1'

def address(value):
    if not isinstance(value,str) or len(value)>254 or not EMAIL.fullmatch(value) or '..' in value:
        raise ValueError('Use one literal email address')
    local,domain=value.rsplit('@',1)
    if local.startswith('.') or local.endswith('.') or '.' not in domain or any(not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?',p) for p in domain.split('.')):
        raise ValueError('Invalid literal email address')
    return value

def checked(s):
    if not isinstance(s,dict) or set(s)!={'account','to','subject','body'}:
        raise ValueError('Expected account, to, subject and body')
    address(s['account']);address(s['to'])
    subject=s['subject'];body=s['body']
    if not isinstance(subject,str) or not 1<=len(subject)<=180 or not subject.strip() or any(not c.isprintable() for c in subject):
        raise ValueError('Use a bounded one-line subject')
    if not isinstance(body,str) or not body.strip() or len(body)>12000 or any(not (c.isprintable() or c in '\n\t') for c in body):
        raise ValueError('Use bounded plain-text body')
    return s

def prepare(s):
    checked(s)
    message=EmailMessage(policy=SMTP)
    message['From']=s['account'];message['To']=s['to'];message['Subject']=s['subject']
    message.set_content(s['body'],subtype='plain',charset='utf-8')
    raw=message.as_bytes()
    if len(raw)>100000:raise ValueError('Encoded message exceeds bound')
    return raw

def send_request(raw,token,cancelled,*,resolver,connection):
    token_checked(token);deadline=time.monotonic()+25
    stopped(cancelled,deadline);ip=resolve_public(HOST,resolver);stopped(cancelled,deadline)
    payload=json.dumps({'raw':base64.urlsafe_b64encode(raw).decode('ascii')},separators=(',',':')).encode()
    conn=connection(HOST,ip)
    try:
        stopped(cancelled,deadline)
        # Exactly one POST; any lost response is an uncertain outcome.
        conn.request('POST',BASE+'/messages/send',body=payload,headers={'Authorization':'Bearer '+token,
            'Content-Type':'application/json','Accept':'application/json','Accept-Encoding':'identity',
            'User-Agent':'JANUS-reviewed-mail/1.0','Connection':'close'})
        r=conn.getresponse();stopped(cancelled,deadline)
        if r.status!=200 or r.headers.get_content_type()!='application/json' or r.getheader('Content-Encoding','identity').lower()!='identity':
            raise ValueError('Send outcome unconfirmed; inspect Sent before retry')
        length=r.getheader('Content-Length')
        if length is not None and (not length.isdecimal() or not 0<int(length)<=MAX_RESPONSE):raise ValueError('Response exceeds bound')
        chunks=[];size=0
        while True:
            stopped(cancelled,deadline);part=r.read1(min(32768,MAX_RESPONSE-size+1));stopped(cancelled,deadline)
            if not part:break
            size+=len(part)
            if size>MAX_RESPONSE:raise ValueError('Response exceeds bound')
            chunks.append(part)
        if length is not None and size!=int(length):raise ValueError('Incomplete send receipt')
        observed=b''.join(chunks)
        return strict_json(observed.decode('utf-8')),hashlib.sha256(observed).hexdigest()
    finally:conn.close()

def send(s,token,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise PermissionError('Explicit approval of exact outgoing mail required')
    s=dict(checked(s));raw=prepare(s)
    before,h1=request(BASE+'/profile?fields=emailAddress',token,cancelled,resolver=resolver,connection=connection)
    account=profile(s,before)
    result,h2=send_request(raw,token,cancelled,resolver=resolver,connection=connection)
    if not isinstance(result,dict) or not isinstance(result.get('id'),str) or not ID.fullmatch(result['id']):
        raise ValueError('Unconfirmed send receipt; inspect Sent before retry')
    return {'schema':SCHEMA,'status':'provider_send_accepted','account':account,'to':s['to'],
            'message_id':result['id'],'message_sha256':hashlib.sha256(raw).hexdigest(),
            'response_sha256':[h1,h2],'delivery_verified':False,'automatic_retry':False,
            'attachments_sent':False,'credential_stored':False}

