# Mandatory lexical screening before dialogue pilot — 2026-11-23

Baseline: GitHub Actions run [45093092918](https://github.com/Vardath/Vardath.github.io/actions/runs/45093092918) completed successfully (unit-tests job), predating these changes.

Changes:
- `capability/run_dialogue_pilot.py` now calls the existing indexed word-trigram cross-split Jaccard audit after manifest and exact-content verification but **before** creating output directories, fitting a tokenizer or training.
- Default threshold 0.8; `--duplicate-threshold` is explicit and must be in (0,1]. Any findings stop training; a passing report is recorded in `pilot_report.json`.
- `tests/test_dialogue_pilot_contamination.py` verifies the fail-closed path and absence of output allocation.

Commits: `f5e8744d47beba611a679445b50d76d16bff62cd`, `2819af43b2a78990efd2bf56ea9c86e490585c0f`.

This is lexical screening, not semantic paraphrase detection or licensing/privacy approval. Existing Dolly data remain quarantined. No training, checkpoint, independent quality evaluation, or actual DeepThorT application integration is claimed for this pass. Push-triggered source CI for these commits has not yet been inspected; do not mark it green without completed job evidence.

Next: verify source CI; acquire/review and pin licensable dialogue with privacy audit; run bounded original-weight training and real held-out JSONL acceptance. GitHub CPU is not a substitute for GPU pretraining.
