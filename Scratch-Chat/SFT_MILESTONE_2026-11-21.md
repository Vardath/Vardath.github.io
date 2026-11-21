# Scratch Chat — assistant-only SFT milestone (2026-11-21)

Verified before changes: GitHub Actions source tests run [44886766002](https://github.com/Vardath/Vardath.github.io/actions/runs/44886766002) completed successfully for commit 66d6876. This was a source-test result, not a conversational acceptance result.

This pass introduced `capability/dialogue_sft_train.py`, a bounded CPU pilot consuming tokenizer-aligned assistant labels, applying assistant-only causal loss to a randomly initialized ModernScratchTransformer, validating held-out assistant loss, and writing a resumable checkpoint with model/optimizer/RNG state and input SHA-256 bindings. The companion unittest smoke tests cover supervision validation, resume and changed-training-data rejection.

**Not established:** successful new CI, successful training on an admitted external corpus, independent multi-turn competence, tool-use competence, GPU access, or production DeepThorT readiness. No pretrained weights were imported. No Shakespeare experiment was started.

**Next:** verify source CI; exercise a bounded end-to-end admitted-dialogue export/tokenize/train run; ensure real corpus scale and license documentation; measure independent conversation and JSON-line tool-use integration. CPU GitHub Actions is for smoke/pilot runs only.

## Follow-up: held-out integrity (2026-11-21)

Verified source-test GitHub Actions run [44892599461](https://github.com/Vardath/Vardath.github.io/actions/runs/44892599461): unit-tests completed successfully. Inspection found the SFT smoke test used identical train and validation rows, which made its held-out loss misleading. The SFT runner now rejects exact train/validation input-ID sequence overlap and the smoke test uses a disjoint validation example plus a contamination rejection assertion. Commits: c509838 and f1846b0. This is an exact-sequence safeguard only; near-duplicate/semantic screening remains a corpus-admission responsibility. No external dialogue corpus, GPU training, independent conversation score, or DeepThorT acceptance is claimed. Follow-on source CI from these pushes remains to be verified.
