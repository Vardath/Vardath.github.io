"""Read-only fourth-core gap check; legacy weights are not a live specialist."""
from pathlib import Path


def exercise(root, *, cancelled=lambda: False, health=None, expected_pid=None, notify=lambda message:None):
    if cancelled():
        return {'status': 'cancelled', 'detail': 'Multimedia check cancelled or deferred for gaming'}
    root = Path(root).resolve()
    from .creative_profile import installed as creative_installed
    if creative_installed(root):
        if health is None:
            return {'status':'inconclusive','detail':'Fourth intelligent checkpoint installed; native supervised task not exercised.'}
        from .creative_core import create_midi
        from .triad_acceptance import resident_roles
        try:
            initial=health()
            before=resident_roles(initial,expected_pid)
            if any(m.get('busy') for m in before.values()):
                return {'status':'inconclusive','detail':'Existing language worker busy; creative acceptance deferred'}
            brief='Produce MIDI at exactly 100 BPM: four quarter notes, MIDI pitches 60, 62, 64, 65 in this order. No additional notes.'
            expected={'bpm':100,'notes':[[60,480],[62,480],[64,480],[65,480]]}
            folder,receipt=create_midi(requester='acceptance',scope='fourth-core-native',
                brief=brief,cancelled=cancelled,notify=notify,root=root,accept=lambda s:s==expected)
            final=health()
            after=resident_roles(final,expected_pid)
            if ({k:v['pid'] for k,v in before.items()}!={k:v['pid'] for k,v in after.items()}
                    or receipt['pid'] in [expected_pid,*[m['pid'] for m in before.values()]]
                    or final.get('serial_memory_mode') or final.get('memory_retries')!=initial.get('memory_retries')):
                return {'status':'failed','detail':'Fourth model completed but existing language worker continuity or memory policy failed'}
            return {'status':'passed','detail':'Actual independent Gemma native generation created exact four-note MIDI under protected shared cap; original three language workers remained resident. Simultaneous language inference, creative quality and other modalities not yet validated.',
                    'evidence':{'artifact_sha256':receipt['sha256'],'pid':receipt['pid']}}
        except (OSError,RuntimeError,ValueError,KeyError,TypeError) as error:
            return {'status':'cancelled' if cancelled() else 'blocked' if isinstance(error,(OSError,RuntimeError)) else 'failed',
                    'detail':'Fourth intelligent model task: '+str(error)[:350]}
    from .multimedia_profile import installed
    if installed(root):
        return {'status':'blocked','detail':'Pinned OpenVINO Stable Diffusion INT8 weights have a matching installation receipt and file sizes. Fourth intelligent Gemma model not installed. Click Install AI; Stable Diffusion is only a production tool.'}
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
    return {'status': 'blocked', 'detail': detail + ' Fourth intelligent Gemma model not installed; click Install AI. Native task and concurrency remain untested.',
            'evidence': {'count': components}}
