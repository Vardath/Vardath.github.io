"""Fixed Windows restricted-token access probe (thread-scoped, no user code).

The kernel performs actual restricted-token access checks. This is one
filesystem boundary test, not a general arbitrary-code or network sandbox.
"""
from __future__ import annotations
import argparse
import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.triad_job import child_server,verify_root_cap
from deepthort_local.disk_gate import DiskGate,require_storage
from deepthort_local.execution_isolation import HostPressure,retry_native_ci
from deepthort_local.source_security import linked

SCHEMA='deepthortriad-windows-restricted-token-probe-v1'
ROOT=Path(__file__).resolve().parents[1]
ALLOWED=b'DeepThorTriad permitted fixture\n'
PROTECTED=b'DeepThorTriad protected fixture\n'
H=w.HANDLE;D=w.DWORD;P=ctypes.c_void_p
TOKEN_QUERY=0x0008
TOKEN_DUPLICATE=0x0002
RESTRICTED_CODE='S-1-5-12'

class SidAttr(ctypes.Structure):
    _fields_=[('sid',P),('attributes',D)]
class TokenGroups(ctypes.Structure):
    _fields_=[('count',D),('first',SidAttr)]

def checked(s):
    if not isinstance(s,dict) or set(s)!={'probe'} or s['probe']!='restricted_token_files':
        raise ValueError('Choose fixed benign restricted-token file probe')
    return s

def assess(r):
    expected={'baseline_allowed_read':True,'baseline_protected_read':True,'baseline_write_open':True,
              'restricted_thread_token_verified':True,'restricted_allowed_read':True,
              'restricted_protected_read_denied':True,'restricted_protected_write_denied':True,
              'restricted_allowed_write_denied':True,'reverted_to_original_identity':True,
              'fixture_contents_unchanged':True}
    if not isinstance(r,dict) or set(r)!=set(expected) or any(r[k] is not v for k,v in expected.items()):
        raise ValueError('Restricted-token access evidence missing or inconsistent')
    return dict(r,restriction_scope='fixed_worker_thread',os_access_check_verified=True,
                arbitrary_code_sandbox=False,network_isolation_verified=False,
                process_wide_restriction_verified=False,filesystem_global_isolation_verified=False)

