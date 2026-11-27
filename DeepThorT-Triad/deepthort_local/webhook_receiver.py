"""Finite, loopback-only, HMAC-verified GitHub webhook receipt; no task admission."""
import hashlib
import hmac
import json
import re
import socket
import time
import uuid
from .structured_source import strict_json

MAX_HEADER=8192
MAX_BODY=65536
MAX_ATTEMPTS=16
EVENT=re.compile(r'[a-z][a-z0-9_]{0,39}\Z')
HEADER=re.compile(r'[A-Za-z0-9-]{1,80}\Z')
def checked(event,secret,seconds):
    if not isinstance(event,str) or not EVENT.fullmatch(event):raise ValueError('Choose one exact GitHub event type')
    if not isinstance(secret,str) or not 16<=len(secret)<=128 or any(not 33<=ord(c)<=126 for c in secret):
        raise ValueError('Use 16–128 printable non-space ASCII secret characters')
    if type(seconds) is not int or not 5<=seconds<=90:raise ValueError('Choose 5–90 seconds')
def stop(cancelled,deadline):
    if cancelled and cancelled():raise TimeoutError('Webhook receiver stopped')
    if time.monotonic()>=deadline:raise TimeoutError('Webhook receiver expired')
def receive(conn,deadline,cancelled):
    while True:
        stop(cancelled,deadline)
        try:return conn.recv(4096)
        except socket.timeout:continue
def parse(conn,event,key,cancelled,deadline):
    data=bytearray()
    while b'\r\n\r\n' not in data:
        chunk=receive(conn,deadline,cancelled)
        if not chunk:raise ValueError('Incomplete headers')
        data.extend(chunk)
        if len(data)>MAX_HEADER+4096:raise ValueError('Header limit')
    raw,_,body=bytes(data).partition(b'\r\n\r\n')
    if len(raw)>MAX_HEADER:raise ValueError('Header limit')
    lines=raw.decode('ascii').split('\r\n')
    if lines[0]!='POST /webhook HTTP/1.1':raise ValueError('Unexpected request target')
    headers={}
    for line in lines[1:]:
        name,sep,value=line.partition(':')
        name=name.lower();value=value.strip()
        if not sep or not HEADER.fullmatch(name) or name in headers or any(ord(c)<32 or ord(c)>126 for c in value):
            raise ValueError('Invalid or duplicate header')
        headers[name]=value
    if 'transfer-encoding' in headers or headers.get('content-encoding','identity')!='identity' or headers.get('content-type','').split(';',1)[0].lower()!='application/json':
        raise ValueError('Only uncompressed length-delimited JSON accepted')
    delivery=headers.get('x-github-delivery','')
    if str(uuid.UUID(delivery))!=delivery.lower():raise ValueError('Expected UUID delivery identifier')
    length=headers.get('content-length','')
    if not re.fullmatch(r'[0-9]{1,5}',length) or not 1<=int(length)<=MAX_BODY:raise ValueError('Body exceeds bound')
    length=int(length)
    if len(body)>length:raise ValueError('Unexpected trailing bytes')
    body=bytearray(body)
    while len(body)<length:
        chunk=receive(conn,deadline,cancelled)
        if not chunk:raise ValueError('Incomplete body')
        body.extend(chunk)
        if len(body)>length:raise ValueError('Unexpected trailing bytes')
    # Consume the complete bounded request body before rejecting a wrong event.
    # Closing a socket with unread bytes can reset the connection on Windows.
    if headers.get('x-github-event')!=event:raise ValueError('Unexpected event')
    signature=headers.get('x-hub-signature-256','')
    expected='sha256='+hmac.new(key,body,hashlib.sha256).hexdigest()
    if not re.fullmatch(r'sha256=[a-f0-9]{64}',signature) or not hmac.compare_digest(expected,signature):
        raise ValueError('Webhook signature mismatch')
    if not isinstance(strict_json(body.decode('utf-8')),dict):raise ValueError('Expected JSON object')
    return {'status':'signed_webhook_received','event':event,'delivery_id':delivery.lower(),
            'body_sha256':hashlib.sha256(body).hexdigest(),'body_bytes':length,'signature_verified':True,
            'payload_retained':False,'task_submitted':False,'scope':'Local authenticated delivery only, not proof of GitHub origin.'}
def reply(conn,status):
    try:conn.sendall(('HTTP/1.1 '+status+'\r\nContent-Length: 0\r\nConnection: close\r\n\r\n').encode('ascii'))
    except OSError:pass
def listen(event,secret,seconds,ready,cancelled=None,*,approved=False):
    if approved is not True:raise PermissionError('Explicit local webhook session approval required')
    checked(event,secret,seconds)
    key=secret.encode('ascii')
    deadline=time.monotonic()+seconds
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as server:
        server.bind(('127.0.0.1',0));server.listen(2);server.settimeout(.2)
        ready(server.getsockname()[1])
        attempts=0
        while attempts<MAX_ATTEMPTS:
            stop(cancelled,deadline)
            try:conn,_=server.accept()
            except socket.timeout:continue
            attempts+=1
            with conn:
                conn.settimeout(.2)
                try:receipt=parse(conn,event,key,cancelled,min(deadline,time.monotonic()+3))
                except (ValueError,UnicodeError,RecursionError,OSError):
                    reply(conn,'400 Bad Request');continue
                stop(cancelled,deadline)
                reply(conn,'200 OK')
                return receipt
    raise ValueError('Local webhook attempt limit reached')
