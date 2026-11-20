# Vardath Scratch Chat — Capability Roadmap & Step 1 Execution Record

**Status: Step 1 completed as an engineering foundation. This model is not yet capable.**

This project deliberately starts from random weights and original tokenizer code. No LLM weights, external chat APIs, or pretrained vocabularies are imported. PyTorch is used for matrix operations and automatic differentiation.

## Baseline diagnosis (v0.1)

- 385,440 parameters, trained on 51 manually written examples.
- 256 UTF-8 byte context means only ~256 ASCII characters per context window.
- Assistant-targeted training but no broad language pretraining and no independent evaluation.
- No genuine capacity to generalize reliably to coding, research, books, tool-calling or complex discussion.
- Windows CPU training only; the user's older AMD RX 480 has no verified official PyTorch/ROCm training support.
- In eight newly authored, unseen question prompts, the old checkpoint included none of the expected diagnostic terms. This **0/8 keyword diagnostic is not a calibrated accuracy metric**, but it demonstrates why remembering 51 answers is not general competence. Read `reports/v01_unseen_baseline.json` for every exact generated response.

## What is required to produce a capable original model

**1 — Data and tokenizer (this release)**

Create a provenance-aware corpus ingestion and held-out evaluation system, then train an original byte-pair tokenizer on training text only. Large-scale text acquisition must have explicit permission/rights; do not blindly scrape files. Track deduplication, source/license, and document grouping. Evaluate tokenizer efficiency on data it was not trained on.

**2 — Scalable model and real pretraining (next)**

Replace toy-training assumptions with next-token pretraining over long continuous documents; support larger contexts, packed batches, a scalable tokenizer/vocabulary, optimizer+random-state checkpoint/resume, gradient accumulation, LR schedules, mixed precision where supported and actual held-out loss/perplexity. Start with ~10M parameters to validate training stability. Do not call this a capable assistant yet.

**3 — Serious corpus and compute**

Acquire a broad, well-filtered and appropriately licensed corpus covering language, reasoning, mathematics, programming, science, history, fiction and conversational writing. Record every source. A serious general-language experiment may involve hundreds of millions or billions of tokens, not fifty dialogues. A 100-million-parameter model trained on roughly 2 billion tokens entails ~1.2e18 training FLOPs under the rough 6*N*D estimate, excluding overhead and evaluation; a 1-billion-parameter model on ~20 billion tokens entails ~1.2e20 FLOPs. These are illustrations, *not* guaranteed quality thresholds, and a modest CPU-based desktop is not a plausible fast training platform for this scale. Feasibility and hardware support must be measured before selecting a target.

**4 — Instruction and multi-turn alignment**

After usable pretraining, perform supervised instruction fine-tuning on permitted high-quality instruction/code conversations. Create explicit tests for factual QA, logic, writing, coding, refusals/uncertainty, long-context use and following prohibitions on unauthorized design changes. Run JANUS-specific integration tests. A model must actually pass tests, not simply have weights or a chat window.

**5 — Deployment as JANUS language service**

Connect the independently evaluated model to JANUS's existing chat adapter, without replacing or short-circuiting the original Fano/11-core cognitive architecture. Maintain an OpenAI-compatible loopback HTTP API with clear versioning, tool-call contracts if added, and bounded memory use.

## Step 1 delivered and verified

- A new `capability/corpus.py` ingestion pipeline reads only manifest-listed UTF-8 `.txt`, `.md` and `.jsonl` inputs.
- Every source requires provenance, a stated license and `permission_to_train=true`.
- Records receive SHA-256-based identifiers, exact duplicate removal and group-stable train/validation/test partitions. A group is never split across sets; text is split before later chunking.
- `capability/bpe.py` implements original reversible byte-pair tokenization, saving merge tables as plain JSON. No pretrained tokenizer is downloaded.
- It uses training data only to learn its 384 merges; held-out validation and test sets are never seen by the tokenizer-training operation.
- A transparent pilot dataset is bundled: 51 old user-assistant dialogues plus one newly written original explanatory document. It is a **pipeline smoke test only**, not training data sufficient for a capable LLM.
- Results: 52 unique records, 46 training, 3 validation, 3 test. The 646-entry vocabulary (256 byte tokens + 384 learned merges + 6 special role tokens) achieved about **2.20 bytes/token on train, 2.03 on validation and 2.08 on test**. The old byte tokenizer always uses one token per UTF-8 byte.
- The new tokenizer **does not yet power the existing v0.1 checkpoint**. Reusing the old weights with different token IDs would be incorrect. Wiring this tokenizer into a new model and doing pretraining is Step 2.
- All 14 unit/integration checks passed, including old API and new tokenizer/corpus tests.

## Run Step 1 on Windows

1. Extract the ZIP to a NEW directory, rather than overwriting the old working v0.1 project.
2. Run `1-Install.cmd` if the project has no `.venv` yet. This installs PyTorch and its Python dependencies, not weights.
3. Run `7-Prepare-Corpus.cmd`. It will generate `data/prepared/train.jsonl`, `validation.jsonl`, `test.jsonl`, `provenance_report.json`, `data/tokenizer-bpe.json`, and held-out tokenizer statistics.
4. Run `9-Run-All-Tests.cmd` to test the original API and new data infrastructure.
5. Run `8-Evaluate-v01.cmd` for the existing model's responses to unseen questions.

## Add your own permitted training files

Put files under `data/corpus/source/` and add a manifest entry in `data/corpus/manifest.json`:

```json
{
  "path": "source/my_notes.md",
  "source": "My original notes",
  "source_url": "local file (self authored)",
  "license": "Original work owned by contributor",
  "permission_to_train": true
}
```

Remember to add a comma between entries in the `sources` array. Supported inputs: `.txt`, `.md`, `.jsonl`. JSONL records may contain `{"text":"..."}` or `{"messages":[{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}`. For related documents/conversations set the same `group` field so they cannot leak between splits.

Do not add private credentials, passwords, account tokens, personal records or other secrets. The pipeline does *not* perform automated copyright verification; the `permission_to_train` field is a declaration, not legal proof.

## Development safeguards

- The included starter checkpoint remains byte-tokenized; original chat and API commands continue to load it unchanged.
- Keep validation/test records out of training and tokenizer fitting.
- Re-run regression tests after every model/format change.
- Do not claim capability based on training loss alone: held-out real task performance is required.
- Never use pretrained weights or tokenizers if the project constraint is an original model trained from scratch.
- Never confuse language-model performance with autonomous JANUS task execution, which is a separate system.

## Next actionable milestone

Implement a v0.2 base-model pretraining path compatible with the new BPE tokens, a 1K-4K token context, proper continuous-text next-token training and exact optimizer-state resume. Train a ~10M-parameter proof-of-learning on licensed corpus, measure held-out perplexity and unseen generation against the v0.1 baseline. Do not attempt a billion-parameter CPU training run on the user's PC without profiling the actual hardware.
