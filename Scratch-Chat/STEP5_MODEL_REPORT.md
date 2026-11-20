# Step 5 — Modern scratch transformer, training and measured results

## Scope and provenance

- Preserved the Step 4 original trained checkpoints and code.
- Added a second independently coded decoder-only transformer using PyTorch tensor operators only: RoPE, RMSNorm, causal scaled dot-product attention, SwiGLU, and shared input/output token weights.
- Added resumable pretraining using existing source-approved corpus/tokenizer files, optimizer state, sampler RNG state, and atomic checkpoints.
- Kept JANUS/Mindcore integration out of this stage until the model produces genuinely useful chat responses.

## Verification

- All 38 test cases passed in the Linux Python/PyTorch test environment.
- Causal isolation test: predictions for earlier tokens are unchanged by appending future tokens.
- Training tests: forward, backward, finite gradients, RoPE length preservation, exact CPU restore between interrupted and continuous runs, held-out evaluation and minimum data guard.
- Full intended architecture: 256 hidden units, 8 layers, 8 heads, 2048 positions, 4096-token vocabulary yields **7,868,672 unique trainable parameters**.
- This size was instantiated and counted, **not pretrained to general capability**.

## Actual smoke-training run

This is **not** a usable chat model. For a small proof that the modern neural architecture trains:

| Measurement | Result |
|---|---:|
| Small architecture | 148,160 parameters; 2 layers, 64 hidden units |
| Optimizer updates | 30 |
| Training tokens | 3,008 |
| Validation tokens actually predicted | 116 |
| Initial validation cross-entropy | 6.533848 |
| Validation cross-entropy after 30 updates | 5.730109 |
| Validation perplexity after training | 308.002794 |

These tiny results do not establish generalization. Multiple sentences are from a small toy dataset, and the model has not been asked to perform a chat-quality evaluation because its pretraining is nowhere near sufficient.

## Blocking requirements for a useful standalone model

1. Substantial, varied, licensed raw text corpus with independent held-out evaluation; a million tokens is a *guardrail*, not an adequate final target.
2. Broad next-token pretraining at meaningful scale, with measured validation and independent tests.
3. Supervised conversation and instruction training **after** broad pretraining, using a large, diverse, independent dataset.
4. A real prompt-by-prompt capability assessment (instruction following, multi-turn coherence, unseen factual questions, coding and reasoning), not just falling language-model loss.
5. Training hardware appropriate to the chosen parameter/data budget. The supplied environment has no GPU and cannot run multi-day pretraining as part of this chat. The user's older RX 480 is also a serious constraint for modern training frameworks.

The new system is a trainable research foundation. A capable general-purpose language model is **not yet complete**.
