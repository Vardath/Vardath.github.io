"""Generate reviewed editable REAPER JSFX stereo gain/balance effects with reference DSP vectors."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard

SCHEMA='janus-audio-plugin-v1'

def checked(s):
    if not isinstance(s,dict) or set(s)!={'name','gain_db','balance','ceiling'}:
        raise ValueError('Choose plugin name, gain, balance and sample ceiling')
    if not isinstance(s['name'],str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9 _-]{0,59}',s['name']):
        raise ValueError('Use a bounded literal plugin name')
    for k,lo,hi in (('gain_db',-24,12),('balance',-1,1),('ceiling',0.1,1)):
        v=s[k]
        if type(v) not in (int,float) or not math.isfinite(v) or not lo<=v<=hi:
            raise ValueError('Control outside range: '+k)
        if abs(v*100-round(v*100))>1e-8:raise ValueError('Use at most two decimal places')
    return s

def source(s):
    checked(s)
    return ('desc:'+s['name']+'\n'
            'in_pin:Left\nin_pin:Right\nout_pin:Left\nout_pin:Right\n'
            f"slider1:{s['gain_db']:.2f}<-24,12,0.01>Gain (dB)\n"
            f"slider2:{s['balance']:.2f}<-1,1,0.01>Balance\n"
            f"slider3:{s['ceiling']:.2f}<0.1,1,0.01>Hard sample ceiling\n\n"
            '@sample\n'
            'gain = 10^(max(-24,min(12,slider1))/20);\n'
            'bal = max(-1,min(1,slider2));\n'
            'limit = max(0.1,min(1,slider3));\n'
            'left = spl0*gain*(1-max(0,bal));\n'
            'right = spl1*gain*(1+min(0,bal));\n'
            'spl0 = max(-limit,min(limit,left));\n'
            'spl1 = max(-limit,min(limit,right));\n').encode('ascii')

def reference(s,left,right):
    checked(s)
    gain=10**(s['gain_db']/20)
    bal=s['balance'];limit=s['ceiling']
    return [max(-limit,min(limit,left*gain*(1-max(0,bal)))),
            max(-limit,min(limit,right*gain*(1+min(0,bal))))]

def bundle(s):
    src=source(s)
    vectors=[{'input':list(pair),'expected':reference(s,*pair)} for pair in
             ((0,0),(.25,-.5),(1,1),(-1,-1),(.5,0),(0,.5))]
    if any(not math.isfinite(v) or abs(v)>s['ceiling'] for row in vectors for v in row['expected']):
        raise ValueError('Reference DSP outside sample ceiling')
    receipt={'schema':SCHEMA,'format':'REAPER JSFX','name':s['name'],'defaults':{k:s[k] for k in ('gain_db','balance','ceiling')},
             'source_sha256':hashlib.sha256(src).hexdigest(),'reference_vectors':vectors,
             'reference_math_verified':True,'native_plugin_compiled':False,'native_host_verified':False,'installed':False}
    entries={'JANUS-effect.jsfx':src,'PLUGIN.json':(json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode(),
             'README.txt':b'Editable REAPER JSFX source. Review before manual installation into REAPER Effects. Test at low monitoring level. Hard sample clipping is intentional; no true-peak or listening claim. Python reference vectors are not a native host test.\n'}
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_STORED) as z:
        for name,raw in entries.items():z.writestr(zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0)),raw)
    payload=buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or z.namelist()!=list(entries) or any(z.read(k)!=v for k,v in entries.items()):
            raise ValueError('Plugin bundle verification failed')
    return payload,receipt

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.zip')

def review(root,source_path,output,exclude=()):
    plan,s=guard.review(root,source_path,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip')
    _,receipt=bundle(s)
    return plan,dict(s,observations=receipt,scope='Generate editable fixed JSFX stereo gain/balance/hard-ceiling source and reference math vectors; no arbitrary script, installation or native host acceptance.')

def execute(root,plan):
    s,dst,_=validate(root,plan)
    payload,receipt=bundle(s)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'jsfx_source_bundle_verified','output':plan['output'],'sha256':digest,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed plugin generation unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
