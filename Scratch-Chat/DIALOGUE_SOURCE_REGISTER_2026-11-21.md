# Dialogue source acquisition register (2026-11-21)

This register is **candidate research, not ingestion approval**. No external dialogue is admitted by this document. Every admitted dataset must have a fixed revision, independently checked terms, original-source provenance, attribution obligations, privacy/consent review, SHA-256 for downloaded bytes, and a split-level contamination audit.

| Candidate | Source | License/provenance decision | Next action |
|---|---|---|---|
| OpenAssistant OASST1 | https://huggingface.co/datasets/OpenAssistant/oasst1 | **PENDING**: verify Apache-2.0 applicability to each message and contributor terms, PII and moderation filtering; dataset label alone insufficient | Retrieve pinned revision and upstream contributor/license documentation, inspect records, then approve or reject |
| Dolly 15k | https://huggingface.co/datasets/databricks/databricks-dolly-15k | **PENDING**: verify CC BY-SA 3.0 terms and compatibility with intended redistribution, attribution and commercial use; employee-authored provenance needs review | Inspect dataset card, license text, revision, and examples before deciding |
| Tulu 3 SFT mixture | https://huggingface.co/datasets/allenai/tulu-3-sft-mixture | **REJECT AS A MIXTURE** until each component's underlying terms and provenance are audited | Create per-component entries; never approve from the mixture-level label |
| Existing self-authored seed | Scratch-Chat/data (repository) | **APPROVED SEED ONLY**, subject to existing hash gate; too small for general capability | Preserve independent test split; no claim of conversational readiness |

## Required acquisition evidence

For each source, save an immutable manifest with `source_id`, upstream URL, exact commit/revision, download UTC, license URL/text, attribution and redistribution obligations, upstream collection method, consent/privacy notes, moderation/filtering procedure, original SHA-256 and filtered split SHA-256, record counts, and reviewer decision. **Do not automatically download or train on PENDING sources.**

Group train/validation/test by original conversation, source document and template family before tokenizer training. Compare exact normalized messages, lexical near-duplicates, and prompt/response paraphrases across splits. Keep independent DeepThorT multi-turn and tool-use acceptance prompts separate from training and tuning.

## Verified CI and current limitation

GitHub Actions **Scratch Chat source tests** run [44900943285](https://github.com/Vardath/Vardath.github.io/actions/runs/44900943285) completed successfully for commit `d6b84f5da9102ca530ad7b233b7c39b691aa37c6`. This verifies scoped source tests, **not** an independently trained conversational model or DeepThorT acceptance. Large licensed corpus, GPU training, and external multi-turn/tool-call acceptance remain outstanding.
