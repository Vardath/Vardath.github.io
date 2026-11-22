# Dialogue acquisition implementation milestone — 2026-11-22

Verified prior Scratch Chat source CI: [44995962360](https://github.com/Vardath/Vardath.github.io/actions/runs/44995962360), completed **success** for c4c4e9be.

Implemented `capability/import_dolly_candidate.py` to convert a locally acquired Dolly-style JSONL export into deterministic role-tagged user/assistant conversations. It requires a fixed upstream revision and exact SHA-256 of source bytes, deduplicates identical instruction/response pairs, retains source line and revision, refuses output overwrite, and labels every row `PENDING-REVIEW`. It deliberately cannot pass approved-data admission. No network retrieval, license clearance, PII filtering, split assignment, model training, or conversational improvement occurred. This is a usable importer, not an acquired corpus.

Regression tests: `tests/test_import_dolly_candidate.py`; CI workflow now includes the suite. Commits: 653e40e, 1bae426, 79fa41a. Next: obtain and inspect revision-pinned source bytes, independently verify license and collection consent, review and filter PII, build grouped decontaminated splits, and train original-weight SFT. Independent DeepThorT multi-turn/tool-use acceptance remains unmet.

CPU GitHub Actions is only for bounded pilot tests; no free GPU allocation has been verified.
