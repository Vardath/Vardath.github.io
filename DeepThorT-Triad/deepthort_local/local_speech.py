"""Offline Windows speech baseline, under the existing shared/nested job.

Uses the bundled fixed System.Speech adapter and installed desktop voices.
No downloads, network calls, generated PowerShell, SSML, or audio playback.
An observed non-silent WAV is structural evidence, not an intelligibility test.
"""
import array
import hashlib
import io
import json
import math
import os
import sys
import tempfile
import time
import wave
from pathlib import Path
from .artifact_media_checks import wav
from .video_planning import canonical,validate_plan
from .reasoning_council import sha

MEMORY_LIMIT=512*1024**2
MAX_WAV=32*1024**2
BACKEND='windows-system-speech-v1'
class NoVoice(ValueError):pass

def check_cancel(cancelled):
    if cancelled and cancelled():raise ValueError('Speech synthesis cancelled or deferred')

def inspect_audio(path):
    path=Path(path)
    if not path.is_file() or path.is_symlink() or not 44<=path.stat().st_size<=MAX_WAV:
        raise ValueError('Missing or oversized narration audio')
    data=path.read_bytes()
    wav(data,max_chunks=128)
    with wave.open(io.BytesIO(data),'rb') as stream:
        rate=stream.getframerate();frames=stream.getnframes()
        if (stream.getnchannels(),stream.getsampwidth(),stream.getcomptype(),rate)!=(1,2,'NONE',22050):
            raise ValueError('Narration must be 22050 Hz mono PCM16')
        duration=frames/rate
        if not .4<=duration<=180:raise ValueError('Narration duration outside supported bounds')
        peak=square=active=seen=0
        while seen<frames:
            samples=array.array('h',stream.readframes(min(8192,frames-seen)))
            if sys.byteorder!='little':samples.byteswap()
            if not samples:raise ValueError('Truncated narration')
            peak=max(peak,max(abs(s) for s in samples))
            square+=sum(s*s for s in samples)
            active+=sum(abs(s)>=100 for s in samples)
            seen+=len(samples)
        rms=math.sqrt(square/seen)
        if peak<250 or rms<30 or active/seen<.005:raise ValueError('Narration is silent or nearly silent')
    return {'sha256':hashlib.sha256(data).hexdigest(),'frames':frames,'sample_rate':rate,
            'channels':1,'bits':16,'duration_seconds':round(duration,6),
            'peak':peak,'rms':round(rms,2),'active_fraction':round(active/seen,6)}

def voice_record(row):
    if not isinstance(row,dict) or set(row)!={'id','name','culture','gender'} or any(
            not isinstance(v,str) or not v.strip() or len(v)>400 or '\x00' in v for v in row.values()):
        raise ValueError('Invalid installed voice metadata')
    return row

def language_code(language):
    value=language.strip().casefold().replace('_','-')
    names={'english':'en','english (australia)':'en-au','australian english':'en-au',
           'english (uk)':'en-gb','british english':'en-gb','english (us)':'en-us','american english':'en-us',
           'french':'fr','german':'de','spanish':'es','italian':'it','portuguese':'pt',
           'japanese':'ja','chinese':'zh','korean':'ko','russian':'ru','dutch':'nl','hindi':'hi'}
    import re
    if value in names:return names[value]
    if re.fullmatch(r'[a-z]{2,3}(?:-[a-z0-9]{2,8})*',value):return value
    raise NoVoice('Unsupported language label; use a matching installed voice and a supported language code in the video brief')

def choose_voice(voices,language,requested=''):
    code=language_code(language)
    matches=[voice_record(v) for v in voices if
        v['culture'].casefold()==code or v['culture'].casefold().startswith(code+'-')]
    if requested:matches=[v for v in matches if v['name']==requested]
    if not matches:raise NoVoice('No enabled installed desktop speech voice matches the requested language/voice')
    if requested and len(matches)!=1:raise NoVoice('Installed voice name is ambiguous')
    return sorted(matches,key=lambda v:(v['culture'].casefold(),v['name'].casefold(),v['id']))[0]

