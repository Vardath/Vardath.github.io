"""Local offline model setup diagnostics; does not invoke inference or any network service."""
from __future__ import annotations
from pathlib import Path
from shutil import which

MODEL_RELPATH = Path('models/onnx-community/Qwen2.5-Coder-1.5B-Instruct/onnx/model_q4.onnx')
MIN_MODEL_BYTES = 1_700_000_000


def inspect_local_setup(root: Path, *, node_path: str | None = None) -> dict:
    root = Path(root)
    model = root / MODEL_RELPATH
    size = model.stat().st_size if model.is_file() else 0
    node = which('node') if node_path is None else node_path
    components = {
        'node': bool(node),
        'transformers': (root / 'node_modules/@huggingface/transformers').is_dir(),
        'model': size >= MIN_MODEL_BYTES,
        'server': (root / 'inference_server.mjs').is_file(),
    }
    issues = []
    if not components['node']:
        issues.append('Node.js was not found on PATH. Install Node.js LTS, then restart DeepThorT.')
    if not components['transformers']:
        issues.append('ONNX runtime dependencies are missing. Click Install AI and approve the installation.')
    if not components['model']:
        issues.append('The local Qwen ONNX model is missing or incomplete. Click Install AI to download it.')
    if not components['server']:
        issues.append('The inference server program is missing. Extract the complete DeepThorT update ZIP.')
    return {'ready_to_launch': all(components.values()), 'components': components,
            'issues': issues, 'model_size_bytes': size, 'model_path': str(model), 'node_path': node or ''}


def format_diagnostic(info: dict, *, model_running: bool, model_ready: bool,
                      model_loading: bool, queued: int, recent_logs: list[str] | None = None, loading_seconds: int = 0) -> str:
    if model_ready and model_running:
        condition = 'AI is responding on the supervised local server.'
    elif model_loading and model_running:
        condition = 'AI process started; local ONNX weights are loading. This can be slow at a 35% CPU limit.'
    elif model_running:
        condition = 'AI process is running but has not passed its local health check.'
    else:
        condition = 'AI process is NOT RUNNING. Chat messages cannot receive replies yet.'
    lines = ['LOCAL COMPUTER DIAGNOSTIC (not a generated AI response)', '', condition,
             f'Waiting chat/jobs: {queued}',
             f'Node.js: {"available" if info["components"]["node"] else "missing"}',
             f'ONNX runtime dependencies: {"available" if info["components"]["transformers"] else "missing"}',
             f'Model weights: {info["model_size_bytes"] / 1e9:.2f} GB / 1.70 GB minimum',
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
    lines += ['', 'System resource protection: 35% CPU hard cap and 35% committed-memory job limit are configured by the launcher.',
              'Actual Windows enforcement and gaming performance still require testing on this PC.']
    return '\n'.join(lines)
