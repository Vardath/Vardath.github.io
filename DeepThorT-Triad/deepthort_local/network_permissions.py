"""Persistent owner-controlled permission gate for shared pinned HTTPS transport.

A restriction only: an allowed host still requires every existing tool-specific
approval, account grant and safety check. This is not a firewall, sandbox or
control over other network stacks, external tools or already sent requests.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import tempfile
from .source_security import linked

SCHEMA='deepthortriad-pinned-network-policy-v1'
POLICY_PATH=Path(__file__).resolve().parents[1]/'state'/'network-permissions.json'
HOST=re.compile(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+')
DEFAULT={'schema':SCHEMA,'mode':'reviewed','hosts':[]}

def hostname(value):
    if not isinstance(value,str) or len(value)>253 or not HOST.fullmatch(value):
        raise ValueError('Expected exact lowercase DNS hostname')
    return value

def validate(value):
    if (not isinstance(value,dict) or set(value)!=set(DEFAULT) or value['schema']!=SCHEMA
            or value['mode'] not in ('reviewed','blocked','allowlist')
            or not isinstance(value['hosts'],list) or len(value['hosts'])>64):
        raise ValueError('Invalid network restriction policy')
    hosts=sorted({hostname(h) for h in value['hosts']})
    if hosts!=value['hosts'] or bool(hosts)!=(value['mode']=='allowlist'):
        raise ValueError('Invalid host allowlist')
    return {'schema':SCHEMA,'mode':value['mode'],'hosts':hosts}

def current():
    path=POLICY_PATH
    if not os.path.lexists(path.parent):
        return dict(DEFAULT,hosts=[])
    if linked(path.parent) or not path.parent.is_dir():
        raise PermissionError('Unsafe network policy directory')
    if not os.path.lexists(path):
        return dict(DEFAULT,hosts=[])
    if linked(path) or not path.is_file():
        raise PermissionError('Unsafe network policy file')
    try:
        with path.open('rb') as f:raw=f.read(20001)
        if len(raw)>20000:raise ValueError('Policy exceeds size bound')
        return validate(json.loads(raw))
    except (ValueError,UnicodeError,TypeError) as exc:
        raise PermissionError('Invalid network policy; shared HTTPS blocked') from exc

def require(host):
    host=hostname(host)
    policy=current()
    if policy['mode']=='blocked' or (policy['mode']=='allowlist' and host not in policy['hosts']):
        raise PermissionError('Owner network restriction blocks '+host)
    return True

def from_text(text):
    if not isinstance(text,str):raise ValueError('Invalid network policy input')
    text=text.strip()
    if text in ('reviewed','blocked'):
        return {'schema':SCHEMA,'mode':text,'hosts':[]}
    hosts=sorted({hostname(x.strip()) for x in text.split(',')})
    return validate({'schema':SCHEMA,'mode':'allowlist','hosts':hosts})

def save(policy,*,approval=False):
    if approval is not True:raise PermissionError('Explicit owner approval required')
    policy=validate(policy);path=POLICY_PATH
    # Never overwrite a linked or unreadable policy. An existing malformed
    # ordinary file can be repaired by an explicit owner action.
    if not path.parent.is_dir() or linked(path.parent):
        raise PermissionError('Unsafe network policy directory')
    if os.path.lexists(path) and (linked(path) or not path.is_file()):
        raise PermissionError('Unsafe network policy file')
    fd,name=tempfile.mkstemp(prefix='.network-permission-',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf8') as out:
            json.dump(policy,out,sort_keys=True);out.flush();os.fsync(out.fileno())
        if linked(path.parent) or (os.path.lexists(path) and (linked(path) or not path.is_file())):
            raise PermissionError('Network policy destination changed')
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)
    if current()!=policy:raise ValueError('Network policy persistence verification failed')
    return policy
