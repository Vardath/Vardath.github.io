# Vardath Scratch Chat — Step 3 dataset infrastructure

**New:** [Step 3 capability report](STEP3_DATA_AND_CAPABILITY_REPORT.md).  This release contains verified WikiText importers, an optional official Hugging Face streaming source, preserved train/validation/test splits, an explicit compute estimator, and Windows launchers `16`–`20`.  **29 tests pass.** Real WikiText training has NOT been performed here; the included weights are from Steps 1–2 and are not a capable general conversational model.

The original v0.1 chat remains usable, while v0.2/v0.3 pretraining is separate. The `capability/wikitext.py` importer can use the publisher archive or stream from `Salesforce/wikitext` when the historical ZIP host blocks downloads.

---

# Vardath Scratch Chat — Step 2 Trainable Model Release

**NEW:** [Step 2 verified training report](STEP2_TRAINING_REPORT.md). This upgrade adds real BPE language-model pretraining, a tested 9.5-million-parameter configuration, resumable optimizer/checkpoint state, streaming token caches, validation/test evaluation and a trained 496K-parameter pilot checkpoint. **It is not yet a capable conversational model.** The initial v0.1 chat server still runs, but v0.2 is a base-model training path, not the existing chat API.

---

# Vardath Scratch Chat — Step 1 Capability Upgrade

**NEW:** Read [STEP1_CAPABILITY_PLAN.md](STEP1_CAPABILITY_PLAN.md) for the capability requirements, measured baseline, completed training-data/tokenizer infrastructure, installation instructions and exact next milestone. **The upgraded tokenizer is an engineering component, not a newly trained capable chat model.** All original v0.1 files and weights remain available below.

---

# Vardath Scratch Chat v0.1

**A fully local, small, genuinely trained neural chat model, implemented from first principles.**

This is **not** a wrapper around Qwen, Ollama, OpenAI, OpenRouter, llama.cpp, or any downloaded pretrained model. Its weights are trained from random initialization with the included Python/PyTorch training code. The ZIP includes weights trained on the included 51-example starter dataset so you can run it immediately.

## Crucial capability limitation

**This is an experimental toy-scale chat model, not a capable general-purpose conversational AI.** Its starter model is only **385,440 parameters**, with a **256-byte-token context**. It can reproduce several trained answers; it will make mistakes and produce gibberish outside its narrow training data. It cannot reliably research, code, reason, run JANUS, or build Faction Command. It does **not** meet the functional quality of commercial LLMs. The training examples are supplied transparently in `data/starter.jsonl`.

Training a generally capable language model *from scratch* takes substantial curated text datasets and considerably more computing power than a Windows 10 machine with an older RX 480 and modest RAM. Building the code is feasible; producing high-quality original weights locally is the hard part. This package is a working baseline for experimenting with original models, **not** a solution to JANUS's need for a strong language model.

## What's actually implemented

- Custom 3-layer causal transformer decoder (causal attention, residual layers, layer normalization, GELU MLP, embeddings).
- Original byte-level UTF-8 tokenizer, with dedicated role and end markers. No downloaded vocabulary.
- Real next-token training, with loss evaluated only for assistant response tokens, saved local weights and restartable training.
- Real autoregressive inference from the saved weights.
- CPU inference and training on Windows 10/11; no GPU dependency.
- Local interactive CLI chat, where successive messages are supplied as conversation history (within 256-token limit).
- Local **OpenAI-style chat completions** HTTP API, localhost-only (`/v1/chat/completions`, `/v1/models`, `/health`). No external network calls after PyTorch installation.
- Reproducible starter training data, source code and integrated tests.

The code uses **PyTorch for tensors and automatic differentiation**, not an externally trained model. The source for the model, tokenizer, trainer and serving API is all present in this package.

## Start on Windows

1. Extract the ZIP to `D:\VardathScratchChat` or another directory. The path can be changed.
2. Install **Python 3.11 or 3.12, 64-bit**, if it is not already installed.
3. Run **`1-Install.cmd`**. This creates a virtual environment and downloads the PyTorch CPU wheel; it does **not** download third-party model weights.
4. Run **`3-Chat.cmd`** immediately to chat using the included small starter checkpoint.
5. Run **`4-API.cmd`** to expose it on your PC. Keep the console window open while using the API.
6. Run **`6-Run-Tests.cmd`** for verification.

**`2-Train.cmd`** resets the model weights to random initialization and trains on the starter examples. It overwrites `checkpoints/starter.pt`; keep a backup if you want to preserve the supplied checkpoint.

**`5-Continue-Training.cmd`** loads the existing checkpoint and continues training (the optimizer state is restarted at each invocation). This does not give the model general knowledge without substantial additional training data.

## API

- Base URL: `http://127.0.0.1:8080/v1`
- Chat endpoint: `POST http://127.0.0.1:8080/v1/chat/completions`
- Model ID: `vardath-scratch-1` (alias `janus-local` accepted on requests)
- No API key required **because the server only binds to localhost**.
- Chat Completions JSON support: text-only `system`, `user` and `assistant` messages; `max_tokens`, `temperature`, `model`.
- **Not implemented:** streaming, tools/function-calling, embeddings, vision, audio, Responses API, authentication, remote access, token-usage accounting, structured JSON generation.
- This is not automatically connected to JANUS. JANUS's actual chat adapter would need to call this endpoint and handle the result.

