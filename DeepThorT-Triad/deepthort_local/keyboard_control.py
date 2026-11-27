"""Bounded native keyboard message delivery to a hidden JANUS-owned window."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.mouse_control import owned_window,deliver
SCHEMA='janus-owned-window-keyboard-v1'
KEYDOWN=0x0100
KEYUP=0x0101
CHAR=0x0102
KEYS={'LEFT':0x25,'UP':0x26,'RIGHT':0x27,'DOWN':0x28,'BACKSPACE':8,'ENTER':13,'TAB':9,'ESCAPE':27}
def checked(s):
    if not isinstance(s,dict) or set(s)!={'actions'} or not isinstance(s['actions'],list) or not 1<=len(s['actions'])<=16:
        raise ValueError('Choose 1–16 keyboard actions')
    count=0
    for a in s['actions']:
        if not isinstance(a,dict) or a.get('kind') not in ('text','key'):raise ValueError('Choose literal text or named key')
        if a['kind']=='text':
            if set(a)!={'kind','text'} or not isinstance(a['text'],str) or not 1<=len(a['text'])<=32 or any(not 32<=ord(c)<=126 for c in a['text']):
                raise ValueError('Use bounded printable ASCII text')
            count+=len(a['text'])
        else:
            if set(a)!={'kind','key'} or not isinstance(a['key'],str) or a['key'] not in KEYS:
                raise ValueError('Unsupported key; no global shortcuts or modifier chords')
            count+=2
    if count>128:raise ValueError('Keyboard sequence exceeds bound')
    return s

def messages(s):
    out=[]
    for a in checked(s)['actions']:
        if a['kind']=='text':out.extend((CHAR,ord(c),1) for c in a['text'])
        else:
            vk=KEYS[a['key']]
            out.extend(((KEYDOWN,vk,1),(KEYUP,vk,0xc0000001)))
    return out

def native_keyboard(s):
    expected=messages(s)
    with owned_window() as (u,hwnd,events):
        deliver(u,hwnd,os.getpid(),expected,keyboard=True)
        if events!=expected:raise ValueError('Native keyboard event oracle mismatch')
    return {'messages_observed':len(expected),'characters_observed':sum(m[0]==CHAR for m in expected),
            'event_sequence_verified':True,'global_input_used':False,'external_application_controlled':False}

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,scope='Send exact literal characters and selected key down/up messages only to a hidden JANUS-owned test window. No physical keyboard input, clipboard, other applications, shortcuts or credentials.')

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def execute(root,plan):
    s,dst,_=validate(root,plan)
    from deepthort_local.triad_job import verify_root_cap
    verify_root_cap();r=native_keyboard(s);r.update(schema=SCHEMA,shared_root_cap_verified=True)
    sha=guard.publish(json.dumps(r,sort_keys=True,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'status':'native_keyboard_fixture_verified','output':plan['output'],'sha256':sha,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Owned Windows keyboard fixture unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
