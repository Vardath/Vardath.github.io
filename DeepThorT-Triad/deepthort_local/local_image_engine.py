"""Opt-in CPU-only offline image generation via a local Diffusers model.

This script never downloads models. The GUI's separate approved installer must first
populate the model folder, then it launches this process under the Windows Job cap.
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from .media_tools import validate_image_prompt


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--prompt',required=True)
    parser.add_argument('--width',type=int,default=384)
    parser.add_argument('--height',type=int,default=384)
    parser.add_argument('--steps',type=int,default=15)
    args=parser.parse_args(argv)
    validate_image_prompt(args.prompt,args.width,args.height,args.steps)
    model=Path(args.model).resolve(strict=True)
    if not (model/'model_index.json').is_file():
        raise RuntimeError('Complete local Diffusers image model not installed')
    out=Path(args.output).resolve()
    out.parent.mkdir(parents=True,exist_ok=True)
    os.environ['HF_HUB_OFFLINE']='1'
    os.environ['TRANSFORMERS_OFFLINE']='1'
    os.environ['DIFFUSERS_OFFLINE']='1'
    os.environ['OMP_NUM_THREADS']='1'
    os.environ['MKL_NUM_THREADS']='1'
    try:
        import torch
        from diffusers import StableDiffusionPipeline
    except ImportError as e:
        raise RuntimeError('The optional PyTorch CPU + diffusers image engine is not installed. Use Install Image Engine in DeepThorT.') from e
    torch.set_num_threads(1)
    print('Loading local image diffusion model on CPU...',flush=True)
    pipe=StableDiffusionPipeline.from_pretrained(str(model),local_files_only=True,
                   safety_checker=None,requires_safety_checker=False,torch_dtype=torch.float32)
    pipe=pipe.to('cpu')
    pipe.enable_attention_slicing('max')
    print('Generating image on CPU (may be very slow under the 20% cap)...',flush=True)
    image=pipe(prompt=args.prompt,num_inference_steps=args.steps,
               height=args.height,width=args.width).images[0]
    temp=out.with_suffix('.partial.png')
    image.save(str(temp))
    os.replace(temp,out)
    print('IMAGE_SAVED: '+str(out),flush=True)
    return 0


if __name__=='__main__':sys.exit(main())
