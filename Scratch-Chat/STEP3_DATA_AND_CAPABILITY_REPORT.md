# Vardath Scratch Chat — Step 3: real text corpus and compute planning

Date: 20 November 2026. **Status: data pipelines tested offline; real WikiText download and large-scale training are NOT completed.**

## What was implemented

- `capability/wikitext.py`: import the publisher's raw WikiText-2 or WikiText-103 ZIP, verifying published archive length and SHA-256; alternatively stream the official `Salesforce/wikitext` dataset from Hugging Face to bypass the historical archive host's 403 errors.
- Preserve the official train/validation/test split at the *article level*. No randomly redistributing WikiText validation or test content into training. Reject exact duplicate articles shared across different splits.
- Retain provenance, source name and Creative Commons BY-SA 4.0 metadata in the JSONL output. Training text is not committed to the public website repository.
- Use the existing from-scratch ByteBPE tokenizer, memmapped token-cache, and v0.2 resumable trainer. No pretrained model weights are introduced.
- `capability/capacity.py`: transparent parameters/tokens/FLOP/state-memory estimator, with optional measured local training throughput. This is an approximation, NOT a predicted model-quality score.
- Windows entry points `16`–`20` for installing optional data tools, importing, tokenizer preparation, pilot training and compute estimates.
- **29 automated tests pass**, including 7 synthetic-corpus ingestion tests. No actual WikiText evaluation perplexity is claimed.

## Starting the WikiText pilot on a Windows PC

1. Run `1-Install.cmd` for the original source model dependencies.
2. Run `16-v03-Install-Dataset-Tools.cmd` to install Hugging Face `datasets`.
3. Run `17-v03-Import-WikiText.cmd`. It streams the official `wikitext-2-raw-v1` dataset into `data/wikitext2/prepared`. It needs internet only during the initial data download.
4. Run `18-v03-Prepare-WikiText-Tokenizer.cmd`. Tokenizer training uses **training text only**; creates token caches for all splits.
5. Run `20-v03-Capacity-Estimate.cmd` to inspect the approximate compute demands. On an older CPU, choose an appropriately small training configuration.
6. Run `19-v03-Train-WikiText-Pilot.cmd` **only when ready for a potentially long local run**. It creates a separate `v03-wikitext-pilot.pt` checkpoint. It does not replace the v0.1 chat weights, and does not yet provide competent general-purpose conversation.
7. Resume an interrupted pilot using `python -m capability.pretrain train` with the same arguments plus `--resume` and a larger total `--steps` value. All other immutable settings and datasets must remain unchanged.

To import a ZIP manually instead, use:

```bash
python -m capability.wikitext --source zip --archive data/downloads/wikitext-2-raw-v1.zip --out data/wikitext2/prepared
```

The verified ZIP SHA-256 is `ef7edb566e3e2b2d31b29c1fdb0c89a4cc683597484c3dc2517919c615435a11`. Some installations cannot download the old ZIP server; default to the official Hugging Face loader.

## Compute example (not a forecast)

For a **9,514,368 parameter** dense transformer processing **10,000,000 training tokens**, the crude `6 × parameters × tokens` scaling gives approximately **5.71×10¹⁴ arithmetic operations**, *excluding* overhead, attention costs, validation and data processing. This is only ~1.05 tokens per parameter; it is not a recipe for useful instruction following. Measure actual tokens/sec on the target PC before attempting longer runs. A faster GPU or hosted training accelerator may be needed for a generally capable model.

## Remaining milestones — not a promise of capability in four more steps

1. **Stage 4 — Real pretraining:** acquire broader training data with appropriate permissions, scale tokenizer/trainer, train, and report held-out benchmarks and actual cost. May require much more capable hardware than the RX 480 / CPU configuration.
2. **Stage 5 — Instruction alignment:** high-quality instruction/chat/code supervision and rigorous out-of-distribution task tests; do not judge capability by training loss alone.
3. **Stage 6 — JANUS integration:** connect to JANUS's actual chat adapter, test interaction with Fano cores and memory, and verify latency/availability.
4. **Stage 7 — Release qualification:** reproducibility, model quality, security, licensing, Windows installers, hardware benchmarking and actual user acceptance tests.

There are **four broad engineering milestones remaining** after Step 3. However, no finite number of programming steps guarantees a capable foundation model: data scale, training compute and measured conversational ability are the limiting factors. No readiness date should be claimed. The model is ready for general use **only after** demonstrating useful competence on previously unseen conversational, coding, reasoning and instruction-following tasks.

## Licence and data sources

- Official WikiText page: https://huggingface.co/datasets/Salesforce/wikitext
- Publisher archival data: https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-2-raw-v1.zip
- License: https://creativecommons.org/licenses/by-sa/4.0/ (CC BY-SA 4.0). Attribution, share-alike and other obligations need review before commercial distribution.
- Source credit: *Pointer Sentinel Mixture Models*, Stephen Merity, Caiming Xiong, James Bradbury and Richard Socher (2016).

The Step 3 code can prepare these datasets. **It has not trained a large model on them in this environment**, because data download was unavailable. The bundled checkpoints remain those of the earlier starter/pilot experiments.