class WindowsSpeech:
    def _run(self,mode,folder,cancelled):
        check_cancel(cancelled)
        if os.name!='nt':raise NoVoice('Windows desktop speech backend requires Windows')
        from .triad_job import verify_root_cap,child_server
        _,available,total=verify_root_cap()
        if available<total//10+MEMORY_LIMIT:raise RuntimeError('Insufficient foreground memory reserve for speech')
        powershell=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
        script=Path(__file__).resolve().parents[1]/'triad_speech.ps1'
        if not powershell.is_file() or not script.is_file():raise NoVoice('Windows speech adapter is unavailable')
        command=[str(powershell),'-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','RemoteSigned',
                 '-File',str(script),'-Mode',mode,'-Folder',str(folder)]
        with child_server(command,folder,folder/'speech.log',memory_limit=MEMORY_LIMIT) as (_,alive):
            deadline=time.monotonic()+(30 if mode=='voices' else 150)
            while alive():
                check_cancel(cancelled)
                if time.monotonic()>=deadline:raise TimeoutError('Local speech synthesis timed out')
                time.sleep(.1)
            if alive.code()!=0:raise RuntimeError('Windows speech adapter failed (exit '+str(alive.code())+')')
        check_cancel(cancelled)
        result=folder/'result.json'
        if not result.is_file() or result.stat().st_size>65536:raise ValueError('Speech adapter response missing or oversized')
        from .structured_source import strict_json
        return strict_json(result.read_text('utf-8'))
    def voices(self,cancelled=None):
        with tempfile.TemporaryDirectory(prefix='triad-voices-') as folder:
            value=self._run('voices',Path(folder),cancelled)
        if not isinstance(value,dict) or set(value)!={'voices'} or not isinstance(value['voices'],list) or len(value['voices'])>128:
            raise ValueError('Invalid voice inventory')
        return [voice_record(v) for v in value['voices']]
    def synthesize(self,text,voice,dest,cancelled=None):
        if not isinstance(text,str) or not text.strip() or len(text)>1000 or '\x00' in text:
            raise ValueError('Invalid bounded narration')
        voice_record(voice)
        with tempfile.TemporaryDirectory(prefix='triad-speak-') as folder:
            folder=Path(folder)
            (folder/'request.json').write_text(canonical({'text':text,'voice':voice}),encoding='utf-8')
            value=self._run('speak',folder,cancelled)
            if value!={'voice':voice}:raise ValueError('Speech voice identity changed')
            audio=folder/'speech.wav'
            info=inspect_audio(audio)
            check_cancel(cancelled)
            # Only the caller-owned fresh staging output is written.
            with Path(dest).open('xb') as out:out.write(audio.read_bytes())
            if inspect_audio(dest)!=info:raise ValueError('Speech output changed during copy')
        return info

def json_read(path):
    from .structured_source import strict_json
    path=Path(path)
    if not path.is_file() or path.is_symlink() or path.stat().st_size>65536:raise ValueError('Narration receipt missing or oversized')
    return strict_json(path.read_text('utf-8'))

def narrate(folder,request,plan,*,voice_name='',backend=None,cancelled=None,stage=None):
    validate_plan(request,plan)
    backend=backend or WindowsSpeech()
    check_cancel(cancelled)
    voice=choose_voice(backend.voices(cancelled),plan['outline']['language'],voice_name)
    identity={'backend':BACKEND,'plan_sha256':sha(canonical(plan)),'binding':plan['binding'],'voice':voice}
    key=sha(canonical(identity))
    folder=Path(folder)/('request-'+str(request['id'])+'-'+key[:20])
    folder.mkdir(parents=True,exist_ok=True)
    if folder.is_symlink():raise ValueError('Narration output folder is a symlink')
    receipts=[]
    for row in plan['scripts']:
        check_cancel(cancelled)
        scene=row['scene'];text=row['narration']
        destination=folder/f'scene-{scene:02d}'
        base={'scene':scene,'identity_sha256':key,'text_sha256':sha(text)}
        if stage:stage(f'Local narration scene {scene}/{len(plan["scripts"])}')
        if destination.exists():
            if destination.is_symlink():raise ValueError('Narration scene folder is a symlink')
            receipt=json_read(destination/'receipt.json')
            if receipt!={**base,'audio':inspect_audio(destination/'speech.wav')}:
                raise ValueError('Saved narration receipt or WAV changed; new draft or repair required')
        else:
            # Publish a fully checked scene directory atomically, never overwrite.
            with tempfile.TemporaryDirectory(prefix='.scene-',dir=folder) as temp:
                prepared=Path(temp)/'complete';prepared.mkdir()
                result=backend.synthesize(text,voice,prepared/'speech.wav',cancelled)
                info=inspect_audio(prepared/'speech.wav')
                if info!=result:raise ValueError('Speech evidence mismatch')
                receipt={**base,'audio':info}
                (prepared/'receipt.json').write_text(canonical(receipt),encoding='utf-8')
                check_cancel(cancelled)
                if destination.exists():raise ValueError('Narration output already exists')
                prepared.rename(destination)
        receipts.append(receipt)
    check_cancel(cancelled)
    total=sum(r['audio']['frames'] for r in receipts)/22050
    manifest={'schema':'deepthort-video-narration-v1','identity':identity,'identity_sha256':key,
              'scenes':receipts,'total_seconds':round(total,6),'target_seconds':plan['outline']['target_seconds'],
              'rendered':False,'intelligibility_verified':False}
    out=folder/'narration.json';payload=canonical(manifest)
    if out.exists():
        if json_read(out)!=manifest:raise ValueError('Narration manifest changed')
    else:
        fd,tmp=tempfile.mkstemp(prefix='.narration-',dir=folder)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(payload);f.flush();os.fsync(f.fileno())
            check_cancel(cancelled)
            os.replace(tmp,out)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    return manifest,out
