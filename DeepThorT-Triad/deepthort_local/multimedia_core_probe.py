"""Read-only fourth-core gap check; legacy weights are not a live specialist."""
from pathlib import Path


def exercise(root, *, cancelled=lambda: False):
    if cancelled():
        return {'status': 'cancelled', 'detail': 'Multimedia check cancelled or deferred for gaming'}
    root = Path(root).resolve()
    from .multimedia_profile import installed
    if installed(root):
        return {'status':'blocked','detail':'Pinned OpenVINO Stable Diffusion INT8 weights have a matching installation receipt and file sizes. Dedicated multimedia service and actual capped inference/concurrency are not yet implemented.'}
    legacy = root / 'models' / 'stable-diffusion-v1-5'
    # Only inspect the existing image engine's fixed model location. No recursive
    # drive scans, weight reads, downloads, model loading or arbitrary execution.
    if any(p.is_symlink() for p in (root / 'models', legacy)):
        return {'status': 'inconclusive', 'detail': 'Legacy image model path is linked; no files inspected. Independent fourth core not verified.'}
    present = legacy.is_dir() and (legacy / 'model_index.json').is_file()
    components = 0
    if present:
        for component in ('unet', 'vae', 'text_encoder'):
            if cancelled():
                return {'status': 'cancelled', 'detail': 'Multimedia check cancelled or deferred for gaming'}
            folder = legacy / component
            if folder.is_symlink() or not folder.is_dir():
                continue
            names = ('diffusion_pytorch_model.safetensors', 'diffusion_pytorch_model.bin',
                     'model.safetensors', 'pytorch_model.bin', 'openvino_model.bin')
            for name in names:
                path = folder / name
                try:
                    if not path.is_symlink() and path.is_file() and path.stat().st_size > 0:
                        components += 1
                        break
                except OSError:
                    continue
    detail = ('Legacy Stable Diffusion index detected; %d/3 expected weight components visible (presence only).' % components
              if present else 'Legacy Stable Diffusion model index not detected at its configured path.')
    return {'status': 'blocked', 'detail': detail + ' Dedicated fourth-core service is not implemented in this release; native generation, concurrent inference and shared-cap verification remain untested.',
            'evidence': {'count': components}}
