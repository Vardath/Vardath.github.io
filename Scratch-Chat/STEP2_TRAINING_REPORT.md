# Vardath Scratch Chat — Step 2: Trainable Language Model

**Development state:** Step 2 engineering complete and locally tested. **General-purpose AI capability: not achieved.**

This release builds directly on Step 1's source-aware corpus preparation and original byte-BPE vocabulary. The v0.1 model, its chat API, and original trained weights are preserved. No downloaded pretrained weights, remote inference, or model-provider API is used.

## Delivered components

- `capability/pretrain.py`: genuine next-token language-model pretraining from random initialization, using the existing custom causal transformer and the new original ByteBPE vocabulary. Chats use actual role token IDs; ordinary text uses regular text IDs.
- Configurable decoder with a 1,024-token **architectural capacity** by default, adjustable layers, width, heads, dropout and training sequence length. A 384-wide, 5-layer, 6-head configuration with vocabulary 646 has **9,514,368 parameters**.
- Context-window batch sampling over continuous token streams, next-token cross-entropy, AdamW, gradient accumulation, gradient clipping, cosine LR decay and warmup.
- Training restart restoring **model, optimizer, sampler RNG, PyTorch RNG and Python RNG states**; the original immutable training settings, corpus hashes and tokenizer checksum are validated before resuming. Checkpoints are written atomically.
- Actual validation and test loss/perplexity, with separate test split not used in training.
- `capability/token_cache.py`: bounded-memory pretokenization into 32-bit token files, memory-mapped via PyTorch. SHA-256 and source hashes reject modified or stale caches. Large token streams need not be materialized as Python lists.
- Optional mixed precision on supported CUDA accelerators; CPU is the tested default. AMD RX 480 GPU training was not verified and is **not** promised.
- `10`–`15` Windows command launchers for evaluation, sample generation, cache creation, larger training and regression tests.
- Trained **496,032-parameter v0.2 pilot** under `checkpoints/v02-pilot.pt`, plus source and tests. This pilot was trained with 64-token sequences; although its model *can represent* 1,024 positions, the farther positions have **not been learned**.

## Measured results, not capability claims

| Measurement | Result |
|---|---:|
| Full-size configuration | 9,514,368 parameters |
| Full-size smoke run | 2 actual CPU optimizer steps |
| Pilot model | 496,032 parameters |
| Pilot training | 120 optimizer steps, 3,008 training tokens |
| Pilot train loss (step 1 → step 120) | 6.4744 → 3.3845 |
| Pilot validation loss | 3.6020 |
| Pilot held-out test loss | 3.9311 |
| Pilot held-out test perplexity | 50.9607 |
| Pilot generation, `JANUS is` | ` and coi, is weights a not exit.` |
| Suite | 20 automated tests, all passed |

The decreasing loss demonstrates parameter learning. The generated text demonstrates the **remaining inadequacy**. The pilot is not ready to chat intelligently, write books, code or operate JANUS. Its evaluation corpus is tiny (3 held-out test records), and perplexity is not a reliable overall language-quality estimate from such few examples.

**10M checkpoint not included:** An AdamW training checkpoint for the 9.5M model occupies approximately 109 MB. After only two steps, these weights are not useful. The training system can create such a checkpoint on demand *after* sufficient licensed data is supplied. We do not package meaningless large weights simply to imply progress.

## How to use on Windows

1. Extract the ZIP to a **new folder**. Do not overwrite previous releases or JANUS.
2. Install Python 3.11 or 3.12 if not installed, then run `1-Install.cmd` (installs CPU PyTorch; does not download another pretrained model).
3. Optionally run `15-v02-Run-All-Tests.cmd` (the complete suite).
4. Run `10-v02-Evaluate-Pilot.cmd` to measure held-out test loss with included weights.
5. Run `11-v02-Generate-Pilot.cmd` to inspect the current model's limited text generation.
6. To add training documents, edit `data/corpus/manifest.json` and include only content you have a right to train on, with `permission_to_train: true`. The old starter data is a smoke corpus only.
7. Rerun `7-Prepare-Corpus.cmd` to prepare the splits and train a new original BPE vocabulary. **Changing a tokenizer invalidates the existing v0.2 pilot checkpoint's vocabulary mapping.** To evaluate that pilot, keep its original tokenizer; to train new weights, use a distinct checkpoint filename.
8. Run `12-v02-Token-Cache.cmd` to generate verified, memory-mapped pretraining token files.
9. Run `13-v02-Train-10M.cmd` to start training from random weights. It will reject the bundled corpus because it contains fewer than **1,000,000 train tokens** and **10,000 validation tokens**. These thresholds are an *anti-waste safeguard*, NOT sufficient to create an intelligent model.
10. For a resumed checkpoint, run `14-v02-Resume-10M.cmd` or issue a command with the same configuration and `--resume --steps N`, where N is the desired *total* optimizer steps. LR schedule and corpus must match. Never delete or overwrite an existing checkpoint without a backup.

### Example command for a small **new** research run

```powershell
.venv\Scripts\python.exe -m capability.pretrain train --corpus data\prepared --tokenizer data\tokenizer-bpe.json --token-cache data\token-cache --output checkpoints\my-experiment.pt --width 96 --layers 3 --heads 4 --model-context 1024 --seq-len 64 --batch 2 --grad-accum 2 --steps 200
```

This is **not** equivalent to creating a capable 10M model. It is for verifying a new corpus and configuration.

### Important resumed training semantics

`--steps` means the **total optimizer steps desired**. For example, after a 1,000-step run, `--resume --steps 2000` performs steps 1,001–2,000. The cosine LR schedule is independently fixed via `--decay-steps` and cannot be silently reset when resuming.

## Remaining work before capability

**Step 3 — large corpus and compute:** obtain a suitably diverse, licensed, curated dataset with independent held-out tasks. Scale tokenizer training beyond the current slower reference implementation. Profile CPU and GPU alternatives, cost and memory limits. Substantial general-language ability typically requires massively more training tokens than the present 3,008. The 9.5M model is a training-system proof, not a sufficient general assistant architecture.

**Step 4 — instruction fine-tuning and evaluation:** add correctly permissioned instruction conversations, supervised assistant-only loss, multi-turn QA, coding tests, writing quality assessment, uncertainty and command-following benchmarks. Only claim a specific capability if independent tasks demonstrate it.

**Step 5 — JANUS adapter:** add a separate local endpoint that uses the *new* vocabulary and weights, then integrate it with JANUS's existing language interface without replacing its 11-core Fano system. The existing v0.1 endpoint remains available; the v0.2 base model is **not yet wired to the chat API**. Do not confuse language generation with JANUS's persistent cognitive architecture.

## Limitations and security

- A 1,024-token model capacity doesn't imply that those positions have been trained. Use longer training sequences only with sufficient data and compute.
- Held-out loss on a handful of documents is not a convincing generalization benchmark.
- Resuming exactly on CPU is tested; exact equality across different devices, different PyTorch builds or nondeterministic GPU kernels is not guaranteed.
- All commands use local files and no cloud APIs. `1-Install.cmd` uses the internet to install the PyTorch library only.
- Checkpoints should be loaded from trusted sources. Training corpora should exclude credentials, private information and copyrighted material without authorization.
