"""Opt-in setup of a single local SD1.5 CPU image model. No generation or cloud API."""
import os
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODEL=ROOT/'models'/'stable-diffusion-v1-5'
os.environ['HF_HOME']=str(ROOT/'cache'/'huggingface')
# Never activate without an explicit GUI confirmation beforehand.
print('Installing CPU image inference dependencies...',flush=True)
subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check','--no-input',
                'diffusers>=0.34,<0.39','transformers>=4.45,<5','safetensors>=0.4',
                'huggingface_hub>=0.28,<2','accelerate>=1,<2','Pillow>=10'],check=True,
               creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name=='nt' else 0)
try:import torch
except ImportError:
    subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check','--no-input',
                    'torch','--index-url','https://download.pytorch.org/whl/cpu'],check=True,
                   creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name=='nt' else 0)
from huggingface_hub import snapshot_download
print('Downloading the Stable Diffusion 1.5 image model (several GB)...',flush=True)
snapshot_download('stable-diffusion-v1-5/stable-diffusion-v1-5',local_dir=str(MODEL),
                  allow_patterns=['model_index.json','scheduler/*','tokenizer/*','text_encoder/*',
                                  'unet/*','vae/*','feature_extractor/*'],
                  ignore_patterns=['*.bin','*.ckpt','*.msgpack','*.onnx','*.h5','*.pth'])
if not (MODEL/'model_index.json').is_file():raise RuntimeError('Image model incomplete')
print('Local image model is installed. Generation will be offline and CPU-only.',flush=True)
