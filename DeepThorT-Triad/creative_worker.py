"""Isolated, native fourth AI worker. No cloud inference or model-authored commands."""
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parent))
from deepthort_local.creative_profile import path, installed, REVISION
from deepthort_local.triad_profiles import ROOT,RUNTIME_VERSION


def put(p,obj):
    tmp=p.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj,ensure_ascii=False),encoding='utf-8')
    os.replace(tmp,p)


def main():
    from deepthort_local.triad_job import verify_root_cap
    from deepthort_local.native_offline import disable_openvino_telemetry
    from deepthort_local.win_cpu_cap import suppress_native_error_dialogs
    from importlib.metadata import version
    suppress_native_error_dialogs()
    verify_root_cap()
    disable_openvino_telemetry()
    if len(sys.argv)!=2:raise ValueError('Supervised task folder required')
    folder=Path(sys.argv[1]).resolve(strict=True)
    if folder.parent!=(ROOT/'state'/'creative-tasks').resolve():
        raise ValueError('Unexpected creative task location')
    if not installed():raise RuntimeError('Fourth intelligent checkpoint missing; use Install AI')
    if version('openvino-genai')!=RUNTIME_VERSION:raise RuntimeError('Native runtime version mismatch')
    data=json.loads((folder/'request.json').read_text('utf-8'))
    if set(data)!={'requester','scope','brief','kind','prompt'} or data['kind']!='midi':
        raise ValueError('Unsupported creative task')
    prompt=data['prompt']
    if not isinstance(prompt,str) or not 1<=len(prompt)<=3000:raise ValueError('Creative input too large')
    put(folder/'worker-ready.json',{'pid':os.getpid(),'revision':REVISION})
    deadline=time.monotonic()+120
    while not (folder/'admitted.flag').is_file():
        if time.monotonic()>deadline:raise RuntimeError('Creative worker was not admitted')
        time.sleep(.1)
    import openvino_genai as genai
    pipe=genai.VLMPipeline(str(path()),'CPU',INFERENCE_NUM_THREADS=1,NUM_STREAMS=1)
    history=genai.ChatHistory()
    history.append({'role':'user','content':prompt})
    history.set_extra_context({'enable_thinking':False})
    config=genai.GenerationConfig()
    config.max_new_tokens=512
    config.do_sample=False
    config.num_beams=1
    out=pipe.generate(history,config)
    answer=out.texts[0]
    if not isinstance(answer,str) or not answer.strip() or len(answer)>12000:
        raise ValueError('Invalid native creative response')
    put(folder/'native-result.json',{'pid':os.getpid(),'revision':REVISION,'answer':answer})
    print('Fourth intelligent core: native VLM generation completed',flush=True)


if __name__=='__main__':
    main()
