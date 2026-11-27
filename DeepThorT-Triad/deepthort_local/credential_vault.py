"""Explicit JANUS-owned, repository/operation-scoped Windows credential storage."""
import ctypes
import os
from ctypes import wintypes as w
from .github_pull_request import repository
from .web_search import token_checked

MODES=('review','pull_request','release')
def target(repo,mode):
    if mode not in MODES:raise ValueError('Unknown credential purpose')
    return 'JANUS/GitHub/v1/'+repository(repo).lower()+'/'+mode
def available():return os.name=='nt'

class Credential(ctypes.Structure):
    _fields_=[('Flags',w.DWORD),('Type',w.DWORD),('TargetName',w.LPWSTR),('Comment',w.LPWSTR),
        ('LastWritten',w.FILETIME),('CredentialBlobSize',w.DWORD),('CredentialBlob',ctypes.POINTER(ctypes.c_ubyte)),
        ('Persist',w.DWORD),('AttributeCount',w.DWORD),('Attributes',ctypes.c_void_p),
        ('TargetAlias',w.LPWSTR),('UserName',w.LPWSTR)]

class WindowsVault:
    def __init__(self):
        if not available():raise OSError('Windows Credential Manager unavailable')
        api=ctypes.WinDLL('Advapi32.dll',use_last_error=True)
        self.read=api.CredReadW
        self.read.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,ctypes.POINTER(ctypes.POINTER(Credential))]
        self.write=api.CredWriteW
        self.write.argtypes=[ctypes.POINTER(Credential),w.DWORD]
        self.delete=api.CredDeleteW
        self.delete.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD]
        for fn in (self.read,self.write,self.delete):fn.restype=w.BOOL
        self.free=api.CredFree;self.free.argtypes=[ctypes.c_void_p];self.free.restype=None
    def get(self,name):
        p=ctypes.POINTER(Credential)()
        if not self.read(name,1,0,ctypes.byref(p)):
            if ctypes.get_last_error()==1168:return None
            raise OSError('Credential retrieval failed')
        try:
            c=p.contents
            if c.Type!=1 or c.TargetName!=name or not c.CredentialBlob or not 8<=c.CredentialBlobSize<=512:
                raise ValueError('Invalid stored credential')
            try:return ctypes.string_at(c.CredentialBlob,c.CredentialBlobSize).decode('ascii')
            except UnicodeError:raise ValueError('Invalid stored credential') from None
        finally:self.free(p)
    def put(self,name,secret):
        buf=(ctypes.c_ubyte*len(secret)).from_buffer_copy(secret.encode('ascii'))
        try:
            c=Credential();c.Type=1;c.TargetName=name;c.CredentialBlobSize=len(buf)
            c.CredentialBlob=ctypes.cast(buf,ctypes.POINTER(ctypes.c_ubyte));c.Persist=2;c.UserName='JANUS'
            if not self.write(ctypes.byref(c),0):raise OSError('Credential storage failed')
        finally:ctypes.memset(buf,0,len(buf))
    def remove(self,name):
        if self.delete(name,1,0):return True
        if ctypes.get_last_error()==1168:return False
        raise OSError('Credential removal failed')

def _approved(approved):
    if approved is not True:raise PermissionError('Explicit credential approval required')
def save(repo,mode,secret,*,approved=False,backend=None):
    _approved(approved);name=target(repo,mode)
    try:token_checked(secret)
    except ValueError:raise ValueError('Invalid credential format') from None
    (backend if backend is not None else WindowsVault()).put(name,secret)
def retrieve(repo,mode,*,approved=False,backend=None):
    _approved(approved);name=target(repo,mode)
    value=(backend if backend is not None else WindowsVault()).get(name)
    if value is None:return None
    try:return token_checked(value)
    except ValueError:raise ValueError('Invalid stored credential') from None
def forget(repo,mode,*,approved=False,backend=None):
    _approved(approved);name=target(repo,mode)
    return (backend if backend is not None else WindowsVault()).remove(name)
