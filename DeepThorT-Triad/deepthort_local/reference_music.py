"""Reference-conditioned new score using measured tempo and tonal-centre evidence."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import tempo_detection as tempo
from deepthort_local import musical_key as key
from deepthort_local import musical_arrangement as arrangement
from deepthort_local import instrumental_synthesis as synth
from deepthort_local.disk_gate import require_storage

SCHEMA='deepthortriad-reference-music-v1'
EXTRA=('reference','.wav')
SCALES={'major':(0,2,4,5,7,9,11),'minor':(0,2,3,5,7,8,10)}

def checked(s):
    if not isinstance(s,dict) or set(s)!={'reference','min_bpm','max_bpm','channel','bars','seed','lead_timbre','backing_timbre','peak_dbfs'} or not isinstance(s['reference'],str):
        raise ValueError('Expected exact audio reference, tempo range, channel and synthesis controls')
    tempo.checked({'audio':s['reference'],'min_bpm':s['min_bpm'],'max_bpm':s['max_bpm']})
    key.checked({'audio':s['reference'],'channel':s['channel']})
    if s['min_bpm']<60 or s['max_bpm']>180:raise ValueError('Initial composition profile requires 60–180 BPM')
    if type(s['bars']) is not int or not 2<=s['bars']<=4 or type(s['seed']) is not int or not 0<=s['seed']<=2**32-1:
        raise ValueError('Use 2–4 bars and bounded seed')
    synth.checked({'midi':'new.mid','voices':voices(s),'peak_dbfs':s['peak_dbfs']})
    return s

def voices(s):
    return [{'timbre':s['lead_timbre'],'gain_db':-6,'pan':0},
        {'timbre':s['backing_timbre'],'gain_db':-15,'pan':-.3},
        {'timbre':'bass','gain_db':-12,'pan':.2}]

def analyse(raw,s):
    _,rate,channels,n=tempo.pcm(raw)
    if n>20*rate:raise ValueError('Use 3–20 seconds of reference audio')
    t=tempo.estimate(raw,{'audio':s['reference'],'min_bpm':s['min_bpm'],'max_bpm':s['max_bpm']})
    k=key.estimate(raw,{'audio':s['reference'],'channel':s['channel']})
    if t['status']!='steady_tempo_estimate' or k['status']!='key_estimate':
        raise ValueError('Reference tempo or key is ambiguous; choose a clearer reference')
    return {'bpm':round(t['tempo_bpm']),'tonic':k['key']['tonic'],'mode':k['key']['mode'],
        'tempo_support':t['support_fraction'],'key_margin':k['score_margin']}

def compose(profile,s):
    checked(s)
    bpm=profile['bpm'];tonic=key.NOTES.index(profile['tonic']);scale=SCALES[profile['mode']]
    if type(bpm) is not int or not s['min_bpm']<=bpm<=s['max_bpm']:raise ValueError('Measured tempo outside reviewed range')
    rng=random.Random(s['seed'])
    lead=[];back=[];bass=[];progression=[]
    # Independent newly selected diatonic progression and melody, not source transcription.
    degrees=[0]+[rng.choice((1,3,4,5)) for _ in range(s['bars']-2)]+[0]
    for i,degree in enumerate(degrees):
        a=i*1920
        triad=[48+tonic+scale[(degree+j)%7]+12*((degree+j)//7) for j in (0,2,4)]
        back.extend([a,1920,p,58] for p in sorted(triad))
        for beat in (0,960):bass.append([a+beat,840,triad[0]-12,78])
        for beat in range(4):
            pitch=rng.choice(triad)+12
            lead.append([a+beat*480,360 if beat%2 else 420,pitch,82+rng.randrange(15)])
        progression.append(degree+1)
    data={'bpm':bpm,'parts':[{'name':'New lead','program':0,'notes':lead},
        {'name':'New harmony','program':48,'notes':back},{'name':'New bass','program':33,'notes':bass}]}
    midi=arrangement.midi(data)
    if arrangement.inspect(midi)!=data:raise ValueError('Reference-conditioned score verification failed')
    settings={'midi':'new.mid','voices':voices(s),'peak_dbfs':s['peak_dbfs']}
    return midi,settings,progression

def generate(raw,s):
    checked(s);profile=analyse(raw,s);midi,settings,progression=compose(profile,s)
    payload,report=synth.render(midi,settings)
    return payload,dict(report,reference_sha256=hashlib.sha256(raw).hexdigest(),reference_profile=profile,
        progression=progression,seed=s['seed'],source_samples_copied=False,source_melody_transcribed=False,
        style_similarity_verified=False,neural_music_generation=False)

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
    _,_,src=validate(root,plan);profile=analyse(guard.exact(src,plan['guards'][1],guard.MAX_INPUT),s)
    return plan,dict(s,reference_profile=profile,scope='New seeded music conditioned only on supported measured tempo and tonal centre, not source melody, samples, arrangement or neural style.')

def execute(root,plan):
    s,dst,src=validate(root,plan);require_storage(dst.parent)
    payload,receipt=generate(guard.exact(src,plan['guards'][1],guard.MAX_INPUT),s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'reference_conditioned_music_pcm_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
