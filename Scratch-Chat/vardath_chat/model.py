"""An original, decoder-only transformer language model.

No downloaded model weights, tokenizers or model-serving frameworks are used.
PyTorch supplies numerical tensor operations and automatic differentiation only.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import torch
from torch import nn
from torch.nn import functional as F

VOCAB_SIZE = 262

@dataclass
class ModelConfig:
    vocab_size: int = VOCAB_SIZE
    context_size: int = 256
    width: int = 96
    layers: int = 3
    heads: int = 4
    dropout: float = 0.0


class CausalAttention(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        assert cfg.width % cfg.heads == 0
        self.heads = cfg.heads
        self.dim = cfg.width // cfg.heads
        self.qkv = nn.Linear(cfg.width, cfg.width * 3)
        self.proj = nn.Linear(cfg.width, cfg.width)
        self.dropout = cfg.dropout

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, t, c = x.shape
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        q = q.reshape(b, t, self.heads, self.dim).transpose(1, 2)
        k = k.reshape(b, t, self.heads, self.dim).transpose(1, 2)
        v = v.reshape(b, t, self.heads, self.dim).transpose(1, 2)
        attn = F.scaled_dot_product_attention(
            q, k, v, is_causal=True,
            dropout_p=self.dropout if self.training else 0.0)
        return self.proj(attn.transpose(1, 2).contiguous().view(b, t, c))


class Block(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.ln1 = nn.LayerNorm(cfg.width)
        self.attn = CausalAttention(cfg)
        self.ln2 = nn.LayerNorm(cfg.width)
        self.ff = nn.Sequential(
            nn.Linear(cfg.width, 4 * cfg.width),
            nn.GELU(),
            nn.Linear(4 * cfg.width, cfg.width),
        )
        self.drop = nn.Dropout(cfg.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.drop(self.attn(self.ln1(x)))
        x = x + self.drop(self.ff(self.ln2(x)))
        return x


class ScratchTransformer(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.cfg = cfg
        self.token_embed = nn.Embedding(cfg.vocab_size, cfg.width)
        self.position_embed = nn.Embedding(cfg.context_size, cfg.width)
        self.blocks = nn.ModuleList(Block(cfg) for _ in range(cfg.layers))
        self.final_ln = nn.LayerNorm(cfg.width)
        self.output = nn.Linear(cfg.width, cfg.vocab_size, bias=False)
        # Weight sharing improves sample efficiency and reduces model size.
        self.output.weight = self.token_embed.weight
        self.apply(self._initialize)

    @staticmethod
    def _initialize(module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0, std=0.02)

    def forward(self, ids: torch.Tensor) -> torch.Tensor:
        b, t = ids.shape
        if t > self.cfg.context_size:
            raise ValueError(f"Sequence length {t} exceeds context {self.cfg.context_size}")
        p = torch.arange(t, device=ids.device)
        x = self.token_embed(ids) + self.position_embed(p)[None, :, :]
        for block in self.blocks:
            x = block(x)
        return self.output(self.final_ln(x))

    @torch.no_grad()
    def generate(self, tokens: list[int], max_tokens: int = 120,
                 temperature: float = 0.45, top_k: int = 16,
                 seed: int | None = None) -> list[int]:
        if seed is not None:
            torch.manual_seed(seed)
        self.eval()
        out = list(tokens)
        from .tokenizer import EOS
        for _ in range(max_tokens):
            # Keep the most recent tokens. This is a bounded-context model.
            tail = out[-self.cfg.context_size:]
            x = torch.tensor([tail], dtype=torch.long, device=next(self.parameters()).device)
            logits = self(x)[0, -1]
            if temperature <= 0:
                nxt = int(torch.argmax(logits).item())
            else:
                logits = logits / temperature
                if top_k > 0:
                    vals, ix = torch.topk(logits, min(top_k, logits.numel()))
                    probs = F.softmax(vals, dim=-1)
                    nxt = int(ix[torch.multinomial(probs, 1).item()].item())
                else:
                    nxt = int(torch.multinomial(F.softmax(logits, -1), 1).item())
            if nxt == EOS:
                break
            out.append(nxt)
        return out[len(tokens):]


def describe(cfg: ModelConfig) -> dict:
    model = ScratchTransformer(cfg)
    return {"architecture": "causal-decoder-transformer", "hyperparameters": asdict(cfg),
            "parameters": sum(p.numel() for p in model.parameters())}