Example PowerShell request:

```powershell
$body = @{
  model = 'vardath-scratch-1'
  messages = @(@{role='user'; content='what is janus?'})
  max_tokens = 100
  temperature = 0
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri 'http://127.0.0.1:8080/v1/chat/completions' -Method Post -ContentType 'application/json' -Body $body
```

## Training a different original model

1. Add conversations to a **UTF-8 JSON Lines** training file; one example per line:

```json
{"messages":[{"role":"user","content":"hello"},{"role":"assistant","content":"Hello."}]}
{"messages":[{"role":"user","content":"what is code?"},{"role":"assistant","content":"Code consists of instructions executed by a computer."}]}
```

2. Activate the installed Python environment and train:

```cmd
.venv\Scripts\python.exe -m vardath_chat train --data data\yourdata.jsonl --out checkpoints\new.pt --steps 2000 --width 128 --layers 4 --heads 4 --context 256
```

3. Serve new trained weights:

```cmd
.venv\Scripts\python.exe -m vardath_chat serve --weights checkpoints\new.pt
```

You can adjust depth, model width, context size, number of examples and training steps. Training more parameters from scratch **does not** automatically produce better reasoning. A sufficiently large, diverse, legally sourced corpus and expensive training regime would be required. The current tokenizer has **one token per UTF-8 byte**, meaning this model's 256-token context corresponds to at most about 256 English characters.

## Testing and provenance

The package includes model weights created by training the included model architecture on the transparent `data/starter.jsonl` corpus. The Python unit/integration tests cover the tokenizer, response-only training targets, causal attention, loading the checkpoint, generation and actual local HTTP server responses.

No pretrained weights or proprietary training dataset are included. No license claim is made over upstream PyTorch code; PyTorch remains subject to its own license. The original application source here can be modified and experimented with; before commercial use, evaluate all dependencies and data provenance.

## JANUS integration: important boundary

JANUS's 11-core/Fano cognition remains separate from this model. For an actual JANUS integration, inspect JANUS's local chat transport and adapt it to make `POST /v1/chat/completions` requests; do not replace the Fano core with this tiny language model. The README is intentionally candid: installing this project **does not** turn JANUS into an autonomous coding agent or supply general-purpose intelligence.

---

# Step 4 — Standalone instruction-training milestone

**User-defined scope:** make the language model work independently first. No JANUS integration, no release activities.

Step 4 adds masked-answer supervised chat training (`capability/instruct.py`) with restartable optimizer state, separate train/validation/test measurements, early stopping, best-checkpoint retention and local multi-turn chat. The supplied checkpoint was trained entirely from random initialization on the 51 original toy dialogs, with 35/8/8 train/validation/test examples. It is demonstrably **not yet capable of normal chat**. Read [STEP4_TRAINING_REPORT.md](STEP4_TRAINING_REPORT.md) for real generated outputs and results.

Windows: `21-v04-Prepare-Chat-Pilot.cmd`, `22-v04-Train-Chat-Pilot.cmd`, `23-v04-Evaluate-Chat.cmd`, and `24-v04-Chat-Pilot.cmd`. The ZIP already includes the best pilot checkpoint, so run evaluation/chat directly if you only want to inspect it. Do not re-train over an existing checkpoint accidentally.

**Remaining language-model work:** obtain and train on a substantial broad text corpus, increase model capacity only when compute/data justify it, instruction-tune the actually pretrained base model, and demonstrate satisfactory responses to previously unseen questions. Number of additional development iterations cannot be accurately forecast without usable training data and compute.

## Step 5: new standalone neural architecture and resumable training

`capability/modern_model.py` implements a **second, independent from-scratch transformer architecture**, using causal self-attention with rotary positional embeddings (RoPE), RMSNorm and SwiGLU. No weights or tokenizer were downloaded from a pretrained model. Older models and checkpoints are unchanged and remain loadable by their original tools.

`capability/modern_train.py` trains the new architecture from random initialization on the existing tokenizer and prepared corpus, with persistent optimizer and sampling states. It deliberately refuses to start the normal-sized run unless at least 1,000,000 **training tokens** are present. This is only a minimum safety guard, **not enough data for strong conversation**. A typical general-purpose language model needs far more data and compute.

- `25-v05-Train-Modern.cmd`: 256-width, 8-layer, 8-head model (about 7.9 million parameters when trained with a 4096-token vocabulary), 2,048 context allocation, 256-token training windows, CPU. Before running it, prepare an appropriately licensed text corpus. The bundled 51-record sample is intentionally rejected.
- `26-v05-Evaluate-Modern.cmd`: independently evaluate the held-out validation and test sets after training.
- `python -m pytest -q`: run all automated tests including modern architecture, causal isolation, gradients, checkpoint recovery and minimum corpus safeguards.

**Do not treat the smoke checkpoint as a useful conversational model.** `v05-modern-smoke.pt` is only 148,160 parameters and has seen 3,008 training tokens. The measured loss reduction on 116 held-out tokens proves the update mechanism works, not that it can converse. The 7.9M configuration was instantiated and parameter-counted, not fully trained. See `STEP5_MODEL_REPORT.md`.

JANUS integration is deferred until actual free-form conversation demonstrates the language model is useful. The recovered Mindcore application is not part of this package.
