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

## Admission gate implementation (2026-11-22)

`capability/dialogue_source_manifest.py` now rejects incomplete, unapproved, unhashed, or empty-split source manifests. `tests/test_dialogue_source_manifest.py` covers approval, missing license, invalid hashes, identical split hashes, and zero records. **This is a metadata structure gate only**: it does not verify license authenticity, scan privacy, hash actual files, or detect content-level cross-split duplicates. Those checks must be implemented before any external corpus is admitted. No external corpus was ingested, and no new model training or acceptance test was run in this pass.

Commits: `6f2d9dbd2d8bd258f19d56cb90ce4354bd0be7f6`, `090ac1b6f1d50b50575ae9c2bd8a817a248c349b`. Latest pre-change combined status for `afcd8b0` had no status checks; source CI run `44905549853` was previously queued and its conclusion remains unverified here.

## File-level admission gate follow-up (2026-11-22)

The validator now supports `--verify-files DIRECTORY` to read train/validation/test JSONL bytes, compare actual SHA-256 and record counts with an approved manifest, parse nonempty JSON objects, and reject exact canonical duplicate records within/across splits. Regression tests added. Commits: `bd1100815fbdf113fb9f16c53d483fe3107448e8`, `9d0f4da21772ca490dbdbc017bd963e1158797b0`, `37382653287d59b6d13dcc4b69e7e52b103ba24a`. This does **not** perform lexical/semantic near-duplicate detection, authenticate upstream license/consent, or admit external data. No training or capability metrics produced. GitHub combined commit status returned no statuses for `9d0f4da`; push CI conclusion remains unverified.

## Normalized dialogue decontamination follow-up (2026-11-22)

The split admission gate now requires nonempty `messages` with recognized roles and nonblank text, and rejects repeated full conversations after Unicode casefolding and whitespace normalization even when record IDs or provenance fields differ. This closes a metadata-disguised exact-conversation leak, **not** fuzzy lexical or semantic near-duplicates, shared prompt templates, or conversation-family grouping. Two regression tests were added. Commits `b72c8c4`, `707b17c`, `13f90d7`. Prior source CI run 44905549853 completed successfully (unit-tests job), but new-commit CI remains unverified at writing. No new external data admitted, no training or capability claims.
