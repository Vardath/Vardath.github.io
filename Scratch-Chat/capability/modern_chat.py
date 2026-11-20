"""Standalone Vardath Scratch Chat generation using *locally trained* modern weights.

No remote APIs, no downloaded pretrained weights.  The bundled v0.6 model is a
training proof, not a capable general-purpose model.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch.nn import functional as F

from capability.bpe import ByteBPE
from capability.instruct import ROLE
from capability.modern_model import ModernConfig, ModernScratchTransformer
from capability.pretrain import file_hash

CHECKPOINT_FORMAT = 'deepthort-modern-instruct-v06'  # historical on-disk format; preserve compatibility


def load_chat(checkpoint: Path, tokenizer_path: Path):
    tok = ByteBPE.load(tokenizer_path)
    state = torch.load(checkpoint, map_location='cpu', weights_only=True)
    if state.get('format') != CHECKPOINT_FORMAT:
        raise ValueError('Modern instruction-training checkpoint required. Pretraining alone is not chat-ready.')
    if state['immutable']['tokenizer_hash'] != file_hash(tokenizer_path):
        raise ValueError('Checkpoint/tokenizer mismatch')
    cfg = ModernConfig(**state['config'])
    if tok.vocab_size != cfg.vocab_size:
        raise ValueError('Vocabulary mismatch')
    model = ModernScratchTransformer(cfg).eval()
    model.load_state_dict(state['model_state'], strict=True)
    return model, tok


def encode_dialog(messages: list[dict], tokenizer: ByteBPE, context_size: int) -> list[int]:
    if not isinstance(messages, list) or not messages or not isinstance(messages[-1], dict) or messages[-1].get('role') != 'user':
        raise ValueError('Conversation must end with a user message')
    if not all(isinstance(m, dict) and m.get('role') in ROLE and isinstance(m.get('content'), str)
               for m in messages):
        raise ValueError('Invalid role or content')
    system = messages[:1] if messages[0]['role'] == 'system' else []
    others = messages[len(system):]
    while True:
        ids = [tokenizer.special['<|bos|>']]
        for m in system + others:
            ids.append(tokenizer.special[ROLE[m['role']]])
            ids.extend(tokenizer.encode(m['content']))
        ids.append(tokenizer.special['<|assistant|>'])
        if len(ids) < context_size:
            return ids
        if len(others) <= 1:
            raise ValueError('Latest user prompt or system instruction exceeds model context')
        others = others[2:] if len(others) >= 3 else others[1:]


@torch.inference_mode()
def generate_tokens(model: ModernScratchTransformer, tok: ByteBPE, messages: list[dict],
                    *, max_new_tokens: int = 64, temperature: float = 0.0,
                    top_p: float = 1.0, top_k: int = 0, repetition_penalty: float = 1.0,
                    seed: int = 2026) -> tuple[list[int], int]:
    """Generate raw token IDs plus prompt length for reliable API token accounting.

    Sampling controls expose model behaviour; they do *not* make an untrained model smart.
    Context is bounded, and generation stops at EOS or full context.
    """
    if not isinstance(max_new_tokens, int) or isinstance(max_new_tokens, bool) or max_new_tokens < 1:
        raise ValueError('max_new_tokens must be a positive integer')
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 0:
        raise ValueError('top_k must be a nonnegative integer')
    if not 0.0 < top_p <= 1.0 or temperature < 0 or repetition_penalty < 1.0:
        raise ValueError('Invalid sampling controls')
    ids = encode_dialog(messages, tok, model.cfg.context_size)
    prompt_count = len(ids)
    output = []
    rng = torch.Generator(device='cpu').manual_seed(seed)
    for _ in range(min(max_new_tokens, model.cfg.context_size - len(ids))):
        logits = model(torch.tensor([ids], dtype=torch.long))[0, -1].float().clone()
        for tag, token_id in tok.special.items():
            if tag != '<|eos|>':
                logits[token_id] = float('-inf')
        if repetition_penalty > 1.0:
            for token_id in set(output):
                if logits[token_id] > 0:
                    logits[token_id] /= repetition_penalty
                else:
                    logits[token_id] *= repetition_penalty
        if temperature == 0:
            next_id = int(logits.argmax())
        else:
            logits /= temperature
            if top_k:
                cutoff = torch.topk(logits, min(top_k, logits.numel())).values[-1]
                logits[logits < cutoff] = -float('inf')
            if top_p < 1.0:
                sorted_logits, sorted_ids = logits.sort(descending=True)
                probs = F.softmax(sorted_logits, dim=0)
                excess = probs.cumsum(0) > top_p
                excess[1:] = excess[:-1].clone()
                excess[0] = False
                logits[sorted_ids[excess]] = -float('inf')
            probs = F.softmax(logits, dim=0)
            next_id = int(torch.multinomial(probs, 1, generator=rng).item())
        if next_id == tok.special['<|eos|>']:
            break
        output.append(next_id)
        ids.append(next_id)
    return output, prompt_count


def decode_tokens(tok: ByteBPE, tokens: list[int]) -> str:
    return b''.join(tok.byte_values[t] for t in tokens).decode('utf-8', errors='replace')


def generate(model: ModernScratchTransformer, tok: ByteBPE, messages: list[dict],
             *, max_new_tokens: int = 64, temperature: float = 0.0,
             top_p: float = 1.0, top_k: int = 0, repetition_penalty: float = 1.0,
             seed: int = 2026) -> str:
    output, _ = generate_tokens(model, tok, messages, max_new_tokens=max_new_tokens,
                               temperature=temperature, top_p=top_p, top_k=top_k,
                               repetition_penalty=repetition_penalty, seed=seed)
    return decode_tokens(tok, output)


def main(argv=None):
    p = argparse.ArgumentParser(description='Standalone Vardath Scratch Chat: modern scratch model')
    p.add_argument('--checkpoint', type=Path, required=True)
    p.add_argument('--tokenizer', type=Path, required=True)
    p.add_argument('--prompt')
    p.add_argument('--max-new-tokens', type=int, default=72)
    p.add_argument('--temperature', type=float, default=0.0)
    p.add_argument('--top-p', type=float, default=1.0)
    p.add_argument('--top-k', type=int, default=0)
    p.add_argument('--repetition-penalty', type=float, default=1.0)
    args = p.parse_args(argv)
    model, tok = load_chat(args.checkpoint, args.tokenizer)
    history = []
    while True:
        if args.prompt is None:
            try:
                user_text = input('You: ')
            except (EOFError, KeyboardInterrupt):
                break
        else:
            user_text = args.prompt
        if user_text.strip().lower() in ('exit', 'quit', '/quit'):
            break
        history.append({'role': 'user', 'content': user_text})
        try:
            answer = generate(model, tok, history, max_new_tokens=args.max_new_tokens,
                              temperature=args.temperature, top_p=args.top_p, top_k=args.top_k,
                              repetition_penalty=args.repetition_penalty)
        except ValueError as exc:
            history.pop()
            print('Error:', exc)
            continue
        print('Scratch Chat:', answer)
        history.append({'role': 'assistant', 'content': answer})
        if args.prompt is not None:
            break

if __name__ == '__main__':
    main()