class Native:
    def __init__(self):
        if os.name!='nt':raise ValueError('Windows required')
        self.k=ctypes.WinDLL('kernel32',use_last_error=True)
        self.a=ctypes.WinDLL('advapi32',use_last_error=True)
        self.close=self.bind(self.k,'CloseHandle',[H],w.BOOL)
        self.free=self.bind(self.k,'LocalFree',[P],P)
        self.process=self.bind(self.k,'GetCurrentProcess',[],H)
        self.thread=self.bind(self.k,'GetCurrentThread',[],H)
        self.open_process=self.bind(self.a,'OpenProcessToken',[H,D,ctypes.POINTER(H)],w.BOOL)
        self.open_thread=self.bind(self.a,'OpenThreadToken',[H,D,w.BOOL,ctypes.POINTER(H)],w.BOOL)
        self.info=self.bind(self.a,'GetTokenInformation',[H,ctypes.c_int,P,D,ctypes.POINTER(D)],w.BOOL)
        self.sid_text=self.bind(self.a,'ConvertSidToStringSidW',[P,ctypes.POINTER(w.LPWSTR)],w.BOOL)
        self.sid_parse=self.bind(self.a,'ConvertStringSidToSidW',[w.LPCWSTR,ctypes.POINTER(P)],w.BOOL)
        self.sd_parse=self.bind(self.a,'ConvertStringSecurityDescriptorToSecurityDescriptorW',[w.LPCWSTR,D,ctypes.POINTER(P),ctypes.POINTER(D)],w.BOOL)
        self.set_security=self.bind(self.a,'SetFileSecurityW',[w.LPCWSTR,D,P],w.BOOL)
        self.restrict=self.bind(self.a,'CreateRestrictedToken',[H,D,D,ctypes.POINTER(SidAttr),D,P,D,ctypes.POINTER(SidAttr),ctypes.POINTER(H)],w.BOOL)
        self.duplicate=self.bind(self.a,'DuplicateToken',[H,ctypes.c_int,ctypes.POINTER(H)],w.BOOL)
        self.impersonate=self.bind(self.a,'ImpersonateLoggedOnUser',[H],w.BOOL)
        self.revert=self.bind(self.a,'RevertToSelf',[],w.BOOL)
        self.is_restricted=self.bind(self.a,'IsTokenRestricted',[H],w.BOOL)
        self.equal_sid=self.bind(self.a,'EqualSid',[P,P],w.BOOL)
    @staticmethod
    def bind(lib,name,args,result):
        f=getattr(lib,name);f.argtypes=args;f.restype=result;return f
    @staticmethod
    def check(ok,label):
        if not ok:raise OSError(ctypes.get_last_error(),label+' failed')
    def token_info(self,token,kind):
        size=D()
        self.info(token,kind,None,0,ctypes.byref(size))
        if not 1<=size.value<=65536:raise ValueError('Token information unavailable')
        buf=ctypes.create_string_buffer(size.value)
        self.check(self.info(token,kind,buf,len(buf),ctypes.byref(size)),'Token information')
        return buf
    def owner(self,token):
        buf=self.token_info(token,1)
        sid=SidAttr.from_buffer(buf).sid
        out=w.LPWSTR()
        self.check(self.sid_text(sid,ctypes.byref(out)),'Token user SID')
        try:
            value=out.value
            if not value or not value.startswith('S-1-'):raise ValueError('Invalid token user')
            return value
        finally:self.free(ctypes.cast(out,P))
    def acl(self,path,user,allow_restricted):
        # Protected DACL: original user and SYSTEM retain full control;
        # the restricted-code SID receives only generic read on one fixture.
        sddl='D:P(A;;FA;;;SY)(A;;FA;;;'+user+')'+('(A;;GR;;;RC)' if allow_restricted else '')
        sd=P()
        self.check(self.sd_parse(sddl,1,ctypes.byref(sd),None),'Fixture security descriptor')
        try:self.check(self.set_security(str(path),0x80000004,sd),'Set protected fixture DACL')
        finally:self.free(sd)
    def verify_restricted(self,token,sid):
        if not self.is_restricted(token):raise ValueError('Kernel token not restricted')
        buf=self.token_info(token,11) # TokenRestrictedSids
        groups=TokenGroups.from_buffer(buf)
        if groups.count!=1 or not self.equal_sid(groups.first.sid,sid):raise ValueError('Unexpected restricting SID')
    def probe(self,stage):
        base=H();restricted=H();imp=H();thread=H();sid=P()
        self.check(self.open_process(self.process(),TOKEN_QUERY|TOKEN_DUPLICATE,ctypes.byref(base)),'Open original process token')
        try:
            if self.is_restricted(base):raise ValueError('Original token already restricted; baseline unavailable')
            user=self.owner(base);allowed=stage/'allowed.txt';protected=stage/'protected.txt'
            for path,data in ((allowed,ALLOWED),(protected,PROTECTED)):
                with path.open('xb') as f:f.write(data)
            self.acl(allowed,user,True);self.acl(protected,user,False)
            if allowed.read_bytes()!=ALLOWED or protected.read_bytes()!=PROTECTED:raise ValueError('Baseline read failed')
            for path in (allowed,protected):
                with path.open('r+b'):pass
            self.check(self.sid_parse(RESTRICTED_CODE,ctypes.byref(sid)),'Restricted-code SID')
            attr=SidAttr(sid,0)
            self.check(self.restrict(base,1,0,None,0,None,1,ctypes.byref(attr),ctypes.byref(restricted)),'Create restricted token')
            self.verify_restricted(restricted,sid)
            self.check(self.duplicate(restricted,2,ctypes.byref(imp)),'Duplicate impersonation token')
            self.check(self.impersonate(imp),'Impersonate restricted token')
            try:
                self.check(self.open_thread(self.thread(),TOKEN_QUERY,True,ctypes.byref(thread)),'Read effective thread token')
                self.verify_restricted(thread,sid)
                if self.owner(thread)!=user:raise ValueError('Unexpected impersonated identity')
                if allowed.read_bytes()!=ALLOWED:raise ValueError('Permitted restricted read failed')
                denied(protected,'rb');denied(protected,'r+b');denied(allowed,'r+b')
            finally:
                if not self.revert():os._exit(1) # never continue in unknown identity
            current=H()
            if self.open_thread(self.thread(),TOKEN_QUERY,True,ctypes.byref(current)):
                self.close(current);raise ValueError('Thread impersonation still active')
            if ctypes.get_last_error()!=1008:raise ValueError('Unable to verify reverted thread token')
            if allowed.read_bytes()!=ALLOWED or protected.read_bytes()!=PROTECTED:
                raise ValueError('Fixture changed')
            return {'baseline_allowed_read':True,'baseline_protected_read':True,'baseline_write_open':True,
                    'restricted_thread_token_verified':True,'restricted_allowed_read':True,
                    'restricted_protected_read_denied':True,'restricted_protected_write_denied':True,
                    'restricted_allowed_write_denied':True,'reverted_to_original_identity':True,
                    'fixture_contents_unchanged':True}
        finally:
            for handle in (thread,imp,restricted,base):
                if handle:self.close(handle)
            if sid:self.free(sid)

