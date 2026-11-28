"""Reviewed melody-to-song arrangement from observed monophonic pitches."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import audio_to_midi as transcription
from deepthort_local import musical_arrangement as arrangement
from deepthort_local import instrumental_synthesis as synth
from deepthort_local.disk_gate import require_storage

SCHEMA='deepthortriad-melody-song-v1'
EXTRA=('audio','.wav')
FIELDS={'audio','bpm','min_pitch','max_pitch','gate_dbfs'}
SCALES={'major':(0,2,4,5,7,9,11),'minor':(0,2,3,5,7,8,10)}

def checked(s):
    if not isinstance(s,dict) or set(s)!=FIELDS|{'tonic','mode','repeats','lead_timbre','backing_timbre','peak_dbfs'}:
        raise ValueError('Expected monophonic melody, tempo, explicit key, repeat count and timbres')
    transcription.checked({k:s[k] for k in FIELDS})
    if type(s['tonic']) is not int or not 0<=s['tonic']<=11 or s['mode'] not in SCALES:
        raise ValueError('Choose explicit tonic pitch class 0–11 and major/minor mode')
    if type(s['repeats']) is not int or not 1<=s['repeats']<=3:
        raise ValueError('Choose one to three repetitions')
    synth.checked({'midi':'song.mid','voices':voices(s),'peak_dbfs':s['peak_dbfs']})
    return s

def voices(s):
    return [{'timbre':s['lead_timbre'],'gain_db':-6,'pan':0},
            {'timbre':s['backing_timbre'],'gain_db':-15,'pan':-.35},
            {'timbre':'bass','gain_db':-12,'pan':.15}]

def compose(notes,s):
    checked(s);bpm=s['bpm']
    if not isinstance(notes,list) or not 1<=len(notes)<=128:
        raise ValueError('Use 1–128 observed stable notes')
    transcription.midi(bpm,notes)
    # Whole-beat segment length; preserve every detected note and gap.
    phrase=((max(a+b for a,b,_ in notes)+479)//480)*480
    if phrase*s['repeats']>arrangement.MAX_TICKS or phrase*s['repeats']*60/(480*bpm)>30:
        raise ValueError('Repeated phrase exceeds 30-second render limit')
    scale=SCALES[s['mode']];tonic=s['tonic']
    chords=[]
    for degree in (0,3,4,5,1):
        pitches=[48+tonic+scale[(degree+j)%7]+12*((degree+j)//7) for j in (0,2,4)]
        chords.append((degree,pitches))
    lead=[];back=[];bass=[];decisions=[]
    for repeat in range(s['repeats']):
        offset=repeat*phrase
        lead.extend([offset+a,b,p,90] for a,b,p in notes)
        for a in range(0,phrase,960):
            b=min(a+960,phrase);length=b-a
            # Choose diatonic triad with greatest observed pitch-class overlap.
            # Silence contributes no harmonic evidence; use tonic in empty windows.
            weights={}
            for start,duration,pitch in notes:
                overlap=max(0,min(b,start+duration)-max(a,start))
                if overlap:weights[pitch%12]=weights.get(pitch%12,0)+overlap
            def quality(item):
                degree,pitches=item
                return sum(weights.get(p%12,0) for p in pitches)
            degree,pitches=max(chords,key=quality)
            back.extend([offset+a,length,p,60] for p in sorted(pitches))
            bass.append([offset+a,length,pitches[0]-12,74])
            decisions.append({'start_tick':offset+a,'duration_ticks':length,'degree':degree+1,
                'chord_pitches':pitches,'matched_melody_ticks':quality((degree,pitches)),
                'observed_melody_ticks':sum(weights.values())})
    data={'bpm':bpm,'parts':[{'name':'Observed melody','program':0,'notes':lead},
        {'name':'Diatonic backing','program':48,'notes':back},
        {'name':'Bass','program':33,'notes':bass}]}
    midi=arrangement.midi(data)
    if arrangement.inspect(midi)!=data:raise ValueError('Arrangement MIDI roundtrip failed')
    settings={'midi':'song.mid','voices':voices(s),'peak_dbfs':s['peak_dbfs']}
    synth.schedule(midi,settings)
    return midi,settings,decisions,phrase

def generate(raw,s):
    notes,seconds=transcription.detect(raw,{k:s[k] for k in FIELDS})
    midi,settings,decisions,phrase=compose(notes,s)
    payload,report=synth.render(midi,settings)
    return payload,dict(report,source_audio_sha256=hashlib.sha256(raw).hexdigest(),source_duration_seconds=seconds,
        observed_notes=notes,chords=decisions,phrase_ticks=phrase,repeats=s['repeats'],tonic=s['tonic'],mode=s['mode'],
        arrangement_sha256=hashlib.sha256(midi).hexdigest(),source_audio_copied=False,
        melody_pitch_accuracy_verified=False,neural_song_generation=False,lyrics_generated=False)

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
    _,_,src=validate(root,plan);_,seconds=transcription.input_pcm(guard.exact(src,plan['guards'][1],guard.MAX_INPUT))
    return plan,dict(s,source_duration_seconds=seconds,
        scope='Transcribe stable monophonic notes, retain their timing and pitch, choose explicit-key backing triads and bass, repeat phrase and render synthetic stereo music. No lyrics, general polyphonic transcription or neural quality assurance.')

def execute(root,plan):
    s,dst,src=validate(root,plan);require_storage(dst.parent)
    payload,receipt=generate(guard.exact(src,plan['guards'][1],guard.MAX_INPUT),s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'melody_arranged_song_pcm_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
