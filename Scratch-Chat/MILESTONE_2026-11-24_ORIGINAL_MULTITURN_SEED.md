# Scratch Chat milestone — 2026-11-24: original multi-turn dialogue seed

## Verified baseline
GitHub Actions [source-test run 45204325855](https://github.com/Vardath/Vardath.github.io/actions/runs/45204325855) completed successfully at `d0e00089eb21f65ebe038fea2aa615042fe7b895`. This predates this change.

## New source
Added `data/original_cc0_multiturn_20261124.jsonl` in commit `9bede59a6ad65a1f7dacfd07a56a872fef7cfffb`: 24 newly authored four-message conversations (96 messages), each with a distinct conversation ID, `source_id`, and `CC0-1.0` declaration. Topics include uncertainty, privacy, tool authorization, JSON-lines, reproducibility, dataset leakage, and source verification. These are original synthetic instruction examples written for this project, not downloaded or paraphrased from an external conversation corpus. CC0 dedication applies to this newly authored seed only, not to external datasets.

## Scope and limits
This seed is small, narrow, and not a general-purpose dialogue corpus. It has not been run through split preparation, near-duplicate auditing, tokenization, SFT, checkpoint creation, or independent model evaluation in this pass. The existing training and held-out acceptance prompts must remain isolated; overlapping themes are not evidence of split independence. No external corpus has been licensed or approved. No Shakespeare-only training was performed.

## Next action
Run split preparation and lexical audit on this source as a bounded pilot; check prompt/answer overlaps with existing training and acceptance fixtures before admission. Acquire a substantially larger independently reviewed licensed dialogue source, with exact immutable revision, original byte hashes, contributor terms and privacy review. Train the original random-weight Scratch Chat only after those gates pass. Verify generated multi-turn and tool-use behavior and actual DeepThorT JSON-line subprocess integration; report raw failures. GitHub Actions CPU is limited to smoke/pilot work; no free GPU is allocated.
