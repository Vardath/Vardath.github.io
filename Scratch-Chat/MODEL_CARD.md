**Step 3 status (20 November 2026):** Added a verified data-ingestion and compute-estimation pipeline. No general-purpose language capability achieved. WikiText large-scale training has not run here. See [STEP3_DATA_AND_CAPABILITY_REPORT.md](STEP3_DATA_AND_CAPABILITY_REPORT.md).

# Vardath Scratch Chat — Model Card

**Model type:** original decoder-only transformer, randomly initialized and trained using the supplied Python code. No third-party pretrained checkpoint, pretrained tokenizer, training API, or inference engine was used.

**Architecture:** 385,440 trainable parameters, 3 transformer layers, 96 hidden units, 4 attention heads, 256 byte-tokens of context, layer normalization, GELU feed-forward blocks, shared token-input and output embeddings.

**Tokenizer:** 256 raw UTF-8 bytes plus six local special tokens (BOS, USER, ASSISTANT, EOS, SYSTEM, PAD). The tokenizer is not BPE and is inefficient for Unicode and long messages.

**Included dataset:** 51 hand-authored pairs in `data/starter.jsonl`. No general-language pretraining corpus was supplied. Data is intentionally transparent and not representative of natural conversation.

**Training:** Saved checkpoint trained for a total of 1800 update steps, from random weights, with intervening resumed training (optimizer state reset between phases). This is supervised answer-token training, **not broad next-token pretraining** over a general corpus. Random seed 17.

**Demonstrated held-in-training responses (greedy decoding):**

- `hello` -> `Hello. What would you like to discuss?`
- `what is your name?` -> `I am Vardath Scratch Chat, a small local model.`
- `what is janus?` -> `JANUS uses Fano-inspired specialist cores for reasoning and memory.`
- `what is a transformer?` -> `A transformer predicts tokens using attention and learned features.`

**Observed limitations:** For unseen requests, such as `how do airplanes fly?`, it produces nonsensical text. Even some training questions contain errors. Those are genuine failures, not hidden by a retrieval fallback. No rigorous held-out evaluation has been conducted.

**Not suitable for:** unsupervised project coordination, coding, online research, factual QA, acting as a strong JANUS language backend, or any safety-critical decisions. A large, diverse, legal training corpus and much stronger compute would be necessary to make an original model genuinely useful.

**Intended use:** education, research, smoke-testing the tokenizer/training/inference/API stack, and experiments with the architecture or with new local datasets. This baseline proves that the entire model lifecycle functions, not that high-quality general language abilities have been achieved.

**Internet use:** The included program performs no external model calls. Installation uses the internet to download Python/PyTorch where necessary; subsequent training, generation and API service are local.


---

## Step 2 (v0.2) model development addendum

The included `checkpoints/v02-pilot.pt` has 496,032 original randomly initialized-and-trained parameters with a 646-token learned tokenizer, 1,024-position model allocation but only 64-token training sequences, and 120 updates on 3,008 training tokens. It is not aligned to follow instructions. Real held-out test cross-entropy was 3.9311 (test perplexity 50.96, 144 next-token predictions). It generates malformed answers on unfamiliar prompts. The full 9,514,368-parameter architecture was smoke-tested for two optimizer steps but its large, essentially untrained checkpoint was not distributed. Do not deploy either as an authoritative assistant.

The original v0.1 checkpoint remains separate and usable. See `STEP2_TRAINING_REPORT.md`.

## Step 4: independent supervised chat training

The best included v0.4 pilot checkpoint has 496,032 original parameters, trained from random initialization on 35 toy dialogs with best held-out validation loss at step 100. Eight validation and eight test dialogs were not included in this supervised training run. The actual responses still contain repeated nonsensical words. **Do not describe this model as a capable general chat engine.** Neither JANUS integration nor release preparation is part of the active scope. See `STEP4_TRAINING_REPORT.md`.

## Step 5 independent neural architecture

New model code, resumable training and measured smoke results are documented in [STEP5_MODEL_REPORT.md](STEP5_MODEL_REPORT.md). The bundled `v05-modern-smoke.pt` is a fresh random-initialized test model trained for just 30 updates. **It does not provide useful chat**, and the 7.9M configuration has not been broadly pretrained. Original and older fine-tuned checkpoints are preserved; no API, JANUS or Mindcore integration has been attempted.
