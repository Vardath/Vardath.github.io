"""Explicit finite OpenAI-compatible loopback gateway to the existing local broker."""
import hashlib
import hmac
import http.client
import json
import re
import secrets
import socket
import time
from .structured_source import strict_json
from .triad_profiles import MODEL_ID
from .webhook_receiver import receive,stop,HEADER
MAX_BODY=80000
MAX_REPLY=262144
MAX_REQUESTS=12
MAX_COMPLETIONS=2
def checked(value):
    if not isinstance(value,dict) or set(value)-{'model','messages','max_tokens','stream'} or value.get('model')!=MODEL_ID or value.get('stream',False) is not False:
        raise ValueError('Unsupported model or request options')
    messages=value.get('messages');tokens=value.get('max_tokens',96)
    if type(tokens) is not int or not 1<=tokens<=768 or not isinstance(messages,list) or not 1<=len(messages)<=12:
        raise ValueError('Invalid message or token count')
    for m in messages:
        if not isinstance(m,dict) or set(m)!={'role','content'} or m['role'] not in ('system','user','assistant') or not isinstance(m['content'],str) or not 1<=len(m['content'])<=8000 or any(0xd800<=ord(c)<=0xdfff for c in m['content']):
            raise ValueError('Invalid message')
    if messages[-1]['role']!='user' or sum(len(m['content']) for m in messages)>15000:
        raise ValueError('Invalid bounded conversation')
    result={'model':MODEL_ID,'messages':messages,'max_tokens':tokens,'stream':False,'triad_role':'implementation'}
    if len(json.dumps(result,ensure_ascii=True).encode('ascii'))>MAX_BODY:raise ValueError('Encoded request exceeds broker bound')
    return result
def broker(payload,internal_token):
    if not isinstance(internal_token,str) or not re.fullmatch(r'[A-Za-z0-9_-]{32,128}',internal_token):
        raise ValueError('Internal broker unavailable')
    conn=http.client.HTTPConnection('127.0.0.1',8765,timeout=120)
    try:
        conn.request('POST','/v1/chat/completions',json.dumps(payload,ensure_ascii=True).encode('ascii'),headers={'Content-Type':'application/json','Authorization':'Bearer '+internal_token,'Connection':'close'})
        response=conn.getresponse()
        if response.status!=200 or response.getheader('Content-Type','').split(';')[0]!='application/json' or response.getheader('Content-Encoding','identity')!='identity':
            raise ValueError('Local broker did not complete')
        raw=response.read(MAX_REPLY+1)
        if len(raw)>MAX_REPLY:raise ValueError('Broker response exceeds bound')
        value=strict_json(raw.decode('utf-8'))
        if not isinstance(value,dict) or value.get('model')!=MODEL_ID or value.get('triad_role')!='implementation':
            raise ValueError('Unexpected broker response identity')
        choices=value.get('choices')
        if not isinstance(choices,list) or len(choices)!=1 or not isinstance(choices[0],dict):raise ValueError('Invalid broker choice')
        row=choices[0];message=row.get('message')
        if not isinstance(message,dict) or message.get('role')!='assistant' or not isinstance(message.get('content'),str) or not message['content'].strip() or row.get('finish_reason') not in ('stop','length'):
            raise ValueError('Invalid broker response')
        return message['content'],row['finish_reason']
    finally:conn.close()
