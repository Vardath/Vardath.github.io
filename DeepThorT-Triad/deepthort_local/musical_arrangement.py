"""Reviewed multitrack arrangement from explicit musical parts; no invented composition."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.audio_to_midi import vlq

SCHEMA='janus-musical-arrangement-v1'
PPQ=480
MAX_TICKS=30720
MAX_NOTES=512
MAX_BYTES=32768
CHANNELS=(0,1,2,3,4,5,6,7)
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'bpm','parts'} or type(spec['bpm']) is not int or not 40<=spec['bpm']<=220:
        raise ValueError('Expected explicit tempo and arrangement parts')
    parts=spec['parts']
    if not isinstance(parts,list) or not 1<=len(parts)<=8:raise ValueError('Expected 1–8 parts')
    names=set();total=0
    for part in parts:
        if not isinstance(part,dict) or set(part)!={'name','program','notes'}:raise ValueError('Invalid part')
        name=part['name']
        if not isinstance(name,str) or not 1<=len(name)<=48 or not name.strip() or any(not 32<=ord(c)<=126 for c in name) or name.casefold() in names:
            raise ValueError('Part names must be unique printable ASCII')
        names.add(name.casefold())
        if type(part['program']) is not int or not 0<=part['program']<=127:raise ValueError('Invalid General MIDI program')
        notes=part['notes']
        if not isinstance(notes,list) or not notes:raise ValueError('Each part needs notes')
        total+=len(notes)
        if total>MAX_NOTES:raise ValueError('Too many arranged notes')
        previous=None;ends={}
        for row in notes:
            if not isinstance(row,list) or len(row)!=4 or any(type(v) is not int for v in row):raise ValueError('Use [start_tick,duration_ticks,pitch,velocity]')
            start,length,pitch,velocity=row
            if not 0<=start<MAX_TICKS or not 1<=length<=MAX_TICKS or start+length>MAX_TICKS or not 0<=pitch<=127 or not 1<=velocity<=127:
                raise ValueError('Note outside arrangement bounds')
            key=(start,pitch)
            if previous is not None and key<=previous:raise ValueError('Notes must be sorted by start then pitch; no duplicates')
            if start<ends.get(pitch,0):raise ValueError('Same-pitch notes must not overlap within a part')
            previous=key;ends[pitch]=start+length
    return spec
def chunk(track):
    return b'MTrk'+struct.pack('>I',len(track))+track
def midi(spec):
    spec=checked(spec);tempo=round(60_000_000/spec['bpm'])
    tracks=[chunk(b'\x00\xff\x51\x03'+tempo.to_bytes(3,'big')+b'\x00\xff\x2f\x00')]
    for channel,part in zip(CHANNELS,spec['parts']):
        name=part['name'].encode('ascii')
        track=bytearray(b'\x00\xff\x03'+vlq(len(name))+name+bytes((0,0xc0|channel,part['program'])))
        events=[]
        for start,length,pitch,velocity in part['notes']:
            events.extend(((start,1,pitch,velocity),(start+length,0,pitch,0)))
        cursor=0
        for tick,on,pitch,vel in sorted(events):
            track.extend(vlq(tick-cursor)+bytes(((0x90 if on else 0x80)|channel,pitch,vel)));cursor=tick
        track.extend(b'\x00\xff\x2f\x00');tracks.append(chunk(track))
    result=b'MThd'+struct.pack('>IHHH',6,1,len(tracks),PPQ)+b''.join(tracks)
    if len(result)>MAX_BYTES:raise ValueError('Arrangement MIDI exceeds bound')
    return result
def inspect(raw):
    if not isinstance(raw,bytes) or not 40<=len(raw)<=MAX_BYTES or raw[:8]!=b'MThd\x00\x00\x00\x06':raise ValueError('Invalid MIDI header')
    fmt,count,ppq=struct.unpack_from('>HHH',raw,8)
    if fmt!=1 or not 2<=count<=9 or ppq!=PPQ:raise ValueError('Unsupported arrangement profile')
    cursor=14;tracks=[]
    for _ in range(count):
        if raw[cursor:cursor+4]!=b'MTrk' or cursor+8>len(raw):raise ValueError('Invalid track header')
        size=int.from_bytes(raw[cursor+4:cursor+8],'big');cursor+=8
        if size<4 or cursor+size>len(raw):raise ValueError('Truncated track')
        tracks.append(raw[cursor:cursor+size]);cursor+=size
    if cursor!=len(raw):raise ValueError('Extra MIDI data')
    conductor=tracks[0]
    if len(conductor)!=11 or conductor[:4]!=b'\x00\xff\x51\x03' or conductor[7:]!=b'\x00\xff\x2f\x00':raise ValueError('Invalid tempo track')
    tempo=int.from_bytes(conductor[4:7],'big')
    if not tempo:raise ValueError('Invalid tempo')
    parts=[]
    for channel,track in zip(CHANNELS,tracks[1:]):
        pos=0
        def delta():
            nonlocal pos
            n=0
            for _ in range(4):
                if pos>=len(track):raise ValueError('Truncated delta')
                v=track[pos];pos+=1;n=(n<<7)|(v&127)
                if not v&128:return n
            raise ValueError('Oversized delta')
        if track[:3]!=b'\x00\xff\x03':raise ValueError('Missing track name')
        pos=3;n=delta()
        if not 1<=n<=48 or pos+n+3>len(track):raise ValueError('Invalid track name')
        name=track[pos:pos+n].decode('ascii');pos+=n
        if track[pos:pos+2]!=bytes((0,0xc0|channel)):raise ValueError('Missing track program')
        program=track[pos+2];pos+=3;active={};notes=[];tick=0
        while track[pos:]!=b'\x00\xff\x2f\x00':
            tick+=delta()
            if pos+3>len(track) or tick>MAX_TICKS:raise ValueError('Invalid event extent')
            status,pitch,vel=track[pos:pos+3];pos+=3
            if status==0x90|channel and 0<=pitch<=127 and 1<=vel<=127 and pitch not in active:
                active[pitch]=(tick,vel)
            elif status==0x80|channel and pitch in active and vel==0:
                start,velocity=active.pop(pitch);notes.append([start,tick-start,pitch,velocity])
                if len(notes)>MAX_NOTES:raise ValueError('Too many decoded notes')
            else:raise ValueError('Unsupported or unpaired event')
        if active:raise ValueError('Missing note off')
        parts.append({'name':name,'program':program,'notes':sorted(notes,key=lambda row:(row[0],row[2]))})
    spec={'bpm':round(60_000_000/tempo),'parts':parts}
    if midi(spec)!=raw:raise ValueError('Noncanonical arrangement')
    return spec
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mid')
    return plan,dict(spec,scope='Explicit reviewed arrangement only; no automatic harmony or listening claim.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.mid')
def execute(root,plan):
    spec,dst,_=validate(root,plan);payload=midi(spec)
    if inspect(payload)!=spec:raise ValueError('Arrangement roundtrip failed')
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-musical-arrangement-result-v1','status':'multitrack_midi_verified','output':plan['output'],'sha256':sha,
            'bpm':spec['bpm'],'parts':len(spec['parts']),'notes':sum(len(p['notes']) for p in spec['parts']),
            'ticks_per_quarter':PPQ,'musical_quality_verified':False,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed arrangement or output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
