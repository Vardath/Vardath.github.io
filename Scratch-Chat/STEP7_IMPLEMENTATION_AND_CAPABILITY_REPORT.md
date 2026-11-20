# Vardath Scratch Chat — Step 7

**Date:** 20 November 2026  
**Scope:** Standalone language-model development only. **DeepThorT is the autonomous application, not the model.** No integration with DeepThorT or JANUS was undertaken.

## Result

The model remains **NOT READY** as a useful independent general-purpose conversational AI. An OpenAI-compatible local API and a direct-response probe now operate using real locally trained modern-model weights. The training engine now supports memory-mapped token caches and optional CUDA devices/precision, enabling experiments with larger independently licensed corpora without loading every token into RAM.

## Actual evidence

- Python tests: **54 passing** (from Step 6 baseline of 46).
- A live request against the **actual** modern-instruction checkpoint through a running local server returned HTTP 200. The returned message was repetitive fragments; the server is functional, but the language model does not converse reliably.
- The checkpoint continued from **150 to 300** optimization steps on the original toy instruction dataset (35 training dialogs; 8 validation and 8 test dialogs). The held-out validation answer-token loss decreased from approximately **4.6944** at 150 steps to **4.4064** at 300 steps, but that did **not** produce coherent replies on six unseen prompts.
- **Six of six** independently generated sample replies were flagged as blank, repetitive, or extremely short. Compare `reports/v07_current_pilot_quality.json` with `reports/v07_continued_pilot_quality.json`.
- Repeatable CPU checkpoint recovery with the memory-mapped corpus was confirmed by comparing all model parameter tensors against an uninterrupted run.

These metrics are *not* an intelligence score. A lower next-token loss on eight held-out dialogs is insufficient to claim conversational ability.

## Step 7 code

- `capability/modern_chat.py` — greedy and sampled inference; top-k / top-p / repeat-penalty controls. Output is still the model's own tokens, without a rules-based response substitute.
- `capability/modern_server.py` — `GET /health`, `GET /v1/models`, `POST /v1/chat/completions`, local-only binding, exact generated-token accounting, malformed-request checks. No internet/API keys needed at inference time.
- `capability/chat_quality.py` — direct unseen-question generated-output probes, error/blank/repetition flags, human-reviewed JSON report.
- `capability/modern_train.py` — memory-mapped training tokens (`--token-cache`), `--device cpu|auto|cuda`, optional CUDA AMP (`--amp bf16|fp16`), checkpoint recovery and held-out evaluation.
- `tests/test_v07_standalone.py` — new coverage for generation, server, cache, sampler, invalid requests and recovery.

## Windows commands

1. `1-Install.cmd` installs Python dependencies to the project virtual environment.
2. `30-v07-Run-Modern-Chat-API.cmd` starts the local experimental API at `http://127.0.0.1:8080/v1`.
3. `31-v07-Measure-Actual-Chat.cmd` writes direct-output diagnostics into `reports/v07_actual_chat.json`.
4. `27-v06-Get-Real-Training-Text.cmd` attempts to download verified WikiText-2 data on a computer with internet access. The data source may be blocked; inspect errors. Prepare its tokenizer and token cache with `capability.cli tokenizer` and `capability.token_cache` before model training.
5. Once a substantial licensed dataset exists, train the modern model with `python -m capability.modern_train train --corpus <prepared-dir> --tokenizer <trained-tokenizer.json> --token-cache <token-cache-dir> --checkpoint checkpoints/v07-trained-base.pt --steps 2000 --context-size 2048 --seq-len 256 --width 256 --layers 8 --heads 8 --batch 2 --grad-accum 4 --min-train-tokens 1000000 --device cpu`. This is an **example of how to start training**, not a claim it will produce a capable model within 2,000 steps. Exact training requirements must be assessed against data and hardware.

**Warning:** Your older Radeon RX 480 is unlikely to support contemporary PyTorch CUDA; CPU mode is the supported fallback. GPU support is for environments where the appropriate PyTorch device backend exists; it is not a claim that this Radeon is supported.

## Outstanding work before 'ready'

- Obtain a significantly larger, high-quality, traceably licensed training dataset in addition to WikiText-2. This environment cannot fetch it, so no real large-scale pretraining occurred here.
- Train a much larger model from random initialization with sufficient varied tokens/compute. Measure held-out learning, not only memorization of small dialogs.
- Instruction-tune that genuinely pretrained model on broad high-quality conversational examples with separate independent test sets.
- Demonstrate coherent answers, multi-turn memory, factual generalization and instruction-following on unfamiliar prompts via direct generation. Do not claim readiness from API/test-suite passes alone.

**No DeepThorT application integration, no release validation or packaging as a commercial product is included.**
