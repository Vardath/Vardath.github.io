"""Local supervised chat training and generation for the scratch-built transformer.

Unlike broad language-model pretraining, this phase trains answer-token predictions
from labelled conversations. It does NOT make a small model generally capable.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time

import torch
from torch import nn
from torch.nn import functional as F

from capability.bpe import ByteBPE
from capability.pretrain import atomic_save, file_hash, load_training_checkpoint
from vardath_chat.model import ModelConfig, ScratchTransformer

FORMAT = 'vardath-instruct-v04'
ROLE = {'system':'<|system|>', 'user':'<|user|>', 'assistant':'<|assistant|>'}


def encode_chat(messages: list[dict], tokenizer: ByteBPE) -> tuple[list[int],list[int]]:
    """Return input token IDs and shifted next-token labels (prompt masked)."""
    if not isinstance(messages,list) or len(messages)<2 or messages[-1].get('role')!='assistant':
        raise ValueError('Training chat must end with assistant after a user message')
    if not any(m.get('role')=='user' for m in messages[:-1]):
        raise ValueError('No user message before final assistant')
    ids = [tokenizer.special['<|bos|>']]
    for index,msg in enumerate(messages):
        if not isinstance(msg,dict) or msg.get('role') not in ROLE or not isinstance(msg.get('content'),str):
            raise ValueError('Malformed chat message')
        ids.append(tokenizer.special[ROLE[msg['role']]])
        if index == len(messages)-1:
            start_target = len(ids)
        ids.extend(tokenizer.encode(msg['content']))
    ids.append(tokenizer.special['<|eos|>'])
    labels = ids[1:]
    labels[:start_target-1] = [-100] * (start_target-1)
    if not any(x!=-100 for x in labels):
        raise ValueError('No assistant target tokens')
    return ids[:-1], labels


def read_examples(data: Path, tokenizer: ByteBPE, context_size: int):
    result = {}
    fingerprints = {}
    prompt_fingerprints = {}
    for split in ('train','validation','test'):
        path = data/(split+'.jsonl')
        if not path.is_file():
            raise FileNotFoundError(f'Missing {path}')
        examples=[]
        for line in path.read_text(encoding='utf8').splitlines():
            if not line.strip():
                continue
            record=json.loads(line)
            messages=record.get('messages')
            ids, labels=encode_chat(messages, tokenizer)
            if len(ids)>context_size:
                raise ValueError(f'{split} example uses {len(ids)} tokens; model context is {context_size}')
            if record.get('split', split) != split:
                raise ValueError('Split mismatch in training data')
            # Group is the unit of splitting. Reject duplicate prompt/answer across splits.
            group=record.get('group') or hashlib.sha256(json.dumps(messages,sort_keys=True).encode()).hexdigest()
            old=fingerprints.setdefault(str(group),split)
            if old!=split:
                raise ValueError(f'Train/evaluation leakage: group {group} appears in {old} and {split}')
            prompt=json.dumps(messages[:-1],sort_keys=True,ensure_ascii=False)
            prompt_hash=hashlib.sha256(prompt.encode('utf8')).hexdigest()
            previous=prompt_fingerprints.setdefault(prompt_hash,split)
            if previous!=split:
                raise ValueError(f'Train/evaluation leakage: same conversation prompt appears in {previous} and {split}')
            examples.append((torch.tensor(ids,dtype=torch.long),torch.tensor(labels,dtype=torch.long)))
        if not examples:
            raise ValueError(f'No {split} examples')
        result[split]=examples
    return result


def batch_examples(examples,indices, device, pad):
    rows=[examples[int(i)] for i in indices]
    n=max(len(row[0]) for row in rows)
    x=torch.full((len(rows),n),pad,dtype=torch.long,device=device)
    y=torch.full((len(rows),n),-100,dtype=torch.long,device=device)
    for i,(xx,yy) in enumerate(rows):
        x[i,:len(xx)]=xx.to(device)
        y[i,:len(yy)]=yy.to(device)
    return x,y


@torch.no_grad()
def evaluate_examples(model,examples,device, pad=0):
    model.eval()
    total_loss=0.0; total_labels=0
    for start in range(0,len(examples),8):
        xs,ys=batch_examples(examples,range(start,min(start+8,len(examples))),device,pad)
        logits=model(xs)
        n=int((ys!=-100).sum())
        loss=F.cross_entropy(logits.float().flatten(0,1),ys.flatten(),ignore_index=-100,reduction='sum')
        total_loss+=float(loss); total_labels+=n
    loss=total_loss/max(1,total_labels)
    return {'answer_token_loss':round(loss,6),'perplexity':round(math.exp(min(loss,40)),5),
            'examples':len(examples),'answer_tokens':total_labels}


def train_instruct(*,data:Path,tokenizer_path:Path,output:Path,
                   base_checkpoint:Path|None=None,steps:int=150, width:int=96,layers:int=3,
                   heads:int=4,context_size:int=1024,batch:int=4,
                   lr:float=3e-4,seed:int=33,threads:int=2,
                   save_every:int=25,eval_every:int=25,resume:bool=False,quiet:bool=False,
                   early_stop_evals:int=0,min_delta:float=0.0):
    if steps<1 or batch<1 or lr<=0 or context_size<4 or threads<1 or early_stop_evals<0 or min_delta<0:
        raise ValueError('Invalid training settings')
    torch.set_num_threads(threads)
    torch.use_deterministic_algorithms(True)
    tok=ByteBPE.load(tokenizer_path)
    data_files={k:file_hash(data/(k+'.jsonl')) for k in ('train','validation','test')}
    examples=read_examples(data,tok,context_size)
    base=None
    if base_checkpoint:
        base=load_training_checkpoint(base_checkpoint,torch.device('cpu'))
        cfg=ModelConfig(**base['model_config'])
        if cfg.vocab_size!=tok.vocab_size or cfg.context_size<context_size:
            raise ValueError('Base checkpoint incompatible with tokenizer or context')
        if base['train_config']['tokenizer_hash']!=file_hash(tokenizer_path):
            raise ValueError('Pretraining tokenizer does not match')
        context_size=cfg.context_size
    else:
        cfg=ModelConfig(vocab_size=tok.vocab_size,context_size=context_size,width=width,layers=layers,heads=heads)
    origin_hash=file_hash(base_checkpoint) if base_checkpoint else None
    immutable={'data_hashes':data_files,'tokenizer_hash':file_hash(tokenizer_path),'origin_hash':origin_hash,
               'batch':batch,'lr':lr,'seed':seed,'early_stop_evals':early_stop_evals,'min_delta':min_delta}
    if resume and not output.is_file():
        raise FileNotFoundError('No instruction checkpoint to resume')
    if not resume and output.exists():
        raise FileExistsError(f'Checkpoint exists; use --resume or a new name: {output}')
    random.seed(seed)
    torch.manual_seed(seed)
    gen=torch.Generator(device='cpu').manual_seed(seed+102)
    model=ScratchTransformer(cfg)
    opt=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=0.01)
    step_start=0
    best_loss=float('inf')
    best_step=0
    bad_evals=0
    if resume:
        state=torch.load(output,map_location='cpu',weights_only=True)
        if state.get('format')!=FORMAT or state['immutable']!=immutable or state['model_config']!=asdict(cfg):
            raise ValueError('Checkpoint and training settings incompatible')
        model.load_state_dict(state['model_state'])
        opt.load_state_dict(state['optimizer_state'])
        gen.set_state(state['sampler_rng_state'])
        torch.set_rng_state(state['torch_rng_state'])
        step_start=int(state['step'])
        best_loss=float(state.get('best_loss',float('inf')))
        best_step=int(state.get('best_step',0))
        bad_evals=int(state.get('bad_evals',0))
    elif base:
        model.load_state_dict(base['model_state'],strict=True)
    if step_start>=steps:
        raise ValueError('Target steps must exceed checkpoint steps')
    metrics={'before':evaluate_examples(model,examples['validation'],torch.device('cpu'),tok.special['<|bos|>'])}
    if not resume:
        best_loss=metrics['before']['answer_token_loss']
    best_path=output.with_name(output.stem+'-best'+output.suffix)
    stopped_early=False

    def save_checkpoint(path, step):
        atomic_save({'format':FORMAT,'step':step,'model_config':asdict(cfg),
            'immutable':immutable,'model_state':model.state_dict(),
            'optimizer_state':opt.state_dict(),'sampler_rng_state':gen.get_state(),
            'torch_rng_state':torch.get_rng_state(),'metrics':metrics,
            'best_loss':best_loss,'best_step':best_step,'bad_evals':bad_evals,
            'weights_origin':'random_initialization_then_local_training'},path)

    for step in range(step_start+1,steps+1):
        model.train()
        indices=torch.randint(len(examples['train']),(batch,),generator=gen).tolist()
        xs,ys=batch_examples(examples['train'],indices,torch.device('cpu'),tok.special['<|bos|>'])
        logits=model(xs)
        loss=F.cross_entropy(logits.float().flatten(0,1),ys.flatten(),ignore_index=-100)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(),1.0)
        opt.step()
        metrics['step']=step
        metrics['train_loss']=round(float(loss.detach()),6)
        if step%eval_every==0 or step==steps:
            metrics['validation']=evaluate_examples(model,examples['validation'],torch.device('cpu'),tok.special['<|bos|>'])
            validation_loss=metrics['validation']['answer_token_loss']
            if validation_loss < best_loss-min_delta:
                best_loss=validation_loss
                best_step=step
                bad_evals=0
                save_checkpoint(best_path,step)
            else:
                bad_evals+=1
            if not quiet:
                print(f'step {step} train={metrics["train_loss"]:.4f} val={validation_loss:.4f} best={best_loss:.4f}',flush=True)
        if step%save_every==0 or step==steps:
            save_checkpoint(output,step)
        if early_stop_evals and bad_evals>=early_stop_evals:
            save_checkpoint(output,step)
            stopped_early=True
            break
    return {'checkpoint':str(output),'steps_requested':steps,'steps_completed':step,
            'best_checkpoint':str(best_path) if best_step else None,
            'best_step':best_step,'early_stopped':stopped_early,
            'parameters':sum(x.numel() for x in model.parameters()),
            'validation':metrics.get('validation'),'before':metrics.get('before')}


@torch.no_grad()
def reply(weights:Path,tokenizer_path:Path,messages:list[dict],max_new_tokens:int=90,
          temperature:float=0.0, seed:int=2026)->str:
    if not messages or messages[-1].get('role')!='user' or max_new_tokens<1:
        raise ValueError('Messages must end in a user message')
    if temperature<0:raise ValueError('Temperature must be nonnegative')
    tok=ByteBPE.load(tokenizer_path)
    state=torch.load(weights,map_location='cpu',weights_only=True)
    if state.get('format')!=FORMAT or state['immutable']['tokenizer_hash']!=file_hash(tokenizer_path):
        raise ValueError('Expected a compatible instruction checkpoint')
    cfg=ModelConfig(**state['model_config'])
    model=ScratchTransformer(cfg).eval()
    model.load_state_dict(state['model_state'])
    ids=[tok.special['<|bos|>']]
    for m in messages:
        if m.get('role') not in ROLE or not isinstance(m.get('content'),str):
            raise ValueError('Malformed message')
        ids.append(tok.special[ROLE[m['role']]])
        ids.extend(tok.encode(m['content']))
    ids.append(tok.special['<|assistant|>'])
    output=[]
    generator=torch.Generator().manual_seed(seed)
    for _ in range(max_new_tokens):
        logits=model(torch.tensor([ids[-cfg.context_size:]],dtype=torch.long))[0,-1].float()
        for tag,v in tok.special.items():
            if tag!='<|eos|>':logits[v]=float('-inf')
        if temperature==0:
            next_id=int(logits.argmax())
        else:
            next_id=int(torch.multinomial(F.softmax(logits/temperature,dim=-1),1,generator=generator).item())
        if next_id==tok.special['<|eos|>']:break
        ids.append(next_id)
        output.append(next_id)
    return b''.join(tok.byte_values[t] for t in output).decode('utf-8',errors='replace')


def main():
    parser=argparse.ArgumentParser(description='Scratch Chat supervised instruction training')
    sub=parser.add_subparsers(dest='cmd',required=True)
    t=sub.add_parser('train')
    t.add_argument('--data',type=Path,required=True)
    t.add_argument('--tokenizer',type=Path,required=True)
    t.add_argument('--checkpoint',type=Path,required=True)
    t.add_argument('--base',type=Path)
    t.add_argument('--steps',type=int,default=150)
    t.add_argument('--batch',type=int,default=4)
    t.add_argument('--threads',type=int,default=2)
    t.add_argument('--lr',type=float,default=0.0003)
    t.add_argument('--seed',type=int,default=33)
    t.add_argument('--resume',action='store_true')
    t.add_argument('--save-every',type=int,default=25)
    t.add_argument('--eval-every',type=int,default=25)
    t.add_argument('--early-stop-evals',type=int,default=0)
    t.add_argument('--min-delta',type=float,default=0.0)
    e=sub.add_parser('evaluate')
    e.add_argument('--checkpoint',type=Path,required=True)
    e.add_argument('--tokenizer',type=Path,required=True)
    e.add_argument('--data',type=Path,required=True)
    c=sub.add_parser('chat')
    c.add_argument('--checkpoint',type=Path,required=True)
    c.add_argument('--tokenizer',type=Path,required=True)
    c.add_argument('--prompt',default=None)
    c.add_argument('--max-new-tokens',type=int,default=90)
    args=parser.parse_args()
    if args.cmd=='train':
        result=train_instruct(data=args.data,tokenizer_path=args.tokenizer,output=args.checkpoint,
                        base_checkpoint=args.base,steps=args.steps,batch=args.batch,threads=args.threads,
                        lr=args.lr,seed=args.seed,resume=args.resume,save_every=args.save_every,
                        eval_every=args.eval_every,early_stop_evals=args.early_stop_evals,min_delta=args.min_delta)
        print(json.dumps(result,indent=2))
    elif args.cmd=='evaluate':
        tok=ByteBPE.load(args.tokenizer)
        ck=torch.load(args.checkpoint,map_location='cpu',weights_only=True)
        if ck['immutable']['tokenizer_hash']!=file_hash(args.tokenizer):raise ValueError('Tokenizer changed')
        model=ScratchTransformer(ModelConfig(**ck['model_config'])).eval()
        model.load_state_dict(ck['model_state'])
        samples=read_examples(args.data,tok,model.cfg.context_size)
        print(json.dumps({part:evaluate_examples(model,samples[part],torch.device('cpu'),tok.special['<|bos|>']) for part in ('validation','test')},indent=2))
    else:
        history=[]
        while True:
            prompt=args.prompt if args.prompt is not None else input('You: ').strip()
            if prompt.lower() in ('quit','exit'):break
            history.append({'role':'user','content':prompt})
            answer=reply(args.checkpoint,args.tokenizer,history,max_new_tokens=args.max_new_tokens)
            print('Model:',answer)
            history.append({'role':'assistant','content':answer})
            if args.prompt is not None:break

if __name__=='__main__':main()
