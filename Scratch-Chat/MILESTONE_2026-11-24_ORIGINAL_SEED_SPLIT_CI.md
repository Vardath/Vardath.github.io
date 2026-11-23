# Original CC0 seed split audit milestone — 24 November 2026

## Verified source-test baseline
GitHub Actions Scratch Chat source-test run [45226087629](https://github.com/Vardath/Vardath.github.io/actions/runs/45226087629) completed successfully for commit 1be126fdd3f18dd80b02db30ded672debce0aebb, after the 15-record turn-alignment repair. This is a source-test result, not model acceptance.

## Implemented
Added `tests/test_original_multiturn_seed_pipeline.py` to check all 24 repaired four-turn conversations, unique conversation identifiers, CC0 metadata, deterministic group-isolated train/validation/test generation, source and split SHA-256 digests, and invocation of the existing cross-split lexical near-duplicate audit. Registered the test in the push-triggered Scratch Chat source-test workflow. This checks the real corrected source file rather than fabricated test fixtures. A failed lexical audit remains exposed and must be investigated before training.

## Outstanding
The test is an automated preparation gate, not a published reviewed split or evidence of conversational performance. The seed remains too small and domain-concentrated for general chat. A provenance-approved manifest, independently inspected lexical/semantic leakage report, larger licensed dialogue corpus, bounded original-weight training, reproducible checkpoint, held-out multi-turn/tool-use evaluations, and actual DeepThorT JSON-line acceptance remain necessary. No new checkpoint, GPU access, or training metric is claimed. Check follow-on source CI before relying on this test.
