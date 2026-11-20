"""Independent, resumable base-language training for ModernScratchTransformer.

Must use real, properly sourced corpus data to gain language capability.
All model weights start random. This is never a pretrained-model wrapper.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import random

import torch
from torch.nn import functional as F
from capability.bpe import ByteBPE
from capability.modern_model import ModernConfig, ModernScratchTransformer
from capability.pretrain import atomic_save, draw_batch, eval_loss, file_hash, load_tokens, lr_at

FORMAT='vardath-modern-pretrain-v05'


def train(*, corpus:Path, tokenizer_path:Path, output:Path, steps:int=500,
          width:int=256, layers:int=8, heads:int=8, context_size:int=2048,
          seq_len:int=256, batch:int=2, grad_accum:int=4, lr:float=3e-4,
          seed:int=2026, threads:int=2, save_every:int=100, eval_every:int=100,
          min_train_tokens:int=1_000_000, resume:bool=False, quiet:bool=False):
    if steps<1 or seq_len<1 or seq_len>context_size or batch<1 or grad_accum<1 or lr<=0:
        raise ValueError('Invalid training parameters')
    if threads<1 or save_every<1 or eval_every<1 or min_train_tokens<0:
        raise ValueError('Invalid training controls')
    torch.set_num_threads(threads)
    torch.use_deterministic_algorithms(True)
    tok=ByteBPE.load(tokenizer_path)
    train_ids, tr_stat=load_tokens(corpus/'train.jsonl',tok)
    valid_ids, vl_stat=load_tokens(corpus/'validation.jsonl',tok)
    if len(train_ids)<max(seq_len+1,min_train_tokens) or len(valid_ids)<2:
        raise ValueError(f'Corpus is inadequate: {len(train_ids)} train tokens, {len(valid_ids)} validation tokens. '
                         f'Required at least {max(seq_len+1,min_train_tokens)} training tokens.')
    cfg=ModernConfig(vocab_size=tok.vocab_size,context_size=context_size,
                     width=width,layers=layers,heads=heads)
    immutable={'corpus_hash':file_hash(corpus/'train.jsonl'),
               'validation_hash':file_hash(corpus/'validation.jsonl'),
               'tokenizer_hash':file_hash(tokenizer_path),
               'seq_len':seq_len,'batch':batch,'grad_accum':grad_accum,'lr':lr,'seed':seed}
    if resume and not output.exists():
        raise FileNotFoundError('Cannot resume without checkpoint')
    if output.exists() and not resume:
        raise FileExistsError('Checkpoint exists; use resume or new path')
    random.seed(seed)
    torch.manual_seed(seed)
    sampler=torch.Generator(device='cpu').manual_seed(seed+10)
    model=ModernScratchTransformer(cfg)
    optimizer=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=0.01)
    start=0
    if resume:
        state=torch.load(output,map_location='cpu',weights_only=True)
        if (state.get('format')!=FORMAT or state.get('config')!=asdict(cfg)
            or state.get('immutable')!=immutable):
            raise ValueError('Checkpoint data, tokenizer or hyperparameters do not match')
        model.load_state_dict(state['model_state'])
        optimizer.load_state_dict(state['optimizer_state'])
        sampler.set_state(state['sampler_state'])
        torch.set_rng_state(state['torch_rng_state'])
        start=int(state['step'])
    if steps<=start: raise ValueError('Target steps must exceed restored step')
    metrics={'baseline_validation':eval_loss(model,valid_ids,seq_len=seq_len,device=torch.device('cpu'),max_eval_tokens=2048)}
    def save(step):
        atomic_save({'format':FORMAT,'config':asdict(cfg),'immutable':immutable,'step':step,
                     'model_state':model.state_dict(),'optimizer_state':optimizer.state_dict(),
                     'sampler_state':sampler.get_state(),'torch_rng_state':torch.get_rng_state(),
                     'metrics':metrics,'origin':'random initialization; no pretrained weights'},output)
    for step in range(start+1,steps+1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        loss_sum=0.0
        for _ in range(grad_accum):
            x,y=draw_batch(train_ids,batch=batch,seq_len=seq_len,generator=sampler,device=torch.device('cpu'))
            logits=model(x)
            loss=F.cross_entropy(logits.flatten(0,1),y.flatten())
            (loss/grad_accum).backward()
            loss_sum+=float(loss.detach())/grad_accum
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
        optimizer.step()
        metrics['step']=step
        metrics['train_loss']=round(loss_sum,6)
        if step%eval_every==0 or step==steps:
            metrics['validation']=eval_loss(model,valid_ids,seq_len=seq_len,device=torch.device('cpu'),max_eval_tokens=2048)
            if not quiet:
                print('step',step,'training',metrics['train_loss'],'held-out',metrics['validation']['loss'],flush=True)
        if step%save_every==0 or step==steps:
            save(step)
    return {'checkpoint':str(output),'steps':steps,'parameters':model.parameter_count,
            'train_tokens':len(train_ids),'validation_tokens':len(valid_ids),'metrics':metrics}


def evaluate(*,checkpoint:Path,tokenizer_path:Path,corpus:Path):
    tok=ByteBPE.load(tokenizer_path)
    state=torch.load(checkpoint,map_location='cpu',weights_only=True)
    if state.get('format')!=FORMAT or state['immutable']['tokenizer_hash']!=file_hash(tokenizer_path):
        raise ValueError('Incompatible model or tokenizer')
    cfg=ModernConfig(**state['config'])
    model=ModernScratchTransformer(cfg).eval()
    model.load_state_dict(state['model_state'])
    results={}
    for split in ('validation','test'):
        ids,_=load_tokens(corpus/f'{split}.jsonl',tok)
        results[split]=eval_loss(model,ids,seq_len=min(256,cfg.context_size),device=torch.device('cpu'))
    return {'checkpoint_step':state['step'],'parameters':model.parameter_count,'results':results}


def main():
    p=argparse.ArgumentParser(description='Train modern scratch model from zero weights')
    s=p.add_subparsers(dest='command',required=True)
    t=s.add_parser('train')
    t.add_argument('--corpus',type=Path,required=True)
    t.add_argument('--tokenizer',type=Path,required=True)
    t.add_argument('--checkpoint',type=Path,required=True)
    for name,kw in {'steps':500,'width':256,'layers':8,'heads':8,'context-size':2048,
                    'seq-len':256,'batch':2,'grad-accum':4,'threads':2,'save-every':100,
                    'eval-every':100,'min-train-tokens':1000000}.items():
        t.add_argument('--'+name,type=int,default=kw)
    t.add_argument('--lr',type=float,default=3e-4)
    t.add_argument('--resume',action='store_true')
    e=s.add_parser('evaluate')
    e.add_argument('--corpus',type=Path,required=True)
    e.add_argument('--tokenizer',type=Path,required=True)
    e.add_argument('--checkpoint',type=Path,required=True)
    a=p.parse_args()
    if a.command=='train':
        kw=vars(a).copy(); kw.pop('command');
        print(json.dumps(train(tokenizer_path=kw.pop('tokenizer'),output=kw.pop('checkpoint'),
                               **{k.replace('context_size','context_size'):v for k,v in kw.items()}),indent=2))
    else:
        print(json.dumps(evaluate(checkpoint=a.checkpoint,tokenizer_path=a.tokenizer,corpus=a.corpus),indent=2))

if __name__=='__main__':main()
