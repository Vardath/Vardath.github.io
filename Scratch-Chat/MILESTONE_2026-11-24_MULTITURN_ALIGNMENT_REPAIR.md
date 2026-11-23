# Original dialogue seed: turn-alignment repair (24 November 2026)

## Verified baseline
[Source-test run 45216806400](https://github.com/Vardath/Vardath.github.io/actions/runs/45216806400) completed successfully: unit-tests job, compilation, and checkpoint-independent dialogue/protocol test step. This run predates the repair.

## Data-quality finding and repair
Manual inspection of all 24 four-message records in `data/original_cc0_multiturn_20261124.jsonl` identified 15 records where the first assistant response answered the *following* user turn, or where the final response failed to answer the most recent user question. This is harmful next-turn supervision, not a cosmetic issue.

Commit [1924366](https://github.com/Vardath/Vardath.github.io/commit/19243661451a52c25c30dae88bd7dcb10cdac976) corrected the assistant replies in records 002, 003, 004, 006, 007, 008, 009, 011, 014, 016, 017, 020, 021, 022 and 023. All 24 original record IDs, message-role order, source IDs and CC0 declarations remain intact. The prior seed bytes are superseded: any previous digest or derived splits must be regenerated from the repaired revision; never silently reuse stale split manifests.

## Limitations and next gates
This remains a tiny synthetic, topic-concentrated seed, not general conversational training data. Manual semantic review is fallible; hold out independent evaluation prompts. The corrected seed has not yet been split, decontaminated, trained or evaluated in this pass. No checkpoint or conversational improvement is claimed. Run source-test CI on the push commit, then generate immutable splits and manifests from the new bytes, check lexical and semantic contamination, and conduct bounded from-scratch SFT. GitHub Actions CPU is appropriate only for bounded pilots; independent multi-turn, tool-use and actual DeepThorT JSON-line acceptance remain required. External dataset licenses and privacy must be independently verified before admission.
