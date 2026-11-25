"""Fixed offline video renderer for reviewed, locally acquired scene assets.

No model-generated commands, network inputs, silent installation or publication.
The native runner uses Triad's inherited Windows job and nested cleanup cap.
"""
import hashlib
import json
import math
import os
import re
import shutil
import tempfile
import time
import wave
import array
import sys
from pathlib import Path
from .video_planning import canonical,validate_plan
from .video_visuals import root_for,read_scene,inspect
from .local_speech import inspect_audio,json_read,BACKEND,voice_record
from .reasoning_council import sha

FPS=24
RATE=22050
DIMENSIONS={'16:9':(1920,1080),'9:16':(1080,1920),'1:1':(1080,1080)}
MAX_SECONDS=600
MAX_FILE=512*1024**2
MEMORY=512*1024**2

class MissingTools(ValueError):pass

def stop(cancelled):
    if cancelled and cancelled():raise ValueError('Video rendering cancelled or deferred')

def file_hash(path,limit=MAX_FILE):
    path=Path(path)
    if not path.is_file() or path.is_symlink() or not 0<path.stat().st_size<=limit:
        raise ValueError('Render input or output missing or oversized')
    before=path.stat();h=hashlib.sha256();size=0
    with path.open('rb') as f:
        while block:=f.read(1024*1024):
            size+=len(block)
            if size>limit:raise ValueError('Video file exceeds bound')
            h.update(block)
    after=path.stat()
    if size!=before.st_size or (after.st_size,after.st_mtime_ns)!=(before.st_size,before.st_mtime_ns):
        raise ValueError('File changed while hashing')
    return h.hexdigest()

def tools():
    from .video_tools import find_pair
    found=find_pair()
    if not found:raise MissingTools('FFmpeg and FFprobe not found in PATH or known WinGet package folders. Install the reviewed FFmpeg package, then retry.')
    return found

def native_runner(command,folder,cancelled=None,seconds=120):
    from .triad_job import verify_root_cap,child_server
    _,available,total=verify_root_cap()
    if available<total//10+MEMORY:raise RuntimeError('Insufficient foreground memory reserve for rendering')
    stop(cancelled)
    log=Path(folder)/'ffmpeg.log'
    with child_server(command,folder,log,memory_limit=MEMORY) as (_,alive):
        deadline=time.monotonic()+seconds
        while alive():
            stop(cancelled)
            if time.monotonic()>=deadline:raise TimeoutError('Video operation timed out; cleanup job closed')
            if log.exists() and log.stat().st_size>1024*1024:raise ValueError('Video process log exceeded bound')
            time.sleep(.15)
        if alive.code()!=0:raise ValueError('Video tool exited '+str(alive.code())+'; check installed FFmpeg codec support')
    stop(cancelled)
    if log.stat().st_size>1024*1024:raise ValueError('Video process log exceeded bound')
    return log.read_text('utf-8',errors='replace')

def load_inputs(audio_root,visual_root,request,plan):
    validate_plan(request,plan)
    digest=sha(canonical(plan))
    audio_root=Path(audio_root)
    manifest=json_read(audio_root/'narration.json')
    identity=manifest['identity']
    if (manifest.get('schema')!='deepthort-video-narration-v1' or identity.get('backend')!=BACKEND
            or identity.get('plan_sha256')!=digest or identity.get('binding')!=plan['binding']
            or manifest.get('identity_sha256')!=sha(canonical(identity))
            or len(manifest.get('scenes',[]))!=len(plan['scripts'])):
        raise ValueError('Narration does not belong to reviewed video plan')
    voice_record(identity['voice'])
    root,_=root_for(visual_root,request,plan)
    rows=[];samples=frames=0
    for row,saved in zip(plan['scripts'],manifest['scenes']):
        n=row['scene'];audio=audio_root/f'scene-{n:02d}'/'speech.wav'
        if audio.parent.is_symlink():raise ValueError('Narration directory is a symlink')
        receipt={'scene':n,'identity_sha256':manifest['identity_sha256'],'text_sha256':sha(row['narration']),'audio':inspect_audio(audio)}
        if receipt!=saved or receipt!=json_read(audio.parent/'receipt.json'):
            raise ValueError('Narration receipt changed')
        visual=read_scene(root,digest,n)
        if visual is None:raise ValueError('Missing scene image '+str(n))
        end=samples+receipt['audio']['frames']
        end_frame=(end*FPS+RATE-1)//RATE
        rows.append({'scene':n,'start_sample':samples,'end_sample':end,'start_frame':frames,'end_frame':end_frame,
                     'audio_path':audio,'image_path':root/f'scene-{n:02d}'/'image.png',
                     'audio':receipt['audio'],'visual':visual,'narration':row['narration']})
        samples=end;frames=end_frame
    if not 0<samples<=MAX_SECONDS*RATE or abs(manifest['total_seconds']-samples/RATE)>1e-5:
        raise ValueError('Narration total changed or exceeds 600 second render bound')
    return rows,identity

