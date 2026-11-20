"""Vardath Scratch Chat v0.2: independently trained causal language model.

All model weights initialize randomly. This module only loads the project's
own ByteBPE vocabulary, explicitly licensed data and local checkpoints.

Run `python -m capability.pretrain --help` for train/evaluate/sample subcommands.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
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
from vardath_chat.model import ModelConfig, ScratchTransformer

FORMAT = 'vardath-scratch-pretrain-v02'
ROLES = {'user': '<|user|>', 'assistant': '<|assistant|>', 'system': '<|system|>'}


def file_hash(path: Path) -> str:
    d = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            d.update(chunk)
    return d.hexdigest()


def encode_record(record: dict, tok: ByteBPE) -> list[int]:
    """Encode approved text; chats get *actual* role token IDs."""
    ids = [tok.special['<|bos|>']]
    if record.get('kind') == 'chat' and isinstance(record.get('messages'), list):
        for msg in record['messages']:
            if not isinstance(msg, dict) or msg.get('role') not in ROLES or not isinstance(msg.get('content'), str):
                raise ValueError('Malformed chat record')
            ids.append(tok.special[ROLES[msg['role']]])
            ids.extend(tok.encode(msg['content']))
    elif isinstance(record.get('text'), str):
        ids.extend(tok.encode(record['text']))
    else:
        raise ValueError('Record needs chat messages or text')
    ids.append(tok.special['<|eos|>'])
    return ids


def load_tokens(path: Path, tok: ByteBPE) -> tuple[torch.Tensor, dict]:
    if not path.is_file():
        raise FileNotFoundError(f'Prepared split missing: {path}; run 7-Prepare-Corpus.cmd')
    all_ids: list[int] = []
    records = 0
    groups = set()
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get('split') and record['split'] != path.stem:
            raise ValueError('Split metadata does not match file name')
        all_ids.extend(encode_record(record, tok))
        groups.add(record.get('group', ''))
        records += 1
    if len(all_ids) < 3:
        raise ValueError(f'{path}: too few tokens to train/evaluate')
    return torch.tensor(all_ids, dtype=torch.long), {'records': records, 'tokens': len(all_ids), 'groups': len(groups)}


def draw_batch(ids: torch.Tensor, *, batch: int, seq_len: int,
               generator: torch.Generator, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    if seq_len < 1 or len(ids) < seq_len + 1:
        raise ValueError(f'Need at least seq_len+1={seq_len+1} training tokens, found {len(ids)}')
    starts = torch.randint(0, len(ids) - seq_len, (batch,), generator=generator)
    pos = starts[:, None] + torch.arange(seq_len + 1)[None, :]
    windows = ids[pos]
    return windows[:, :-1].to(device=device,dtype=torch.long), windows[:, 1:].to(device=device,dtype=torch.long)


@torch.no_grad()
def eval_loss(model: ScratchTransformer, tokens: torch.Tensor, *, seq_len: int,
              device: torch.device, max_eval_tokens: int = 20_000) -> dict:
    """Measure real next-token cross-entropy on a separate held-out split.

    Every target token is counted once in independent contiguous windows.
    Context resets across windows, so the metric is conservative.
    """
    model.eval()
    if len(tokens) < 2:
        raise ValueError('Evaluation set must have at least two tokens')
    last = min(len(tokens) - 1, max_eval_tokens)
    total_nll, total_count = 0.0, 0
    for start in range(0, last, seq_len):
        length = min(seq_len, last - start)
        x = tokens[start:start + length].unsqueeze(0).to(device=device,dtype=torch.long)
        y = tokens[start + 1:start + length + 1].to(device=device,dtype=torch.long)
        logits = model(x).float().reshape(-1, model.cfg.vocab_size)
        total_nll += F.cross_entropy(logits, y, reduction='sum').item()
        total_count += length
    nll = total_nll / total_count
    return {'loss': round(nll, 6), 'perplexity': round(math.exp(min(nll, 40)), 6),
            'tokens_evaluated': total_count}


def lr_at(step: int, *, peak_lr: float, min_lr: float, warmup: int, decay_steps: int) -> float:
    if step <= warmup and warmup > 0:
        return peak_lr * step / warmup
    if step >= decay_steps:
        return min_lr
    p = (step - warmup) / max(1, decay_steps - warmup)
    return min_lr + (peak_lr - min_lr) * (1 + math.cos(math.pi * p)) / 2


def atomic_save(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    try:
        torch.save(payload, temporary)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _checkpoint(path: Path, model: ScratchTransformer, optimizer, scaler,
                sampler: torch.Generator, step: int, immutable: dict, model_cfg: ModelConfig,
                metrics: dict):
    state = {
        'format': FORMAT, 'step': step, 'model_config': asdict(model_cfg),
        'train_config': immutable,
        'model_state': model.state_dict(),
        'optimizer_state': optimizer.state_dict(),
        'scaler_state': scaler.state_dict() if scaler is not None else None,
        'sampler_rng_state': sampler.get_state(),
        'torch_rng_state': torch.get_rng_state(),
        'cuda_rng_state': torch.cuda.get_rng_state_all() if model_cfg and next(model.parameters()).is_cuda else None,
        'python_rng_state': random.getstate(), 'metrics': metrics,
        'weights_origin': 'random_initialization',
    }
    atomic_save(state, path)


def load_training_checkpoint(path: Path, device: torch.device):
    # This loads checkpoints the user trusts. weights_only=True disallows
    # arbitrary Python objects even if a checkpoint is supplied by others.
    result = torch.load(path, map_location=device, weights_only=True)
    if result.get('format') != FORMAT:
        raise ValueError('Wrong v0.2 checkpoint format')
    return result


def _amp_context(device: torch.device, amp: str):
    if amp == 'off':
        return nullcontext()
    if device.type != 'cuda':
        raise ValueError('Mixed precision is currently supported only on CUDA; use --amp off on CPU')
    return torch.autocast('cuda', dtype=torch.bfloat16 if amp == 'bf16' else torch.float16)


def train(*, corpus: Path, tokenizer_path: Path, output: Path, steps: int = 1000,
          width: int = 384, layers: int = 5, heads: int = 6,
          model_context: int = 1024, seq_len: int = 128,
          batch: int = 2, grad_accum: int = 4, lr: float = 3e-4,
          min_lr: float = 3e-5, warmup: int = 50, decay_steps: int = 2000,
          weight_decay: float = 0.01, clip_norm: float = 1.0, dropout: float = 0.0,
          seed: int = 2026, threads: int = 2, device: str = 'cpu',
          amp: str = 'off', token_cache: Path | None = None, save_every: int = 50, eval_every: int = 50,
          eval_tokens: int = 20000, min_train_tokens: int = 0,
          min_validation_tokens: int = 0, resume: bool = False, quiet: bool = False) -> dict:
    if steps < 1 or width < 8 or layers < 1 or heads < 1 or width % heads or model_context < 2:
        raise ValueError('Invalid model size or training step count')
    if not 1 <= seq_len <= model_context or batch < 1 or grad_accum < 1:
        raise ValueError('Invalid training batch, accumulation or sequence length')
    if min_lr < 0 or lr <= 0 or min_lr > lr or not 0 <= warmup < decay_steps:
        raise ValueError('Invalid learning-rate schedule')
    if threads < 1 or save_every < 1 or eval_every < 1 or eval_tokens < 1:
        raise ValueError('Invalid resource or evaluation settings')
    if amp not in {'off','bf16','fp16'}:
        raise ValueError('amp must be off, bf16 or fp16')
    device_obj = torch.device(('cuda' if torch.cuda.is_available() else 'cpu') if device == 'auto' else device)
    if device_obj.type == 'cuda' and not torch.cuda.is_available():
        raise ValueError('CUDA was requested but is unavailable')
    if amp != 'off' and device_obj.type != 'cuda':
        raise ValueError('Mixed precision requires supported CUDA GPU, otherwise select --amp off')
    torch.set_num_threads(threads)
    if device_obj.type == 'cpu':
        torch.use_deterministic_algorithms(True)
    tok = ByteBPE.load(tokenizer_path)
    if token_cache is not None:
        from capability.token_cache import load_cache
        train_ids, train_stats = load_cache(cache_dir=token_cache,corpus=corpus,tokenizer_path=tokenizer_path,split='train')
        val_ids, val_stats = load_cache(cache_dir=token_cache,corpus=corpus,tokenizer_path=tokenizer_path,split='validation')
    else:
        train_ids, train_stats = load_tokens(corpus / 'train.jsonl', tok)
        val_ids, val_stats = load_tokens(corpus / 'validation.jsonl', tok)
    if len(train_ids) < min_train_tokens or len(val_ids) < min_validation_tokens:
        raise ValueError(f'Training corpus inadequate: {len(train_ids)} train / {len(val_ids)} validation tokens; required {min_train_tokens}/{min_validation_tokens}. Add more approved source documents and rerun preparation/tokenizer/cache.')
    if len(train_ids) <= seq_len:
        raise ValueError(f'Only {len(train_ids)} training tokens; reduce --seq-len or add data')
    cfg = ModelConfig(vocab_size=tok.vocab_size, context_size=model_context,
                      width=width, layers=layers, heads=heads, dropout=dropout)
    immutable = {
        'data_hash': file_hash(corpus/'train.jsonl'),
        'validation_hash': file_hash(corpus/'validation.jsonl'),
        'cache_hash': file_hash(token_cache/'metadata.json') if token_cache is not None else None,
        'tokenizer_hash': file_hash(tokenizer_path),
        'seq_len': seq_len, 'batch': batch, 'grad_accum': grad_accum,
        'lr': lr, 'min_lr': min_lr, 'warmup': warmup,
        'decay_steps': decay_steps, 'weight_decay': weight_decay,
        'clip_norm': clip_norm, 'seed': seed, 'amp': amp,
    }
    if not resume and output.exists():
        raise FileExistsError(f'{output} exists. Use --resume or choose a new output path')
    if resume and not output.exists():
        raise FileNotFoundError(f'No checkpoint to resume: {output}')
    random.seed(seed)
    torch.manual_seed(seed)
    sampler = torch.Generator(device='cpu').manual_seed(seed + 23)
    model = ScratchTransformer(cfg).to(device_obj)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scaler = torch.amp.GradScaler('cuda', enabled=amp == 'fp16') if device_obj.type == 'cuda' else None
    start = 0
    if resume:
        state = load_training_checkpoint(output, device_obj)
        if state['model_config'] != asdict(cfg):
            raise ValueError('Model architecture differs from checkpoint; refusing unsafe resume')
        if state['train_config'] != immutable:
            raise ValueError('Training/data settings changed; refusing non-equivalent resume')
        model.load_state_dict(state['model_state'], strict=True)
        opt.load_state_dict(state['optimizer_state'])
        if scaler is not None and state['scaler_state'] is not None:
            scaler.load_state_dict(state['scaler_state'])
        sampler.set_state(state['sampler_rng_state'].cpu())
        torch.set_rng_state(state['torch_rng_state'].cpu())
        random.setstate(state['python_rng_state'])
        if state.get('cuda_rng_state') is not None and device_obj.type == 'cuda':
            torch.cuda.set_rng_state_all(state['cuda_rng_state'])
        start = int(state['step'])
    count = sum(p.numel() for p in model.parameters())
    if not quiet:
        print(json.dumps({'parameters': count, 'start_step':start, 'target_step':steps,
                          'device':str(device_obj), 'train':train_stats, 'validation':val_stats,
                          'context_capacity':model_context, 'tokens_per_step':batch*seq_len*grad_accum}, indent=2), flush=True)
    if steps <= start:
        raise ValueError(f'Requested target step {steps} must exceed checkpoint step {start}')
    began = time.monotonic()
    metrics: dict = {}
    for step in range(start + 1, steps + 1):
        model.train()
        opt.zero_grad(set_to_none=True)
        this_lr = lr_at(step, peak_lr=lr, min_lr=min_lr, warmup=warmup, decay_steps=decay_steps)
        for group in opt.param_groups:
            group['lr'] = this_lr
        summed_loss = 0.0
        for _ in range(grad_accum):
            xs, ys = draw_batch(train_ids, batch=batch, seq_len=seq_len, generator=sampler, device=device_obj)
            with _amp_context(device_obj, amp):
                logits = model(xs)
                loss = F.cross_entropy(logits.float().flatten(0, 1), ys.flatten())
            summed_loss += float(loss.detach().item()) / grad_accum
            if scaler is not None and scaler.is_enabled():
                scaler.scale(loss / grad_accum).backward()
            else:
                (loss / grad_accum).backward()
        if scaler is not None and scaler.is_enabled():
            scaler.unscale_(opt)
        nn.utils.clip_grad_norm_(model.parameters(), clip_norm)
        if scaler is not None and scaler.is_enabled():
            scaler.step(opt)
            scaler.update()
        else:
            opt.step()
        metrics = {'step':step, 'train_loss':round(summed_loss, 6), 'learning_rate':this_lr}
        if step % eval_every == 0 or step == steps:
            metrics['validation'] = eval_loss(model, val_ids, seq_len=seq_len,
                                              device=device_obj, max_eval_tokens=eval_tokens)
        if step % save_every == 0 or step == steps:
            _checkpoint(output, model, opt, scaler, sampler, step, immutable, cfg, metrics)
        if (step == start + 1 or step % eval_every == 0 or step == steps) and not quiet:
            print(f'step {step:>6} | train {summed_loss:.4f} | lr {this_lr:.7g} | valid {metrics.get("validation", {}).get("loss", "-")} | elapsed {time.monotonic()-began:.1f}s', flush=True)
    return {'checkpoint': str(output), 'parameters':count, 'steps':steps,
            'train_tokens':len(train_ids), 'validation_tokens':len(val_ids), 'final_metrics':metrics}


def evaluate(*, weights: Path, tokenizer_path: Path, corpus: Path, split: str = 'test',
             seq_len: int = 128, eval_tokens: int = 20000, device: str = 'cpu',
             token_cache: Path | None = None) -> dict:
    if split not in ('validation', 'test'):
        raise ValueError('Evaluation split must be validation or test')
    dev = torch.device(device)
    state = load_training_checkpoint(weights, dev)
    if state['train_config']['tokenizer_hash'] != file_hash(tokenizer_path):
        raise ValueError('Tokenizer does not match checkpoint')
    tok = ByteBPE.load(tokenizer_path)
    if token_cache is not None:
        from capability.token_cache import load_cache
        tokens,stats = load_cache(cache_dir=token_cache,corpus=corpus,tokenizer_path=tokenizer_path,split=split)
    else:
        tokens, stats = load_tokens(corpus / (split + '.jsonl'), tok)
    if state['model_config']['vocab_size'] != tok.vocab_size:
        raise ValueError('Model and tokenizer vocab sizes differ')
    cfg = ModelConfig(**state['model_config'])
    model = ScratchTransformer(cfg).to(dev)
    model.load_state_dict(state['model_state'])
    model.eval()
    return {'split':split, 'checkpoint_step':state['step'], 'records':stats['records'],
            'metrics':eval_loss(model,tokens,seq_len=min(seq_len,cfg.context_size),
                                device=dev,max_eval_tokens=eval_tokens)}


@torch.no_grad()
def sample(*, weights: Path, tokenizer_path: Path, prompt: str, max_new_tokens: int = 100,
           temperature: float = 0.8, top_k: int = 30, seed: int = 3,
           device: str = 'cpu') -> str:
    if not prompt:
        raise ValueError('Prompt cannot be empty')
    if max_new_tokens < 1 or temperature < 0 or top_k < 0:
        raise ValueError('Invalid generation parameters')
    dev = torch.device(device)
    tok = ByteBPE.load(tokenizer_path)
    state = load_training_checkpoint(weights, dev)
    if state['train_config']['tokenizer_hash'] != file_hash(tokenizer_path):
        raise ValueError('Tokenizer does not match checkpoint')
    cfg = ModelConfig(**state['model_config'])
    model = ScratchTransformer(cfg).to(dev).eval()
    model.load_state_dict(state['model_state'])
    ids = tok.encode(prompt)
    if not ids:
        raise ValueError('Prompt cannot tokenize to an empty sequence')
    rnd = torch.Generator(device=dev).manual_seed(seed)
    output_ids = []
    special_ids = set(tok.special.values())
    for _ in range(max_new_tokens):
        x = torch.tensor([ids[-cfg.context_size:]], dtype=torch.long,device=dev)
        logits = model(x)[0,-1].float()
        # The next token can end the document, but must not begin a new role.
        for marker, value in tok.special.items():
            if marker != '<|eos|>':
                logits[value] = float('-inf')
        if temperature == 0:
            nxt = int(logits.argmax())
        else:
            logits = logits / temperature
            if top_k:
                values,indices = torch.topk(logits,min(top_k,len(logits)-len(special_ids)+1))
                nxt = int(indices[torch.multinomial(F.softmax(values,dim=-1),1,generator=rnd)].item())
            else:
                nxt = int(torch.multinomial(F.softmax(logits,dim=-1),1,generator=rnd).item())
        if nxt == tok.special['<|eos|>']:
            break
        ids.append(nxt)
        output_ids.append(nxt)
    raw = b''.join(tok.byte_values[t] for t in output_ids if t < len(tok.byte_values))
    return raw.decode('utf-8', errors='replace')


def main() -> None:
    p = argparse.ArgumentParser(description='From-scratch v0.2 BPE language-model pretraining')
    commands = p.add_subparsers(dest='command',required=True)
    t = commands.add_parser('train')
    t.add_argument('--corpus',type=Path,default=Path('data/prepared'))
    t.add_argument('--token-cache',type=Path,default=None,help='Optional memory-mapped token cache directory')
    t.add_argument('--tokenizer',type=Path,default=Path('data/tokenizer-bpe.json'))
    t.add_argument('--output',type=Path,default=Path('checkpoints/v02-base.pt'))
    t.add_argument('--steps',type=int,default=1000,help='Target TOTAL optimizer steps, not steps to add')
    t.add_argument('--width',type=int,default=384)
    t.add_argument('--layers',type=int,default=5)
    t.add_argument('--heads',type=int,default=6)
    t.add_argument('--model-context',type=int,default=1024)
    t.add_argument('--seq-len',type=int,default=128)
    t.add_argument('--batch',type=int,default=2)
    t.add_argument('--grad-accum',type=int,default=4)
    t.add_argument('--lr',type=float,default=3e-4)
    t.add_argument('--min-lr',type=float,default=3e-5)
    t.add_argument('--warmup',type=int,default=50)
    t.add_argument('--decay-steps',type=int,default=2000)
    t.add_argument('--weight-decay',type=float,default=0.01)
    t.add_argument('--clip-norm',type=float,default=1.0)
    t.add_argument('--dropout',type=float,default=0.0)
    t.add_argument('--seed',type=int,default=2026)
    t.add_argument('--threads',type=int,default=2)
    t.add_argument('--device',choices=['auto','cpu','cuda'],default='cpu')
    t.add_argument('--amp',choices=['off','bf16','fp16'],default='off')
    t.add_argument('--save-every',type=int,default=50)
    t.add_argument('--eval-every',type=int,default=50)
    t.add_argument('--eval-tokens',type=int,default=20000)
    t.add_argument('--min-train-tokens',type=int,default=0)
    t.add_argument('--min-validation-tokens',type=int,default=0)
    t.add_argument('--resume',action='store_true')
    e = commands.add_parser('evaluate')
    e.add_argument('--weights',type=Path,required=True)
    e.add_argument('--tokenizer',type=Path,default=Path('data/tokenizer-bpe.json'))
    e.add_argument('--corpus',type=Path,default=Path('data/prepared'))
    e.add_argument('--token-cache',type=Path,default=None)
    e.add_argument('--split',choices=['validation','test'],default='test')
    e.add_argument('--seq-len',type=int,default=128)
    e.add_argument('--eval-tokens',type=int,default=20000)
    e.add_argument('--device',choices=['cpu','cuda'],default='cpu')
    s = commands.add_parser('sample')
    s.add_argument('--weights',type=Path,required=True)
    s.add_argument('--tokenizer',type=Path,default=Path('data/tokenizer-bpe.json'))
    s.add_argument('--prompt',required=True)
    s.add_argument('--max-new-tokens',type=int,default=100)
    s.add_argument('--temperature',type=float,default=0.8)
    s.add_argument('--top-k',type=int,default=30)
    s.add_argument('--seed',type=int,default=3)
    s.add_argument('--device',choices=['cpu','cuda'],default='cpu')
    a = p.parse_args()
    if a.command == 'train':
        result=train(corpus=a.corpus, tokenizer_path=a.tokenizer, output=a.output, steps=a.steps,
                     width=a.width,layers=a.layers,heads=a.heads, model_context=a.model_context,
                     seq_len=a.seq_len,batch=a.batch,grad_accum=a.grad_accum,
                     lr=a.lr,min_lr=a.min_lr,warmup=a.warmup,decay_steps=a.decay_steps,
                     weight_decay=a.weight_decay,clip_norm=a.clip_norm,dropout=a.dropout,
                     seed=a.seed,threads=a.threads,device=a.device,amp=a.amp,
                     save_every=a.save_every,eval_every=a.eval_every,eval_tokens=a.eval_tokens,
                     resume=a.resume,token_cache=a.token_cache,
                     min_train_tokens=a.min_train_tokens,
                     min_validation_tokens=a.min_validation_tokens)
    elif a.command=='evaluate':
        result=evaluate(weights=a.weights,tokenizer_path=a.tokenizer,corpus=a.corpus,
                        split=a.split, seq_len=a.seq_len,eval_tokens=a.eval_tokens,device=a.device,token_cache=a.token_cache)
    else:
        result={'response':sample(weights=a.weights,tokenizer_path=a.tokenizer,prompt=a.prompt,
                                  max_new_tokens=a.max_new_tokens,temperature=a.temperature,
                                  top_k=a.top_k,seed=a.seed,device=a.device)}
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=='__main__':
    main()
