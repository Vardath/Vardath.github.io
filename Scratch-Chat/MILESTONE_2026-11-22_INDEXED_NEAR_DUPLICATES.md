# Indexed near-duplicate audit milestone — 2026-11-22

Verified preceding main-branch Scratch Chat source tests run 45021359475: success. Quarantined acquisition run 45021350379: success.

Changed `capability/audit_near_duplicates.py` to use an inverted shingle index rather than comparing every pair of conversations. Every pair with nonzero Jaccard shares at least one shingle, so candidate generation preserves exact detection at the configured positive threshold; it is not probabilistic MinHash/LSH. Added a regression test and candidate-pair diagnostic. Push commits trigger bounded source CI; check their actual results before claiming the new test passes.

This audit is lexical only and may miss semantic paraphrases; it does not constitute source licensing, privacy/consent, benchmark decontamination or approval to train. Dolly remains quarantined. No new checkpoint, GPU run, DeepThorT application integration, multi-turn or tool-use acceptance is claimed. Next: inspect CI and source/license evidence, resolve admission, prepare independent held-out evaluation and run original-weight dialogue pilot only on approved material.
