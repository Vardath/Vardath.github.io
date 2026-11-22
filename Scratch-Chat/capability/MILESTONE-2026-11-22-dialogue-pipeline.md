# Scratch Chat dialogue pilot pipeline — 2026-11-22

## Verified baseline
GitHub Actions source tests run [44971029632](https://github.com/Vardath/Vardath.github.io/actions/runs/44971029632), head d936777231f8362b3adb78094cdcf0f3b56b52e8, completed successfully at 2026-11-22 01:21 UTC. This predates the commits below.

## Changes
- Added capability/run_dialogue_pilot.py: single entry point that refuses unapproved manifests, checks split hashes and exact leakage, serializes all splits, fits ByteBPE on train only, produces assistant-only labels, trains independently initialized ModernScratchTransformer on train only, evaluates validation loss and saves a checkpoint plus provenance report. Test is excluded from optimization and selection.
- Added tests/test_dialogue_pipeline.py for missing/unapproved provenance and non-overwrite behavior.
- The workflow's test_dialogue*.py pattern includes the new regression tests; push commits trigger bounded source tests.

## Not yet demonstrated
No real external corpus was downloaded, licensed, approved or trained in this change. The existing source manifest validator requires explicit approval but cannot independently establish licensing or privacy. The pipeline has not been run end-to-end on an approved corpus. The current trainer rejects sequences longer than context_size instead of packing or chunking them, so large/long dialogue sources may fail. ByteBPE tokenizer and model size need capacity benchmarking on GPU. Checkpoint persistence in a local output directory is not equivalent to uploading a reproducible Actions artifact. Independent multi-turn/tool-use and actual DeepThorT application JSONL acceptance remain required. No pretrained weights were substituted.

## Next gate
Source and pin a suitable permissively licensed multi-turn dialogue dataset; record URL, immutable revision, license, attribution, privacy/moderation review and raw/split hashes. Run admitted pipeline on a bounded pilot, archive checkpoint and exact config, then run independent conversation and DeepThorT integration tests. Do not claim conversation capability from training loss alone.
