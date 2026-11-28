"""Operate an exact standard Edit control in a newly launched, reviewed project executable."""
from __future__ import annotations
import argparse
import ctypes
from ctypes import wintypes as w
import json
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import verify_guards
from deepthort_local.mouse_control import fn
SCHEMA='janus-reviewed-gui-edit-v1'
EXTRA=('executable','.exe')
MAX_LOG=1024*1024

def checked(s):
    if not isinstance(s,dict) or set(s)!={'executable','window_title','window_class','control_id','text'} or not isinstance(s['executable'],str):
        raise ValueError('Choose exact project executable, window title/class, Edit ID and literal text')
    for k,limit in (('window_title',160),('window_class',120),('text',120)):
        v=s[k]
        if not isinstance(v,str) or not 1<=len(v)<=limit or any(not 32<=ord(c)<=126 for c in v):
            raise ValueError('Use bounded printable ASCII values')
    if type(s['control_id']) is not int or not 1<=s['control_id']<=65535:raise ValueError('Use exact positive control ID')
    return s

class Windows:
    def __init__(self):
        self.u=ctypes.WinDLL('user32',use_last_error=True)
        H=w.HWND;L=ctypes.c_ssize_t;U=ctypes.c_size_t
        self.owner=fn(self.u,'GetWindowThreadProcessId',[H,ctypes.POINTER(w.DWORD)],w.DWORD)
        self.title=fn(self.u,'GetWindowTextW',[H,w.LPWSTR,ctypes.c_int],ctypes.c_int)
        self.cls=fn(self.u,'GetClassNameW',[H,w.LPWSTR,ctypes.c_int],ctypes.c_int)
        self.visible=fn(self.u,'IsWindowVisible',[H],w.BOOL)
        self.enabled=fn(self.u,'IsWindowEnabled',[H],w.BOOL)
        self.parent=fn(self.u,'GetParent',[H],H)
        self.child=fn(self.u,'GetDlgItem',[H,ctypes.c_int],H)
        self.control_id=fn(self.u,'GetDlgCtrlID',[H],ctypes.c_int)
        self.style=fn(self.u,'GetWindowLongW',[H,ctypes.c_int],ctypes.c_long)
        self.send=fn(self.u,'SendMessageTimeoutW',[H,w.UINT,U,L,w.UINT,w.UINT,ctypes.POINTER(U)],L)
    def pid(self,hwnd):
        value=w.DWORD()
        if not self.owner(hwnd,ctypes.byref(value)):raise ValueError('Window owner unavailable')
        return int(value.value)
    def text(self,method,hwnd):
        b=ctypes.create_unicode_buffer(256)
        n=method(hwnd,b,len(b))
        if not 0<n<255:return ''
        return b.value
    def matching(self,pid,title,cls):
        rows=[]
        cbtype=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,ctypes.c_ssize_t)
        @cbtype
        def visit(hwnd,_):
            try:
                if self.pid(hwnd)==pid and self.visible(hwnd) and self.text(self.title,hwnd)==title and self.text(self.cls,hwnd)==cls:rows.append(hwnd)
            except ValueError:pass
            return True
        if not fn(self.u,'EnumWindows',[cbtype,ctypes.c_ssize_t],w.BOOL)(visit,0):raise ValueError('Window enumeration failed')
        if len(rows)>1:raise ValueError('Ambiguous reviewed window')
        return rows[0] if rows else None
    def edit(self,parent,pid,ident):
        if self.pid(parent)!=pid:raise ValueError('Parent identity changed')
        hwnd=self.child(parent,ident)
        if (not hwnd or self.pid(hwnd)!=pid or self.parent(hwnd)!=parent or self.control_id(hwnd)!=ident
            or self.text(self.cls,hwnd).casefold()!='edit' or not self.enabled(hwnd)
            or self.style(hwnd,-16)&(0x20|0x800)): # ES_PASSWORD or ES_READONLY
            raise ValueError('Exact enabled non-password standard Edit control required')
        return hwnd
    def message(self,hwnd,msg,wp,lp):
        result=ctypes.c_size_t()
        if not self.send(hwnd,msg,wp,lp,0x0002,1000,ctypes.byref(result)):raise ValueError('Window message failed')
        return result.value
    def set_text(self,parent,pid,ident,value,*,still_owned):
        def target():
            if not still_owned(pid):raise ValueError('Child is no longer within approved cleanup scope')
            return self.edit(parent,pid,ident)
        hwnd=target()
        incoming=ctypes.create_unicode_buffer(value)
        if not self.message(hwnd,0x000c,0,ctypes.addressof(incoming)):raise ValueError('Edit rejected literal value')
        if target()!=hwnd:raise ValueError('Control changed after edit')
        # Read back at most the reviewed length plus one extra character;
        # never persist or log an unexpected value.
        outgoing=ctypes.create_unicode_buffer(len(value)+2)
        n=self.message(hwnd,0x000d,len(outgoing),ctypes.addressof(outgoing))
        if target()!=hwnd or n!=len(value) or outgoing.value!=value:raise ValueError('Edit readback did not match')
        return True

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    return plan,dict(s,scope='Launch the exact trusted project executable in a fresh capped child process. On its uniquely matching visible top-level window, set one exact direct standard Edit control and verify literal readback. May display a window and trigger application side effects; executable runs with your user permissions. No existing applications, passwords, global input, arbitrary commands or clicks. Close the entire child scope afterward. Not a security sandbox.')

def operate(s,exe,stage,plan):
    from deepthort_local.triad_job import verify_root_cap,child_server
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    verify_root_cap();sampler=WindowsPressureSampler();_,ram=sampler.read()
    if ram is None or ram<15:raise ValueError('Insufficient RAM reserve')
    log=stage/'gui.log';verify_guards(plan['guards'])
    with child_server([str(exe)],exe.parent,log) as (pid,alive):
        if not alive.member(pid):raise ValueError('Child outside cleanup job')
        backend=Windows();deadline=time.monotonic()+25
        while True:
            cpu,ram=sampler.read()
            if not alive() or not alive.member(pid) or time.monotonic()>=deadline or ram is None or ram<10 or (cpu is not None and cpu>=90) or log.stat().st_size>MAX_LOG:
                raise ValueError('Approved window unavailable within resource bounds')
            hwnd=backend.matching(pid,s['window_title'],s['window_class'])
            if hwnd:break
            time.sleep(.25)
        verify_guards(plan['guards'])
        if backend.matching(pid,s['window_title'],s['window_class'])!=hwnd:raise ValueError('Window changed')
        backend.set_text(hwnd,pid,s['control_id'],s['text'],still_owned=lambda p:alive() and alive.member(p))
    return {'literal_readback_verified':True,'control_class':'Edit','control_id':s['control_id'],
            'characters':len(s['text']),'global_input_used':False,'external_application_controlled':True,
            'application_task_success_verified':False,'cleanup_scope_closed':True,'shared_root_cap_verified':True}

def execute(root,plan):
    s,dst,exe=validate(root,plan)
    from deepthort_local.disk_gate import require_storage
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-gui-edit-',dir=dst.parent) as tmp:
        result=operate(s,exe,Path(tmp),plan)
    result.update(schema=SCHEMA,executable_sha256=plan['guards'][1]['expected'])
    sha=guard.publish(json.dumps(result,sort_keys=True,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'standard_edit_readback_verified','output':plan['output'],'sha256':sha,**result}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'unconfirmed','error_type':type(e).__name__,'reason':'Reviewed GUI operation unavailable; application may already have acted'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
