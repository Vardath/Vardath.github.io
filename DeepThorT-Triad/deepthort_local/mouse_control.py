"""Bounded Windows client-coordinate mouse delivery to a JANUS-owned test window."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import secrets
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard

SCHEMA='janus-owned-window-mouse-v1'
MOVE=0x0200
DOWN=0x0201
UP=0x0202
MAX_COORD=63

def checked(s):
    if not isinstance(s,dict) or set(s)!={'actions'} or not isinstance(s['actions'],list) or not 1<=len(s['actions'])<=16:
        raise ValueError('Choose 1–16 mouse actions')
    for a in s['actions']:
        if not isinstance(a,dict) or set(a)!={'kind','x','y'} or a['kind'] not in ('move','click'):
            raise ValueError('Only move and left click supported')
        if any(type(a[k]) is not int or not 0<=a[k]<=MAX_COORD for k in ('x','y')):
            raise ValueError('Use bounded client coordinates 0–63')
    return s

def messages(s):
    result=[]
    for a in checked(s)['actions']:
        pos=a['x']|(a['y']<<16)
        result.append((MOVE,0,pos))
        if a['kind']=='click':result.extend(((DOWN,1,pos),(UP,0,pos)))
    return result

def fn(dll,name,args,restype):
    f=getattr(dll,name);f.argtypes=args;f.restype=restype;return f

@contextmanager
def owned_window():
    """Hidden native fixture, no global cursor or foreground input."""
    if os.name!='nt':raise RuntimeError('Windows native input required')
    u=ctypes.WinDLL('user32',use_last_error=True)
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    L=ctypes.c_ssize_t;U=ctypes.c_size_t;H=w.HWND
    proc_type=ctypes.WINFUNCTYPE(L,H,w.UINT,U,L)
    default=fn(u,'DefWindowProcW',[H,w.UINT,U,L],L)
    events=[]
    @proc_type
    def proc(hwnd,msg,wp,lp):
        if msg in (MOVE,DOWN,UP):
            events.append((int(msg),int(wp),int(lp)))
            return 0
        return default(hwnd,msg,wp,lp)
    class WndClass(ctypes.Structure):
        _fields_=[('style',w.UINT),('lpfnWndProc',proc_type),('cbClsExtra',ctypes.c_int),
                  ('cbWndExtra',ctypes.c_int),('hInstance',w.HINSTANCE),('hIcon',w.HANDLE),
                  ('hCursor',w.HANDLE),('hbrBackground',w.HANDLE),('lpszMenuName',w.LPCWSTR),('lpszClassName',w.LPCWSTR)]
    name='JANUS_Input_'+secrets.token_hex(12)
    instance=fn(k,'GetModuleHandleW',[w.LPCWSTR],w.HMODULE)(None)
    cls=WndClass();cls.lpfnWndProc=proc;cls.hInstance=instance;cls.lpszClassName=name
    register=fn(u,'RegisterClassW',[ctypes.POINTER(WndClass)],w.ATOM)
    unregister=fn(u,'UnregisterClassW',[w.LPCWSTR,w.HINSTANCE],w.BOOL)
    if not register(ctypes.byref(cls)):raise ctypes.WinError(ctypes.get_last_error())
    hwnd=None
    try:
        create=fn(u,'CreateWindowExW',[w.DWORD,w.LPCWSTR,w.LPCWSTR,w.DWORD,ctypes.c_int,ctypes.c_int,
            ctypes.c_int,ctypes.c_int,H,w.HMENU,w.HINSTANCE,ctypes.c_void_p],H)
        # WS_POPUP, without WS_VISIBLE: never steals focus or displays over user work.
        hwnd=create(0,name,'JANUS input fixture',0x80000000,0,0,128,128,None,None,instance,None)
        if not hwnd:raise ctypes.WinError(ctypes.get_last_error())
        yield u,hwnd,events
    finally:
        if hwnd:fn(u,'DestroyWindow',[H],w.BOOL)(hwnd)
        unregister(name,instance)

def deliver(u,hwnd,pid,sequence):
    """Recheck ownership and client geometry before each bounded native message."""
    H=w.HWND;L=ctypes.c_ssize_t;U=ctypes.c_size_t
    owner=fn(u,'GetWindowThreadProcessId',[H,ctypes.POINTER(w.DWORD)],w.DWORD)
    rect=fn(u,'GetClientRect',[H,ctypes.POINTER(w.RECT)],w.BOOL)
    send=fn(u,'SendMessageTimeoutW',[H,w.UINT,U,L,w.UINT,w.UINT,ctypes.POINTER(U)],L)
    if pid!=os.getpid() or not 1<=len(sequence)<=48:raise ValueError('Only current owned fixture allowed')
    for msg,wp,lp in sequence:
        actual=w.DWORD();bounds=w.RECT()
        if not owner(hwnd,ctypes.byref(actual)) or actual.value!=pid or not rect(hwnd,ctypes.byref(bounds)):
            raise ValueError('Owned window identity unavailable')
        x=lp&0xffff;y=(lp>>16)&0xffff
        if msg not in (MOVE,DOWN,UP) or wp!=(1 if msg==DOWN else 0) or not 0<=x<bounds.right or not 0<=y<bounds.bottom:
            raise ValueError('Invalid client mouse message')
        result=U()
        if not send(hwnd,msg,wp,lp,0x0002,1000,ctypes.byref(result)):
            raise ValueError('Window message delivery failed')

def native_mouse(s):
    expected=messages(s)
    with owned_window() as (u,hwnd,events):
        deliver(u,hwnd,os.getpid(),expected)
        if events!=expected:raise ValueError('Native mouse event oracle mismatch')
    return {'messages_observed':len(expected),'clicks_observed':sum(a['kind']=='click' for a in s['actions']),
            'event_sequence_verified':True,'global_input_used':False,'external_application_controlled':False}

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,scope='Deliver bounded mouse move/click messages only to a hidden JANUS-owned native test window. No physical cursor movement, foreground changes or external application input.')

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def execute(root,plan):
    s,dst,_=validate(root,plan)
    from deepthort_local.triad_job import verify_root_cap
    verify_root_cap();r=native_mouse(s);r.update(schema=SCHEMA,shared_root_cap_verified=True)
    digest=guard.publish(json.dumps(r,sort_keys=True,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'native_mouse_fixture_verified','output':plan['output'],'sha256':digest,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Owned Windows mouse fixture unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
