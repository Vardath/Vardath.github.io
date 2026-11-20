"""Modern scratch-only causal transformer: RoPE, RMSNorm and SwiGLU.

Original implementation using PyTorch's tensor primitives, no pretrained weights.
Legacy ScratchTransformer and all older checkpoints are deliberately unchanged.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
import torch
from torch import nn
from torch.nn import functional as F


@dataclass(frozen=True)
class ModernConfig:
    vocab_size: int
    context_size: int = 2048
    width: int = 256
    layers: int = 8
    heads: int = 8
    ff_multiplier: float = 3.0
    dropout: float = 0.0

    def __post_init__(self):
        if (self.vocab_size < 8 or self.context_size < 2 or self.width < 16
            or self.layers < 1 or self.heads < 1 or self.width % self.heads
            or (self.width // self.heads) % 2 or self.ff_multiplier <= 0
            or not 0 <= self.dropout < 1):
            raise ValueError('Invalid modern transformer configuration')


class RMSNorm(nn.Module):
    def __init__(self, width: int, eps: float = 1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(width))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x * torch.rsqrt(x.float().square().mean(dim=-1, keepdim=True) + self.eps).to(x.dtype) * self.weight


def apply_rope(x: torch.Tensor) -> torch.Tensor:
    """Apply rotary encoding to [batch, heads, sequence, head_dim] tensor."""
    d = x.shape[-1]
    if d % 2:
        raise ValueError('RoPE requires even head dimension')
    inv = torch.arange(0, d, 2, device=x.device, dtype=torch.float32)
    inv = 1.0 / (10000.0 ** (inv / d))
    t = torch.arange(x.shape[-2], device=x.device, dtype=torch.float32)
    angle = torch.outer(t, inv)
    cos, sin = angle.cos()[None, None, :, :], angle.sin()[None, None, :, :]
    first, second = x.float()[..., ::2], x.float()[..., 1::2]
    out = torch.stack((first * cos - second * sin, first * sin + second * cos), dim=-1)
    return out.flatten(-2).to(x.dtype)


class Attention(nn.Module):
    def __init__(self, cfg: ModernConfig):
        super().__init__()
        self.heads = cfg.heads
        self.dim = cfg.width // cfg.heads
        self.qkv = nn.Linear(cfg.width, cfg.width * 3, bias=False)
        self.out = nn.Linear(cfg.width, cfg.width, bias=False)
        self.dropout = cfg.dropout

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, t, c = x.shape
        q, k, v = self.qkv(x).chunk(3, -1)
        q = apply_rope(q.view(b, t, self.heads, self.dim).transpose(1, 2))
        k = apply_rope(k.view(b, t, self.heads, self.dim).transpose(1, 2))
        v = v.view(b, t, self.heads, self.dim).transpose(1, 2)
        y = F.scaled_dot_product_attention(q, k, v, is_causal=True,
                                            dropout_p=self.dropout if self.training else 0.0)
        return self.out(y.transpose(1, 2).contiguous().view(b, t, c))


class Block(nn.Module):
    def __init__(self, cfg: ModernConfig):
        super().__init__()
        width = cfg.width
        ff = int(math.ceil(width * cfg.ff_multiplier / 8) * 8)
        self.pre_attn = RMSNorm(width)
        self.attn = Attention(cfg)
        self.pre_ff = RMSNorm(width)
        self.gate = nn.Linear(width, ff, bias=False)
        self.up = nn.Linear(width, ff, bias=False)
        self.down = nn.Linear(ff, width, bias=False)
        self.dropout = nn.Dropout(cfg.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.dropout(self.attn(self.pre_attn(x)))
        h = self.pre_ff(x)
        return x + self.dropout(self.down(F.silu(self.gate(h)) * self.up(h)))


class ModernScratchTransformer(nn.Module):
    def __init__(self, cfg: ModernConfig):
        super().__init__()
        self.cfg = cfg
        self.embed = nn.Embedding(cfg.vocab_size, cfg.width)
        self.blocks = nn.ModuleList(Block(cfg) for _ in range(cfg.layers))
        self.norm = RMSNorm(cfg.width)
        self.out = nn.Linear(cfg.width, cfg.vocab_size, bias=False)
        self.out.weight = self.embed.weight
        self.apply(self._init)

    @staticmethod
    def _init(m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, std=0.02)
        if isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, std=0.02)

    def forward(self, ids: torch.Tensor) -> torch.Tensor:
        if ids.ndim != 2 or ids.size(1) < 1 or ids.size(1) > self.cfg.context_size:
            raise ValueError('Input must be [batch, 1..context_size] token IDs')
        x = self.embed(ids)
        for block in self.blocks:
            x = block(x)
        return self.out(self.norm(x))

    @property
    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())
