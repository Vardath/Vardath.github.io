"""Load and serve locally trained weights. No external model service is called."""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import torch
from .model import ModelConfig, ScratchTransformer
from .tokenizer import encode_chat, decode_text


def save_checkpoint(path: Path, model: ScratchTransformer, metadata: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"format": "vardath-chat-v1", "config": asdict(model.cfg),
                "state": model.state_dict(), "metadata": metadata or {}}, path)


def load_checkpoint(path: Path, device: str = "cpu") -> tuple[ScratchTransformer, dict]:
    if not path.is_file():
        raise FileNotFoundError(f"No trained model weights at {path}. Run 2-Train.cmd first.")
    # weights_only=True prevents arbitrary unpickling of untrusted weight files.
    payload = torch.load(path, map_location=device, weights_only=True)
    if payload.get("format") != "vardath-chat-v1":
        raise ValueError("Not a Vardath Scratch Chat checkpoint")
    model = ScratchTransformer(ModelConfig(**payload["config"]))
    model.load_state_dict(payload["state"], strict=True)
    model.eval().to(device)
    return model, payload.get("metadata", {})


class LocalChatEngine:
    def __init__(self, weights: str | Path, device: str = "cpu"):
        self.model, self.metadata = load_checkpoint(Path(weights), device)
        self.device = device

    def reply(self, messages: list[dict], max_tokens: int = 100,
              temperature: float = 0.35, seed: int | None = None) -> str:
        if not isinstance(messages, list) or not messages:
            raise ValueError("Expected a nonempty messages array")
        prefix = encode_chat(messages, context_size=self.model.cfg.context_size)
        output = self.model.generate(prefix, max_tokens=max(1, min(max_tokens, 512)),
                                     temperature=temperature, seed=seed)
        return decode_text(output).strip()