def stamp(ms):
    hours,ms=divmod(ms,3600000);minutes,ms=divmod(ms,60000);seconds,ms=divmod(ms,1000)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}'

def captions(rows):
    import textwrap
    lines=[];i=0
    for row in rows:
        # Approximate cue timing within exact measured scene boundaries.
        # This is not forced word alignment.
        parts=textwrap.wrap(' '.join(row['narration'].split()),width=72,break_long_words=True,break_on_hyphens=False)
        if not parts:raise ValueError('Missing caption text')
        start=row['start_sample']*1000//RATE;end=row['end_sample']*1000//RATE
        if end-start<len(parts):raise ValueError('Insufficient duration for captions')
        weights=[max(1,len(x)) for x in parts];total=sum(weights);used=0
        for p,w in zip(parts,weights):
            a=start+(end-start)*used//total;used+=w
            b=start+(end-start)*used//total
            if b<=a:raise ValueError('Invalid subtitle interval')
            i+=1;lines.extend([str(i),stamp(a)+' --> '+stamp(b),p.replace('-->','—>'),''])
    return '\n'.join(lines)+'\n'

def scene_command(exe,n,width,height,count):
    return [exe,'-hide_banner','-loglevel','error','-nostdin','-n','-filter_threads','1',
            '-protocol_whitelist','file','-loop','1','-framerate',str(FPS),'-i',f'image-{n:02d}.png',
            '-frames:v',str(count),'-vf',f'scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1',
            '-an','-c:v','libx264','-preset','ultrafast','-crf','22','-pix_fmt','yuv420p','-threads','2',
            '-map_metadata','-1',f'clip-{n:02d}.mp4']

def probe_video(exes,folder,width,height,samples,frames,runner,cancelled):
    ffmpeg,ffprobe=exes
    raw=runner([ffprobe,'-v','error','-protocol_whitelist','file','-count_frames','-show_streams','-show_format','-of','json','video.mp4'],folder,cancelled,180)
    data=json.loads(raw)
    streams=data['streams']
    if len(streams)!=2:raise ValueError('Expected exactly one video and one audio stream')
    v=next((s for s in streams if s['codec_type']=='video'),{})
    a=next((s for s in streams if s['codec_type']=='audio'),{})
    if (v.get('codec_name')!='h264' or v.get('pix_fmt')!='yuv420p' or (v.get('width'),v.get('height'))!=(width,height)
        or v.get('avg_frame_rate')!=f'{FPS}/1' or int(v.get('nb_read_frames',-1))!=frames
        or a.get('codec_name')!='aac' or a.get('channels')!=1):
        raise ValueError('Rendered stream format or frame count mismatch')
    duration=float(data['format']['duration']);ad=float(a['duration']);vd=float(v['duration'])
    if not all(math.isfinite(x) for x in (duration,ad,vd)) or abs(ad-samples/RATE)>.15 or abs(vd-frames/FPS)>.08 or abs(duration-max(ad,vd))>.15:
        raise ValueError('Rendered duration or A/V synchronization mismatch')
    runner([ffmpeg,'-hide_banner','-loglevel','error','-xerror','-nostdin','-protocol_whitelist','file',
            '-threads','2','-i','video.mp4','-map','0:v','-map','0:a','-f','null','-'],folder,cancelled,300)
    runner([ffmpeg,'-hide_banner','-loglevel','error','-xerror','-nostdin','-n','-protocol_whitelist','file',
            '-i','video.mp4','-map','0:a','-ac','1','-ar',str(RATE),'-c:a','pcm_s16le','decoded.wav'],folder,cancelled,120)
    with wave.open(str(folder/'decoded.wav'),'rb') as w:
        count=w.getnframes();active=0;seen=0
        if (w.getnchannels(),w.getsampwidth(),w.getframerate())!=(1,2,RATE) or abs(count-samples)>RATE*.15:
            raise ValueError('Decoded audio sample count mismatch')
        while block:=w.readframes(8192):
            values=array.array('h',block)
            if sys.byteorder!='little':values.byteswap()
            active+=sum(abs(x)>=100 for x in values);seen+=len(values)
        if not seen or active/seen<.005:raise ValueError('Rendered audio nearly silent')
    (folder/'decoded.wav').unlink()
    return {'width':width,'height':height,'fps':FPS,'frames':frames,'duration_seconds':duration,
            'audio_seconds':ad,'video_seconds':vd,'audio_active_fraction':round(active/seen,6),'full_decode':True,
            'sha256':file_hash(folder/'video.mp4')}