def denied(path,mode):
    try:
        with path.open(mode):pass
    except OSError as e:
        if getattr(e,'winerror',None)==5 or (isinstance(e,PermissionError) and e.errno==13 and getattr(e,'winerror',None) is None):return
        raise
    raise ValueError('Restricted token unexpectedly opened fixture')

def run(stage):
    verify_root_cap()
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    sampler=WindowsPressureSampler();_,ram=sampler.read()
    gaming=DiskGate(game_names_path=ROOT/'game_executables.txt',game_flag=ROOT/'state/game-active.flag')
    if ram is None:raise ValueError('Host RAM reading unavailable')
    if ram<15:raise HostPressure('Host RAM below admission reserve')
    if gaming.gaming():raise ValueError('Gaming priority')
    exe=str(Path(sys._base_executable).resolve(strict=True));log=stage/'probe.log'
    with child_server([exe,'-I','-B',str(Path(__file__).resolve()),'--worker',str(stage)],stage,log,
                      memory_limit=128*1024**2,process_limit=1) as (pid,alive):
        if not alive.member(pid):raise ValueError('Restricted probe outside cleanup scope')
        deadline=time.monotonic()+20
        while alive():
            cpu,free=sampler.read()
            if gaming.gaming():raise ValueError('Gaming priority')
            if free is None:raise ValueError('Host RAM reading unavailable')
            if free<10 or (cpu is not None and cpu>=90):raise HostPressure('Transient host pressure')
            if time.monotonic()>=deadline or log.stat().st_size>8192:raise ValueError('Probe time or log bound')
            time.sleep(.1)
        if alive.code()!=0:raise ValueError('Restricted-token native worker failed: '+log.read_text(encoding='utf8',errors='replace')[-500:])
    return assess(json.loads(guard.read_bound(log,8192).decode('utf8')))

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,scope='Fixed native Windows restricted-token thread probe in a capped child. Create two benign temporary files with explicit protected ACLs; verify original access, restricted allowed read, denied protected read and denied writes; revert identity and verify both files unchanged. No project code execution or global sandbox claim.')

def execute(root,plan,*,backend=None):
    s,dst,_=validate(root,plan);require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.deepthortriad-token-probe-',dir=dst.parent) as tmp:
        result=run(Path(tmp)) if backend is None else assess(backend(Path(tmp)))
    result.update(schema=SCHEMA,backend='native_windows_token' if backend is None else 'injected_fixture')
    digest=guard.publish((json.dumps(result,sort_keys=True,indent=2)+'\n').encode(),dst,lambda:validate(root,plan))
    return dict(result,status='restricted_token_boundary_probe_saved',output=plan['output'],sha256=digest)

def main():
    p=argparse.ArgumentParser();p.add_argument('--root');p.add_argument('--plan');p.add_argument('--worker');p.add_argument('--native-ci',action='store_true');p.add_argument('--ci-inside');a=p.parse_args()
    try:
        if a.worker:
            verify_root_cap();stage=Path(a.worker).resolve(strict=True)
            if stage!=Path.cwd().resolve() or linked(stage):raise ValueError('Worker requires its isolated stage')
            print(json.dumps(Native().probe(stage),sort_keys=True),flush=True)
        elif a.native_ci:
            from deepthort_local.win_cpu_cap import run_capped
            with tempfile.TemporaryDirectory(prefix='deepthortriad-token-ci-') as tmp:
                report=Path(tmp)/'receipt.json'
                code=run_capped([sys.executable,str(Path(__file__).resolve()),'--ci-inside',str(report)],cwd=str(ROOT))
                if report.is_file():print(guard.read_bound(report,8192).decode('utf8'),flush=True)
                else:print('Native restricted-token probe produced no receipt',flush=True)
                return code
        elif a.ci_inside:
            def attempt():
                with tempfile.TemporaryDirectory(prefix='deepthortriad-token-native-') as tmp:return run(Path(tmp))
            Path(a.ci_inside).write_text(json.dumps(retry_native_ci(attempt),sort_keys=True),encoding='utf8')
        else:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True)
        return 0
    except Exception as e:
        result={'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:500]}
        if a.ci_inside:Path(a.ci_inside).write_text(json.dumps(result),encoding='utf8')
        print(json.dumps(result),flush=True);return 1
if __name__=='__main__':sys.exit(main())
