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
from capability.modern_train import FORMAT as PRETRAIN_FORMAT
from capability.dialogue_sft_train import FORMAT as SFT_FORMAT
from capability.pretrain import file_hash


def load_model(checkpoint: Path, tokenizer: Path):
    tok = ByteBPE.load(tokenizer)
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if state.get("format") not in (PRETRAIN_FORMAT, SFT_FORMAT):
        raise ValueError("Incompatible Scratch Chat checkpoint")
    if state.get("immutable", {}).get("tokenizer_hash") != file_hash(tokenizer):
        raise ValueError("Checkpoint tokenizer mismatch")
    cfg = ModernConfig(**(state["immutable"]["config"] if state["format"] == SFT_FORMAT else state["config"]))
    if cfg.vocab_size != tok.vocab_size:
        raise ValueError("Tokenizer vocabulary size mismatch")
    model = ModernScratchTransformer(cfg)
    model.load_state_dict(state["model_state"], strict=True)
    model.eval()
    model.chat_format = "sft" if state["format"] == SFT_FORMAT else "legacy"
    return model, tok, state


@torch.inference_mode()
def respond(model, tok, messages, *, max_new_tokens=64):
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages must be a nonempty array")
    if not isinstance(max_new_tokens, int) or isinstance(max_new_tokens, bool) or not 1 <= max_new_tokens <= 512:
        raise ValueError("max_new_tokens must be 1..512")
    if len(messages) > 128:
        raise ValueError("Too many messages (maximum 128)")
    # Validate the full conversation before generating tokens.
    roles = []
    for item in messages:
        if not isinstance(item, dict) or item.get("role") not in ("system", "user", "assistant") or not isinstance(item.get("content"), str):
            raise ValueError("Invalid message")
        roles.append(item["role"])
    start = 1 if roles[0] == "system" else 0
    if "system" in roles[start:]:
        raise ValueError("System message must be first")
    if not roles[start:] or roles[start] != "user":
        raise ValueError("Conversation must begin with user message")
    for previous, current in zip(roles[start:], roles[start + 1:]):
        if previous == current:
            raise ValueError("Consecutive identical dialogue roles")
    if roles[-1] != "user":
        raise ValueError("Last message must be user before generation")
    prompt = ""
    for item in messages:
        if not isinstance(item, dict) or item.get("role") not in ("system", "user", "assistant") or not isinstance(item.get("content"), str):
            raise ValueError("Invalid message")
        if len(item["content"]) > 16000:
            raise ValueError("Message exceeds 16000 characters")
        if getattr(model, "chat_format", "legacy") == "sft":
            if "<|im_start|>" in item["content"] or "<|im_end|>" in item["content"]:
                raise ValueError("Reserved chat delimiter")
            prompt += "<|im_start|>" + item["role"] + "\n" + item["content"] + "<|im_end|>\n"
        else:
            prompt += item["role"].capitalize() + ": " + item["content"] + "\n"
    prompt += "<|im_start|>assistant\n" if getattr(model, "chat_format", "legacy") == "sft" else "Assistant: "
    ids = tok.encode(prompt)
    if not ids:
        raise ValueError("Empty prompt")
    generated = []
    stop_markers = (b"<|im_end|>", b"<|im_start|>") if getattr(model, "chat_format", "legacy") == "sft" else (b"\nUser:", b"\nSystem:", b"\nAssistant:")
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
        if any(marker in b"".join(tok.byte_values[i] for i in generated) for marker in stop_markers):
            break
    raw = b"".join(tok.byte_values[i] for i in generated)
    for marker in stop_markers:
        raw = raw.split(marker, 1)[0]
    return raw.decode("utf-8", errors="replace")


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