def render(folder,request,plan,audio_root,visual_root,*,exes=None,runner=None,cancelled=None,stage=None):
    stop(cancelled)
    exes=exes or tools();runner=runner or native_runner
    rows,voice=load_inputs(audio_root,visual_root,request,plan)
    width,height=DIMENSIONS[plan['outline']['aspect']]
    timeline=[{k:v for k,v in r.items() if k not in ('audio_path','image_path')} for r in rows]
    identity={'schema':'deepthort-video-render-v1','plan_sha256':sha(canonical(plan)),'voice':voice,
              'timeline':timeline,'width':width,'height':height,'fps':FPS,
              'tools':[{'name':Path(x).name,'sha256':file_hash(x)} for x in exes]}
    key=sha(canonical(identity))
    root=Path(folder);root.mkdir(parents=True,exist_ok=True)
    dest=root/('request-'+str(request['id'])+'-'+key[:20])
    if dest.exists():
        if dest.is_symlink():raise ValueError('Output directory is a symlink')
        saved=json_read(dest/'render.json')
        if (saved.get('identity_sha256')!=key or saved.get('identity')!=identity or saved.get('verification',{}).get('sha256')!=file_hash(dest/'video.mp4')
            or saved.get('subtitles_sha256')!=file_hash(dest/'captions.srt') or saved.get('credits_sha256')!=file_hash(dest/'credits.json')):
            raise ValueError('Existing render changed; new output or repair required')
        return saved,dest
    with tempfile.TemporaryDirectory(prefix='.render-',dir=root) as temp:
        work=Path(temp)
        complete=work/'complete';complete.mkdir()
        ffmpeg,ffprobe=exes
        with wave.open(str(work/'narration.wav'),'wb') as joined:
            joined.setnchannels(1);joined.setsampwidth(2);joined.setframerate(RATE)
            for row in rows:
                stop(cancelled)
                n=row['scene'];count=row['end_frame']-row['start_frame']
                if stage:stage(f'Render video scene {n}/{len(rows)}')
                image=work/f'image-{n:02d}.png'
                shutil.copyfile(row['image_path'],image)
                if inspect(image)!=row['visual']['image']:raise ValueError('Scene image changed')
                audio=work/f'audio-{n:02d}.wav';shutil.copyfile(row['audio_path'],audio)
                if inspect_audio(audio)!=row['audio']:raise ValueError('Scene narration changed')
                with wave.open(str(audio),'rb') as part:
                    while block:=part.readframes(8192):joined.writeframesraw(block)
                runner(scene_command(ffmpeg,n,width,height,count),work,cancelled,300)
                file_hash(work/f'clip-{n:02d}.mp4')
        (work/'clips.txt').write_text(''.join(f"file 'clip-{r['scene']:02d}.mp4'\n" for r in rows),encoding='ascii')
        if stage:stage('Mux measured narration and scene video')
        runner([ffmpeg,'-hide_banner','-loglevel','error','-nostdin','-n','-protocol_whitelist','file',
                '-f','concat','-safe','1','-i','clips.txt','-protocol_whitelist','file','-i','narration.wav',
                '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','128k','-movflags','+faststart',
                '-map_metadata','-1','video.mp4'],work,cancelled,180)
        verified=probe_video(exes,work,width,height,rows[-1]['end_sample'],rows[-1]['end_frame'],runner,cancelled)
        (complete/'captions.srt').write_text(captions(rows),encoding='utf-8')
        (complete/'credits.json').write_text(canonical({'sources':[r['visual']['source'] for r in rows],
            'voice':voice['voice'],'publication_rights_verified':False,'research_needed':[r['research_needed'] for r in plan['scripts']]}),encoding='utf-8')
        shutil.move(str(work/'video.mp4'),str(complete/'video.mp4'))
        result={'identity':identity,'identity_sha256':key,'verification':verified,
                'subtitles_sha256':file_hash(complete/'captions.srt'),'credits_sha256':file_hash(complete/'credits.json'),
                'publication_rights_verified':False,'creative_quality_verified':False,'captions_word_aligned':False}
        (complete/'render.json').write_text(canonical(result),encoding='utf-8')
        if any(file_hash(x)!=item['sha256'] for x,item in zip(exes,identity['tools'])):raise ValueError('Renderer executable changed')
        stop(cancelled)
        if dest.exists():raise ValueError('Render output appeared during operation')
        complete.rename(dest)
    return result,dest