def read_request(conn,deadline,cancelled):
    data=bytearray()
    while b'\r\n\r\n' not in data:
        chunk=receive(conn,deadline,cancelled)
        if not chunk:raise ValueError('Incomplete request')
        data.extend(chunk)
        if len(data)>12288:raise ValueError('Header exceeds bound')
    header,_,body=bytes(data).partition(b'\r\n\r\n')
    if len(header)>8192:raise ValueError('Header exceeds bound')
    lines=header.decode('ascii').split('\r\n')
    if lines[0] not in ('GET /v1/models HTTP/1.1','POST /v1/chat/completions HTTP/1.1'):raise ValueError('Unsupported endpoint')
    headers={}
    for line in lines[1:]:
        name,sep,value=line.partition(':');name=name.lower();value=value.strip()
        if not sep or not HEADER.fullmatch(name) or name in headers or any(ord(c)<32 or ord(c)>126 for c in value):raise ValueError('Invalid header')
        headers[name]=value
    if 'transfer-encoding' in headers or headers.get('content-encoding','identity')!='identity':raise ValueError('Unsupported encoding')
    length=headers.get('content-length','0')
    if not re.fullmatch(r'[0-9]{1,5}',length) or not 0<=int(length)<=MAX_BODY:raise ValueError('Invalid length')
    length=int(length)
    if lines[0].startswith('GET') and length:raise ValueError('GET body unsupported')
    if lines[0].startswith('POST') and (not length or headers.get('content-type','').split(';')[0].strip().lower()!='application/json'):
        raise ValueError('JSON body required')
    data=bytearray(body)
    if len(data)>length:raise ValueError('Trailing bytes')
    while len(data)<length:
        part=receive(conn,deadline,cancelled)
        if not part:raise ValueError('Incomplete body')
        data.extend(part)
        if len(data)>length:raise ValueError('Trailing bytes')
    return lines[0],headers,bytes(data)
def reply(conn,code,value):
    raw=json.dumps(value,ensure_ascii=True,allow_nan=False,separators=(',',':')).encode('ascii')
    if len(raw)>MAX_REPLY:raise ValueError('Response exceeds bound')
    status={200:'OK',400:'Bad Request',401:'Unauthorized',429:'Too Many Requests',503:'Service Unavailable'}[code]
    try:conn.sendall(('HTTP/1.1 '+str(code)+' '+status+'\r\nContent-Type: application/json\r\nContent-Length: '+str(len(raw))+'\r\nConnection: close\r\n\r\n').encode('ascii')+raw)
    except OSError:pass
def error(conn,code,message):
    reply(conn,code,{'error':{'message':message,'type':'local_gateway_error','code':str(code)}})
def serve(key,infer,ready,cancelled=None,*,approved=False,seconds=120):
    if approved is not True:raise PermissionError('Explicit gateway approval required')
    if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{32,128}',key) or type(seconds) is not int or not 5<=seconds<=120:
        raise ValueError('Invalid gateway key or duration')
    end=time.monotonic()+seconds;calls=0;requests=0
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as server:
        server.bind(('127.0.0.1',0));server.listen(2);server.settimeout(.2);ready(server.getsockname()[1])
        while requests<MAX_REQUESTS and calls<MAX_COMPLETIONS:
            if cancelled and cancelled() or time.monotonic()>=end:break
            try:conn,_=server.accept()
            except socket.timeout:continue
            requests+=1
            with conn:
                conn.settimeout(.5)
                try:line,headers,raw=read_request(conn,min(end,time.monotonic()+4),cancelled)
                except (ValueError,UnicodeError,OSError,RecursionError):error(conn,400,'Unsupported or incomplete request');continue
                if not hmac.compare_digest(headers.get('authorization',''),'Bearer '+key):
                    error(conn,401,'Unauthorized');continue
                if line.startswith('GET'):
                    reply(conn,200,{'object':'list','data':[{'id':MODEL_ID,'object':'model','created':0,'owned_by':'local'}]});continue
                try:payload=checked(strict_json(raw.decode('utf-8')))
                except (ValueError,TypeError,RecursionError):error(conn,400,'Unsupported chat request');continue
                if cancelled and cancelled() or time.monotonic()>=end:break
                calls+=1
                try:
                    content,finish=infer(payload)
                    if not isinstance(content,str) or not content.strip() or finish not in ('stop','length'):raise ValueError('Invalid inference')
                    if cancelled and cancelled():break
                    reply(conn,200,{'id':'chatcmpl-'+secrets.token_hex(12),'object':'chat.completion','created':int(time.time()),'model':MODEL_ID,'choices':[{'index':0,'message':{'role':'assistant','content':content},'finish_reason':finish}]})
                except Exception:error(conn,503,'Local inference unavailable; no automatic retry')
    return {'requests':requests,'completion_attempts':calls}
