"""Dependency-light JSON-line protocol for embedding Scratch Chat in DeepThorT.

Launch with python -m capability.deepthort_bridge --checkpoint ... --tokenizer ...
Send one JSON object per line on stdin. No pretrained weights are loaded.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import torch
from capability.bpe import ByteBPE
from capability.modern_model import ModernConfig, ModernScratchTransformer
from capability.modern_train import FORMAT
from capability.pretrain import file_hash


def load_model(checkpoint: Path, tokenizer: Path):
    tok = ByteBPE.load(tokenizer)
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if state.get("format") != FORMAT:
        raise ValueError("Incompatible Scratch Chat checkpoint")
    if state.get("immutable", {}).get("tokenizer_hash") != file_hash(tokenizer):
        raise ValueError("Checkpoint tokenizer mismatch")
    cfg = ModernConfig(**state["config"])
    if cfg.vocab_size != tok.vocab_size:
        raise ValueError("Tokenizer vocabulary size mismatch")
    model = ModernScratchTransformer(cfg)
    model.load_state_dict(state["model_state"], strict=True)
    model.eval()
    return model, tok, state


@torch.inference_mode()
def respond(model, tok, messages, *, max_new_tokens=64):
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages must be a nonempty array")
    if not 1 <= max_new_tokens <= 512:
        raise ValueError("max_new_tokens must be 1..512")
    prompt = ""
    for item in messages:
        if not isinstance(item, dict) or item.get("role") not in ("system", "user", "assistant") or not isinstance(item.get("content"), str):
            raise ValueError("Invalid message")
        prompt += item["role"].capitalize() + ": " + item["content"] + "\n"
    prompt += "Assistant: "
    ids = tok.encode(prompt)
    if not ids:
        raise ValueError("Empty prompt")
    generated = []
    eos = tok.special.get("<|eos|>")
    for _ in range(max_new_tokens):
        x = torch.tensor([ids[-model.cfg.context_size:]], dtype=torch.long)
        logits = model(x)[0, -1].float()
        for special_id in tok.special.values():
            if special_id != eos:
                logits[special_id] = -float("inf")
        nxt = int(logits.argmax().item())
        if nxt == eos:
            break
        ids.append(nxt)
        generated.append(nxt)
    return b''.join(tok.byte_values[i] for i in generated).decode('utf-8', errors='replace')


def serve(model, tok, checkpoint_state):
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise ValueError("Request must be a JSON object")
            if request.get("method") == "health":
                result = {"ok": True, "model": "vardath-scratch-chat", "checkpoint_step": checkpoint_state["step"], "ready_for_conversation": False}
            elif request.get("method") == "chat":
                result = {"ok": True, "response": respond(model, tok, request.get("messages"), max_new_tokens=request.get("max_new_tokens", 64)), "experimental": True}
            else:
                raise ValueError("Unknown method")
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            result = {"ok": False, "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, required=True)
    args = parser.parse_args()
    model, tok, state = load_model(args.checkpoint, args.tokenizer)
    serve(model, tok, state)


if __name__ == "__main__":
    main()
