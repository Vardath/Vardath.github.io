"""Native speech acceptance and separate deterministic artifact fixtures."""
import array
import tempfile
import wave
from pathlib import Path
from .local_speech import WindowsSpeech,NoVoice,inspect_audio,narrate

def native_exercise(cancelled=None):
    backend=WindowsSpeech()
    try:
        voices=backend.voices(cancelled)
        english=[v for v in voices if v['culture'].casefold().startswith('en-')]
        if not english:raise NoVoice('No enabled English desktop speech voice; install one in Windows settings')
        with tempfile.TemporaryDirectory(prefix='triad-speech-native-') as folder:
            path=Path(folder)/'spoken.wav'
            info=backend.synthesize('This is a local speech synthesis verification. The voice produces audible narration.',english[0],path,cancelled)
            if info!=inspect_audio(path):raise ValueError('Native speech receipt mismatch')
            return {'status':'passed','detail':f'Actual capped Windows installed speech voice generated {info["duration_seconds"]:.2f}s of non-silent 22050 Hz mono PCM16. Structural/audio energy checks passed; intelligibility not independently reviewed.'}
    except NoVoice as error:
        return {'status':'blocked','detail':str(error)}

def fixture_exercise():
    from .video_planning import binding
    request={'id':9,'project':'fixture-project','chat_id':'fixture-chat','prompt':'/video Create a 30-second English garden video.'}
    scene={'narration':'A flower opens in the morning.','visual':'Garden image','asset_source':'generate','research_needed':[]}
    plan={'schema':'deepthort-video-plan-v1','binding':binding(request),
          'outline':{'title':'Garden','audience':'All','language':'English','style':'Quiet','aspect':'16:9',
                     'target_seconds':30,'scenes':[{'title':'A','intent':'A'},{'title':'B','intent':'B'}]},
          'scripts':[{'scene':1,**scene},{'scene':2,**scene}],
          'status':'reviewed_draft','rendered':False,'assets_acquired':False,'audio_generated':False}
    voice={'id':'fixture','name':'Fixture voice','culture':'en-AU','gender':'Female'}
    def fixture_audio(path,amplitude=1000):
        # Synthetic waveform deliberately used ONLY for structural tests.
        import math,sys
        samples=array.array('h',(int(amplitude*math.sin(i*.2)) for i in range(22050)))
        if sys.byteorder!='little':samples.byteswap()
        with wave.open(str(path),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(22050);w.writeframes(samples.tobytes())
    class Backend:
        def __init__(self):self.calls=[]
        def voices(self,cancelled=None):return [voice]
        def synthesize(self,text,selected,dest,cancelled=None):
            if selected!=voice:raise ValueError('Wrong voice')
            self.calls.append(text)
            fixture_audio(dest);return inspect_audio(dest)
    with tempfile.TemporaryDirectory(prefix='triad-speech-fixture-') as folder:
        root=Path(folder);backend=Backend()
        result,path=narrate(root,request,plan,backend=backend)
        if len(backend.calls)!=2 or result['total_seconds']!=2 or result['rendered'] or result['intelligibility_verified']:
            raise ValueError('Narration timeline or status incorrect')
        result2,path2=narrate(root,request,plan,backend=backend)
        if path2!=path or result2!=result or len(backend.calls)!=2:raise ValueError('Verified narration not resumed')
        try:narrate(root,request,plan,backend=backend,voice_name='Missing voice')
        except NoVoice:pass
        else:raise ValueError('Uninstalled voice selected')
        try:narrate(root,request,plan,backend=backend,cancelled=lambda:True)
        except ValueError:pass
        else:raise ValueError('Cancelled narration proceeded')
        silent=root/'silent.wav';fixture_audio(silent,0)
        try:inspect_audio(silent)
        except ValueError:pass
        else:raise ValueError('Silent waveform accepted')
        fixture_audio(path.parent/'scene-01'/'speech.wav',2000)
        try:narrate(root,request,plan,backend=backend)
        except ValueError:pass
        else:raise ValueError('Changed cached audio accepted')
        return {'status':'passed','detail':'Synthetic fixture validated scene receipts, duration, resumable generation, voice selection, cancellation, silence and stale-audio refusal. Not real speech.'}
