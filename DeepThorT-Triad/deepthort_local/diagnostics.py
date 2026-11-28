"""Triad setup diagnostics; read only."""
from pathlib import Path
from .triad_profiles import PROFILES,MODEL_SET_DIR,model_path,runtime_path,ready,total_weights
MODEL_RELPATH=Path('models')/MODEL_SET_DIR/'implementation'/'openvino_model.bin'
MIN_MODEL_BYTES=PROFILES['implementation'][3]
def inspect_local_setup(root:Path,*,node_path=None):
    root=Path(root)
    size=sum((model_path(r,root)/'openvino_model.bin').stat().st_size for r in PROFILES if (model_path(r,root)/'openvino_model.bin').is_file())
    components={'node':True,'transformers':runtime_path(root).is_file(),'model':ready(root),'server':(root/'triad_server.py').is_file()}
    return {'ready_to_launch':all(components.values()),'components':components,
            'issues':[] if all(components.values()) else ['Install all three verified OpenVINO IR files and the pinned CPU runtime.'],
            'model_size_bytes':size,'model_path':str(root/'models'/MODEL_SET_DIR),'node_path':'Python broker'}
def format_diagnostic(info: dict, *, model_running: bool, model_ready: bool,
                      model_loading: bool, queued: int, recent_logs: list[str] | None = None, loading_seconds: int = 0) -> str:
    if model_ready and model_running:
        condition = 'AI is responding on the supervised local server.'
    elif model_loading and model_running:
        condition = 'AI process started; local OpenVINO IR weights are loading. This can be slow under automatic resource limits.'
    elif model_running:
        condition = 'AI process is running but has not passed its local health check.'
    else:
        condition = 'AI process is NOT RUNNING. Chat messages cannot receive replies yet.'
    lines = ['LOCAL COMPUTER DIAGNOSTIC (not a generated AI response)', '', condition,
             f'Waiting chat/jobs: {queued}',
             f'Python broker: {"available" if info["components"]["node"] else "missing"}',
             f'Triad CPU runtime: {"available" if info["components"]["transformers"] else "missing"}',
             f'Model weights: {info["model_size_bytes"] / 1e9:.2f} GB / three native IR model directories',
             f'Inference script: {"available" if info["components"]["server"] else "missing"}', '']
    if model_loading and model_running:
        elapsed=max(0,int(loading_seconds))
        lines += [f'Model loading elapsed: {elapsed//60}m {elapsed%60:02d}s',
                  'Model initialization has no verified percentage. A running process alone is not proof of progress.']
    if info['issues']:
        lines.append('TO FIX:')
        lines.extend('- ' + x for x in info['issues'])
    elif not model_running:
        lines.append('TO FIX: Click Start AI. If it stops, inspect the error dialog and Processes tab.')
    elif model_loading:
        lines.append('TO FIX: Wait for the model-ready status; if startup fails, inspect the error dialog and Processes log.')
    else:
        lines.append('The local model is ready to process chat. If a job remains queued, inspect Work queue.')
    if recent_logs and not model_ready:
        lines += ['', 'RECENT MODEL OUTPUT:']
        lines += [line[:300] for line in recent_logs[-8:]]
    lines += ['', 'System resource protection: automatic Medium 50% / High 85% CPU hard cap, up to 80% RAM-sized root commit; Medium uses a 65% cooperative admission budget, not forced eviction.',
              'Actual Windows enforcement and gaming performance still require testing on this PC.']
    return '\n'.join(lines)
