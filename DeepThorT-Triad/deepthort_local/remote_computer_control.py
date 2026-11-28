"""Reviewed manual RDP session handoff to an explicitly authorised computer.

No remote agent, arbitrary shell, unattended input, credential collection,
authentication bypass, or remote session success claim.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import network_permissions as network
from deepthort_local.action_guards import snapshot_file
from deepthort_local.source_security import linked
from deepthort_local.disk_gate import DiskGate,require_storage

SCHEMA='deepthortriad-reviewed-remote-desktop-v1'
ROOT=Path(__file__).resolve().parents[1]

def checked(s):
    if not isinstance(s,dict) or set(s)!={'host','port','seconds','authorised_host'}:
        raise ValueError('Choose an exact authorised remote computer, port and duration')
    network.hostname(s['host'])
    if s['authorised_host'] is not True:raise ValueError('Explicit authority over remote computer required')
    if type(s['port']) is not int or not 1<=s['port']<=65535:raise ValueError('Invalid RDP port')
    if type(s['seconds']) is not int or not 15<=s['seconds']<=120:raise ValueError('Choose 15–120 seconds of manual client access')
    return s

def profile(s):
    checked(s)
    fields={
        'full address:s':s['host']+':'+str(s['port']),
        'prompt for credentials:i':'1','promptcredentialonce:i':'0',
        'authentication level:i':'1','enablecredsspsupport:i':'1',
        'negotiate security layer:i':'1','screen mode id:i':'1',
        'desktopwidth:i':'1024','desktopheight:i':'768',
        'redirectclipboard:i':'0','redirectprinters:i':'0',
        'redirectcomports:i':'0','redirectsmartcards:i':'0',
        'redirectposdevices:i':'0','redirectwebauthn:i':'0',
        'redirectlocation:i':'0','redirectdrives:i':'0',
        'drivestoredirect:s':'','devicestoredirect:s':'','camerastoredirect:s':'',
        'usbdevicestoredirect:s':'','audiocapturemode:i':'0','audiomode:i':'2',
        'autoreconnection enabled:i':'0','gatewayusagemethod:i':'0',
        'administrative session:i':'0','disableconnectionsharing:i':'1',
        'use redirection server name:i':'0',
    }
    return ('\r\n'.join(k+':'+v for k,v in fields.items())+'\r\n').encode('utf-16')

def runtime():
    if os.name!='nt':raise ValueError('Windows Remote Desktop client required')
    folder=Path(os.environ['SystemRoot']).resolve(strict=True)/'System32'
    exe=folder/'mstsc.exe'
    if linked(folder) or linked(exe) or not exe.is_file():raise ValueError('Trusted installed Windows RDP client unavailable')
    return snapshot_file(exe,kind='stat')

def validate(root,plan):
    if not isinstance(plan,dict) or 'client' not in plan:raise ValueError('Invalid remote desktop approval')
    s,dst,_=guard.validate(root,{k:v for k,v in plan.items() if k!='client'},schema=SCHEMA,checked=checked,output_suffix='.json')
    network.require(s['host'])
    if plan['client']!=runtime():raise ValueError('Reviewed RDP client changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    plan['client']=runtime();validate(root,plan)
    return plan,dict(s,client=plan['client'],scope='Connect the visible native Windows Remote Desktop client to this exact authorised host. You must authenticate and operate manually. Certificate failure must abort. Local device redirection disabled in the profile; Windows/client/server policies may further affect behaviour. No credentials collected, remote agent installed or autonomous input sent. Closing the client can leave the remote session running; remote authentication and identity are not independently verified by this tool.')

def run(s,stage,client):
    from deepthort_local.triad_job import child_server,verify_root_cap
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    verify_root_cap();sampler=WindowsPressureSampler()
    gaming=DiskGate(game_names_path=ROOT/'game_executables.txt',game_flag=ROOT/'state/game-active.flag')
    _,free=sampler.read()
    if gaming.gaming() or free is None or free<15:raise ValueError('Gaming priority or host reserve')
    rdp=stage/'reviewed.rdp';rdp.write_bytes(profile(s))
    log=stage/'client.log';network.require(s['host'])
    if runtime()!=client:raise ValueError('RDP client changed before launch')
    observed=False
    with child_server([client['path'],str(rdp)],stage,log) as (pid,alive):
        if not alive.member(pid):raise ValueError('RDP client outside reviewed cleanup scope')
        deadline=time.monotonic()+s['seconds']
        status='duration_elapsed'
        while alive():
            observed=True
            _,free=sampler.read()
            try:network.require(s['host'])
            except PermissionError:status='network_policy_changed';break
            if gaming.gaming() or free is None or free<10:
                status='resource_preempted';break
            if time.monotonic()>=deadline:break
            if log.stat().st_size>65536:status='log_bound';break
            time.sleep(.25)
        else:status='client_exited'
    return {'client_process_observed':observed,'client_scope_closed':True,'stop_reason':status}

def execute(root,plan,*,backend=None):
    s,dst=validate(root,plan);require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.deepthortriad-rdp-',dir=dst.parent) as tmp:
        r=(backend or run)(s,Path(tmp),plan['client'])
    if (not isinstance(r,dict) or set(r)!={'client_process_observed','client_scope_closed','stop_reason'}
        or type(r['client_process_observed']) is not bool or r['client_scope_closed'] is not True
        or r['stop_reason'] not in ('duration_elapsed','client_exited','resource_preempted','network_policy_changed','log_bound')):
        raise ValueError('Invalid client observation receipt')
    report={'schema':SCHEMA,'host':s['host'],'port':s['port'],'seconds':s['seconds'],**r,
            'rdp_profile_sha256':hashlib.sha256(profile(s)).hexdigest(),
            'backend':'native_mstsc' if backend is None else 'injected_fixture',
            'manual_authentication_required':True,'credentials_collected':False,'autonomous_input_sent':False,
            'remote_connection_verified':False,'remote_session_closed_verified':False}
    payload=(json.dumps(report,sort_keys=True,indent=2)+'\n').encode()
    # Remote activity cannot be rolled back. A changed policy can prevent
    # receipt publication; do not automatically retry the connection.
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return dict(report,status='remote_client_observation_saved',output=plan['output'],sha256=digest)

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_unconfirmed','error_type':type(e).__name__,'reason':str(e)[:300],
                          'retry_automatically':False}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
