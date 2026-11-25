"""Real FFmpeg render fixture and native Windows acceptance.
Fixture images are synthetic; native test uses the real installed speech voice.
"""
import array
import math
import sys
import tempfile
import wave
from pathlib import Path
from .visual_probe import scenario,fixture_png
from .video_visuals import assign,inspect,normalize
from .local_speech import narrate,inspect_audio,WindowsSpeech,NoVoice
from .video_render import render,tools,MissingTools,captions,RATE

def fixture_runner(argv,folder,cancelled=None,seconds=120):
    # Only CI/test on non-Windows. Production never uses this runner.
    import os,subprocess
    if os.name=='nt':raise RuntimeError('Windows requires native capped runner')
    result=subprocess.run(argv,cwd=folder,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,timeout=seconds,check=True)
    return result.stdout.decode('utf-8')

class FixtureVoice:
    voice={'id':'fixture','name':'Fixture','culture':'en-AU','gender':'Female'}
    def voices(self,cancelled=None):return [self.voice]
    def synthesize(self,text,voice,dest,cancelled=None):
        # Deliberately synthetic PCM, not claimed to be intelligible speech.
        samples=array.array('h',(int(1500*math.sin(i*.1)) for i in range(11053)))
        if sys.byteorder!='little':samples.byteswap()
        with wave.open(str(dest),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(samples.tobytes())
        return inspect_audio(dest)

def exercise(native=False,cancelled=None):
    exes=tools()
    request,plan=scenario()
    plan['scripts']=plan['scripts'][:2];plan['outline']['scenes']=plan['outline']['scenes'][:2]
    plan['scripts'][1]['narration']='The garden grows.'
    with tempfile.TemporaryDirectory(prefix='triad-render-fixture-') as temp:
        root=Path(temp);image=root/'source.png';image.write_bytes(fixture_png())
        def decoder(data,dest,cancel=None):
            if native:return normalize(data,dest,cancel)
            dest.write_bytes(data);return inspect(dest)
        _,audio_manifest=narrate(root/'audio',request,plan,backend=WindowsSpeech() if native else FixtureVoice(),cancelled=cancelled)
        for n in (1,2):assign(root/'visuals',request,plan,n,'provided',provided=image,normalizer=decoder,cancelled=cancelled)
        kw={'exes':exes,'cancelled':cancelled}
        if not native:kw['runner']=fixture_runner
        result,folder=render(root/'renders',request,plan,audio_manifest.parent,root/'visuals',**kw)
        v=result['verification']
        if (not v['full_decode'] or v['width']!=1920 or v['height']!=1080 or v['fps']!=24
                or v['audio_active_fraction']<=0 or result['publication_rights_verified']
                or result['creative_quality_verified'] or result['captions_word_aligned']):
            raise ValueError('Invalid render verification')
        if 'A flower opens.' not in (folder/'captions.srt').read_text('utf-8') or 'The garden grows.' not in (folder/'captions.srt').read_text('utf-8'):
            raise ValueError('Caption text lost')
        again,path=render(root/'renders',request,plan,audio_manifest.parent,root/'visuals',**kw)
        if path!=folder or again!=result:raise ValueError('Verified render could not resume')
        (folder/'captions.srt').write_text('changed',encoding='utf-8')
        try:render(root/'renders',request,plan,audio_manifest.parent,root/'visuals',**kw)
        except ValueError:pass
        else:raise ValueError('Altered output was accepted')
        # Revalidate input even when an earlier result exists.
        (audio_manifest.parent/'scene-01'/'speech.wav').write_bytes(b'changed')
        try:render(root/'new-renders',request,plan,audio_manifest.parent,root/'visuals',**kw)
        except ValueError:pass
        else:raise ValueError('Altered narration accepted')
        return {'status':'passed','detail':f'Actual {"capped Windows speech and" if native else "fixture PCM and"} FFmpeg H.264/AAC MP4: {v["width"]}x{v["height"]}, {v["frames"]} decoded frames, {v["duration_seconds"]:.2f}s, non-silent decoded audio, captions, credits, resume and changed-input/output refusal. No creative quality or rights review.'}

def native_exercise(cancelled=None):
    try:return exercise(native=True,cancelled=cancelled)
    except (MissingTools,NoVoice) as error:return {'status':'blocked','detail':str(error)}
