# Scratch Chat milestone — 2026-11-23

## Verified
- GitHub Actions source-test run [45076317677](https://github.com/Vardath/Vardath.github.io/actions/runs/45076317677) completed successfully (unit-tests job).
- Added `capability/independent_chat_eval.py`: deterministic, fail-closed held-out prediction scorer with case/prediction ID alignment, multi-turn message validation, lexical inclusion/exclusion, exact-answer and JSON-object checks.
- Added `tests/test_independent_chat_eval.py` with basic positive, negative, structured-output and missing-prediction regression cases.
- These changes do not train weights or imply conversation competence. New push CI is not yet confirmed green.

## Required next steps
1. Obtain and independently review appropriately licensed dialogue sources (including attribution, personal-data handling, upstream restrictions and revisions); do not admit quarantined Dolly by assumption.
2. Freeze and decontaminate train/validation/test partitions before training; publish source manifest and split hashes.
3. Train original random-initialized weights on approved dialogue with reproducible optimizer/checkpoint state. CPU Actions only for bounded pilots.
4. Produce real held-out predictions through the DeepThorT JSON-line subprocess and feed them to the independent scorer; include tool-use, multi-turn context, malformed input recovery and a semantic/human assessment. Do not manufacture predictions.
5. Explore available free GPU environments only after verifying actual availability and terms; do not claim GPU allocation.
