"""Headless local client for an explicitly enabled JANUS developer session.

The existing desktop owns the inference broker, permission scope, and Windows
resource caps. This client never launches a model, opens a project, writes
application state, or obtains an internal broker credential.
"""
import argparse
import getpass
import http.client
import json
import os
import re
import sys
from .structured_source import strict_json
from .triad_profiles import MODEL_ID
from .openai_gateway import checked,MAX_BODY,MAX_REPLY

def validate_port(port):
    if type(port) is not int or not 1024<=port<=65535 or port in (8765,8766):
        raise ValueError('Use the temporary developer gateway port, not a broker port')
    return port
def validate_key(key):
    if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{32,128}',key):
        raise ValueError('Temporary developer session key required')
    return key
def call(port,key,operation,payload=None,*,connection=http.client.HTTPConnection):
    validate_port(port);validate_key(key)
    if operation not in ('models','status','chat'):raise ValueError('Unknown local operation')
    if operation=='chat':
        bounded=checked(payload)
        bounded.pop('triad_role')
        raw=json.dumps(bounded,ensure_ascii=True,allow_nan=False).encode('ascii')
        if len(raw)>MAX_BODY:raise ValueError('Request exceeds bound')
        method,path='POST','/v1/chat/completions'
    else:
        if payload is not None:raise ValueError('Read operation does not accept a body')
        raw=None;method='GET';path='/v1/models' if operation=='models' else '/janus/v1/status'
    conn=connection('127.0.0.1',port,timeout=130)
    try:
        conn.request(method,path,body=raw,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','Connection':'close'})
        response=conn.getresponse()
        if response.status!=200:raise ValueError('Local session refused request or unavailable; no automatic retry')
        if response.getheader('Content-Type','').split(';',1)[0]!='application/json' or response.getheader('Content-Encoding','identity')!='identity':
            raise ValueError('Unexpected local API response')
        data=response.read(MAX_REPLY+1)
        if not data or len(data)>MAX_REPLY:raise ValueError('Response exceeds bound')
        result=strict_json(data.decode('utf-8'))
        if not isinstance(result,dict):raise ValueError('Invalid local API response')
        if operation=='chat':
            choices=result.get('choices')
            if result.get('object')!='chat.completion' or result.get('model')!=MODEL_ID or not isinstance(choices,list) or len(choices)!=1:
                raise ValueError('Unexpected completion identity')
            message=choices[0].get('message') if isinstance(choices[0],dict) else None
            if not isinstance(message,dict) or message.get('role')!='assistant' or not isinstance(message.get('content'),str) or not message['content'].strip():
                raise ValueError('Unexpected completion content')
        elif operation=='models':
            if result.get('object')!='list' or not isinstance(result.get('data'),list) or len(result['data'])!=1 or not isinstance(result['data'][0],dict) or result['data'][0].get('id')!=MODEL_ID:
                raise ValueError('Unexpected model listing')
        elif result.get('schema')!='janus-local-status-v1' or result.get('mutated') is not False:
            raise ValueError('Unexpected status identity')
        return result
    finally:conn.close()

def main(argv=None,*,stdin=None,stdout=None,stderr=None,env=None,key_reader=getpass.getpass,transport=call):
    parser=argparse.ArgumentParser(description='Headless client for a user-enabled JANUS loopback session')
    parser.add_argument('--port',required=True,type=int)
    parser.add_argument('operation',choices=('models','status','chat'))
    parser.add_argument('--max-tokens',type=int,default=96)
    args=parser.parse_args(argv)
    stdin=sys.stdin.buffer if stdin is None else stdin
    stdout=sys.stdout if stdout is None else stdout
    stderr=sys.stderr if stderr is None else stderr
    env=os.environ if env is None else env
    try:
        validate_port(args.port)
        payload=None
        if args.operation=='chat':
            data=stdin.read(32001)
            if not data or len(data)>32000:raise ValueError('Supply one bounded UTF-8 prompt on stdin')
            text=data.decode('utf-8')
            if not text.strip() or len(text)>8000:raise ValueError('Invalid prompt')
            payload={'model':MODEL_ID,'messages':[{'role':'user','content':text}],'max_tokens':args.max_tokens,'stream':False}
            checked(payload)
        key=env.get('JANUS_DEVELOPER_KEY')
        if key is None:
            key=key_reader('Temporary JANUS developer key: ')
        result=transport(args.port,validate_key(key),args.operation,payload)
        stdout.write(json.dumps(result,ensure_ascii=True,allow_nan=False)+'\n')
        return 0
    except KeyboardInterrupt:
        stderr.write('Local request interrupted; an already admitted inference may continue.\n');return 130
    except Exception:
        stderr.write('JANUS local request unavailable or invalid; no automatic retry. Check the enabled session and scope.\n');return 1
