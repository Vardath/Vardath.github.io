# Scratch Chat milestone — 2026-11-23 — assistant turn termination

Verified preceding source-test run 45053687987: unit-tests job completed successfully. This predates the commits below.

**Defect:** Dialogue serialization supervised only assistant response content, excluding the assistant `<|im_end|>` turn terminator. A model trained this way receives no direct target for learning when to stop speaking, although the DeepThorT bridge expects this marker. This is a training/serving mismatch, not a cosmetic formatting issue.

**Change:** `dialogue_format.serialize` now records explicit assistant-termination spans while preserving original content-only spans for compatibility. `dialogue_labels.encode_assistant_labels` validates and supervises those exact marker bytes, leaving user/system text masked. Added a dedicated regression suite and CI inclusion.

**Commits:** 8f14aea, 24f7113, abdbbfe, 237d068.

**Verification:** GitHub connector confirmed commits; follow-on push CI is not yet independently confirmed. No external Dolly data admitted, no model training, no quality score and no DeepThorT live-app acceptance claimed. Existing checkpoint formats remain independent random-weight Scratch Chat artifacts. New labels change training targets, so previously produced labeled data/checkpoints must not be treated as equivalent to this revision.

**Next:** Verify CI; audit dataset licensing and privacy for admission; regenerate labels and train an original-weight pilot with reproducible source hashes; score held-out multi-turn/tool-use cases and actual DeepThorT JSONL subprocess behavior. CPU GitHub Actions is suitable for bounded pilots, not full pretraining.
