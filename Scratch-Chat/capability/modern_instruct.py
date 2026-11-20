"""Instruction-tune *modern scratch transformer* without pretrained third-party weights.

Requires pretraining checkpoint from capability.modern_train. This fine-tuning
is supervised answer-token training on train-only data with held-out early stop.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

import torch
from torch.nn import functional as F

from capability.bpe import ByteBPE
from capability.instruct import batch_examples, evaluate_examples, read_examples
from capability.modern_model import ModernConfig, ModernScratchTransformer
from capability.modern_chat import CHECKPOINT_FORMAT
from capability.pretrain import atomic_save, file_hash
from capability.modern_train import FORMAT as PRETRAIN_FORMAT


def fine_tune(*, base: Path, tokenizer_path: Path, data: Path, output: Path,
              steps: int = 150, batch: int = 4, lr: float = 2e-4,
              eval_every: int = 25, save_every: int = 25,
              patience_evals: int = 4, seed: int = 2026,
              threads: int = 2, resume: bool = False):
    if min(steps, batch, eval_every, save_every, threads) < 1 or lr <= 0 or patience_evals < 0:
        raise ValueError('Invalid training settings')
    torch.set_num_threads(threads)
    torch.use_deterministic_algorithms(True)
    tokenizer = ByteBPE.load(tokenizer_path)
    immutable = {'tokenizer_hash': file_hash(tokenizer_path),
                 'train_hash': file_hash(data / 'train.jsonl'),
                 'validation_hash': file_hash(data / 'validation.jsonl'),
                 'base_hash': file_hash(base), 'batch': batch,
                 'lr': lr, 'seed': seed}
    base_state = torch.load(base, map_location='cpu', weights_only=True)
    if base_state.get('format') != PRETRAIN_FORMAT:
        raise ValueError('Expected a modern language-pretraining checkpoint; fine-tuning must not start from an unrelated toy model')
    if base_state['immutable']['tokenizer_hash'] != immutable['tokenizer_hash']:
        raise ValueError('Pretraining tokenizer does not match instruction tokenizer')
    cfg = ModernConfig(**base_state['config'])
    if cfg.vocab_size != tokenizer.vocab_size:
        raise ValueError('Tokenizer vocabulary mismatch')
    sets = read_examples(data, tokenizer, cfg.context_size)
    if output.resolve() == base.resolve():
        raise ValueError('Instruction checkpoint must not overwrite pretraining checkpoint')
    best = output.with_name(output.stem + '-best' + output.suffix)
    model = ModernScratchTransformer(cfg)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    sampler = torch.Generator().manual_seed(seed + 19)
    start = 0
    best_loss = float('inf')
    best_step = 0
    misses = 0
    metrics = {}
    if resume:
        if not output.exists(): raise FileNotFoundError('Cannot resume without a checkpoint')
        state = torch.load(output, map_location='cpu', weights_only=True)
        if state.get('format') != CHECKPOINT_FORMAT or state['config'] != asdict(cfg) or state['immutable'] != immutable:
            raise ValueError('Resume checkpoint incompatible with current data, base, or settings')
        model.load_state_dict(state['model_state'])
        optimizer.load_state_dict(state['optimizer_state'])
        sampler.set_state(state['sampler_state'])
        torch.set_rng_state(state['torch_rng_state'])
        start = int(state['step'])
        best_loss = float(state['best_loss'])
        best_step = int(state['best_step'])
        misses = int(state['misses'])
        metrics = state['metrics']
    else:
        if output.exists() or best.exists():
            raise FileExistsError('Use --resume, or choose a new checkpoint path')
        torch.manual_seed(seed)
        model.load_state_dict(base_state['model_state'])
        metrics['before'] = evaluate_examples(model, sets['validation'], torch.device('cpu'), tokenizer.special['<|pad|>'])
    if steps <= start:
        raise ValueError('Target steps must exceed current training step')

    def save(path: Path, step: int):
        atomic_save({'format': CHECKPOINT_FORMAT, 'step': step,
                     'config': asdict(cfg), 'immutable': immutable,
                     'model_state': model.state_dict(),
                     'optimizer_state': optimizer.state_dict(),
                     'sampler_state': sampler.get_state(),
                     'torch_rng_state': torch.get_rng_state(),
                     'metrics': metrics, 'best_loss': best_loss,
                     'best_step': best_step, 'misses': misses,
                     'origin': 'Fine-tuned from self-trained Vardath Scratch Chat modern pretrained base'}, path)

    stopped_early = False
    last_step = start
    for step in range(start + 1, steps + 1):
        last_step = step
        model.train()
        indices = torch.randint(0, len(sets['train']), (batch,), generator=sampler)
        x, y = batch_examples(sets['train'], indices, torch.device('cpu'), tokenizer.special['<|pad|>'])
        optimizer.zero_grad(set_to_none=True)
        logits = model(x)
        loss = F.cross_entropy(logits.flatten(0, 1), y.flatten(), ignore_index=-100)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        metrics['step'] = step
        metrics['train_loss'] = round(float(loss.detach()), 6)
        if step % eval_every == 0 or step == steps:
            val = evaluate_examples(model, sets['validation'], torch.device('cpu'), tokenizer.special['<|pad|>'])
            metrics['validation'] = val
            if val['answer_token_loss'] < best_loss - 1e-5:
                best_loss = val['answer_token_loss']
                best_step = step
                misses = 0
                save(best, step)
            else:
                misses += 1
            if patience_evals and misses >= patience_evals:
                stopped_early = True
        if step % save_every == 0 or step == steps or stopped_early:
            save(output, step)
        if stopped_early:
            break
    return {'steps': last_step, 'best_step': best_step, 'best_checkpoint': str(best),
            'checkpoint': str(output), 'parameters': model.parameter_count,
            'early_stopped': stopped_early,
            'validation': metrics.get('validation'),
            'test': evaluate_checkpoint(best if best.exists() else output, tokenizer_path, data)['test']}


def evaluate_checkpoint(checkpoint: Path, tokenizer_path: Path, data: Path):
    tok = ByteBPE.load(tokenizer_path)
    state = torch.load(checkpoint, map_location='cpu', weights_only=True)
    if state.get('format') != CHECKPOINT_FORMAT or state['immutable']['tokenizer_hash'] != file_hash(tokenizer_path):
        raise ValueError('Not a compatible modern instruction checkpoint')
    cfg = ModernConfig(**state['config'])
    model = ModernScratchTransformer(cfg).eval()
    model.load_state_dict(state['model_state'])
    sets = read_examples(data, tok, cfg.context_size)
    return {k: evaluate_examples(model, sets[k], torch.device('cpu'), tok.special['<|pad|>'])
            for k in ('validation', 'test')}


def main(argv=None):
    p = argparse.ArgumentParser(description='Vardath Scratch Chat modern instruction fine-tuning')
    sub = p.add_subparsers(dest='action', required=True)
    t = sub.add_parser('train')
    t.add_argument('--base', type=Path, required=True)
    t.add_argument('--tokenizer', type=Path, required=True)
    t.add_argument('--data', type=Path, required=True)
    t.add_argument('--checkpoint', type=Path, required=True)
    t.add_argument('--steps', type=int, default=150)
    t.add_argument('--batch', type=int, default=4)
    t.add_argument('--threads', type=int, default=2)
    t.add_argument('--lr', type=float, default=2e-4)
    t.add_argument('--eval-every', type=int, default=25)
    t.add_argument('--save-every', type=int, default=25)
    t.add_argument('--patience-evals', type=int, default=4)
    t.add_argument('--resume', action='store_true')
    e = sub.add_parser('evaluate')
    e.add_argument('--checkpoint', type=Path, required=True)
    e.add_argument('--tokenizer', type=Path, required=True)
    e.add_argument('--data', type=Path, required=True)
    args = p.parse_args(argv)
    if args.action == 'train':
        d = vars(args); d.pop('action'); d['output'] = d.pop('checkpoint'); d['tokenizer_path'] = d.pop('tokenizer');
        print(json.dumps(fine_tune(**d), indent=2))
    else:
        print(json.dumps(evaluate_checkpoint(args.checkpoint,args.tokenizer,args.data),indent=2))


if __name__ == '__main__':
    main()
