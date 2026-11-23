"""Analytical capacity and optimizer-memory planning; no GPU allocation or training.

Counts tied embedding/output once, matching ModernScratchTransformer.
Estimates exclude activations, kernels, allocator fragmentation and dataloader.
"""
import argparse
import json
import math


def estimate(vocab_size, width, layers, heads, context_size, *, ff_multiplier=3.0):
    if (vocab_size < 8 or width < 16 or layers < 1 or heads < 1
            or width % heads or (width // heads) % 2
            or context_size < 2 or ff_multiplier <= 0):
        raise ValueError("Invalid ModernConfig dimensions")
    ff = math.ceil(width * ff_multiplier / 8) * 8
    # tied embedding, 2 RMSNorms/block + final RMSNorm,
    # attention qkv/out and SwiGLU gate/up/down, all without bias
    parameters = vocab_size * width + layers * (2 * width + 4 * width * width + 3 * width * ff) + width
    return {
        "parameters": parameters,
        "ff_width": ff,
        "weights_fp32_gib": round(parameters * 4 / 2**30, 4),
        "adamw_fp32_weights_grad_moments_gib": round(parameters * 16 / 2**30, 4),
        "adamw_mixed_precision_master_weights_grad_moments_gib": round(parameters * 18 / 2**30, 4),
        "context_size": context_size,
        "warning": "Parameter-state lower bounds only; activations, attention buffers, CUDA kernels, checkpointing and fragmentation excluded. Not a GPU fit guarantee.",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--vocab-size", type=int, required=True)
    p.add_argument("--width", type=int, default=256)
    p.add_argument("--layers", type=int, default=8)
    p.add_argument("--heads", type=int, default=8)
    p.add_argument("--context-size", type=int, default=2048)
    p.add_argument("--ff-multiplier", type=float, default=3.0)
    a = p.parse_args()
    print(json.dumps(estimate(a.vocab_size, a.width, a.layers, a.heads,
                              a.context_size, ff_multiplier=a.ff_multiplier), indent=2))


if __name__ == "__main__":
    main()
