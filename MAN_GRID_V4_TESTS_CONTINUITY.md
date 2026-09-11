# Man Grid v4 — active test continuity

Active campaign: corrected exact-v4 Tests 4–16. Tests 1–3 are the completed corrected foundation.

Execution: every Test 4–16 is a genuine deterministic 20-shard test with disjoint evidence partitions; every merge requires all 20 shard outputs; independent branches run concurrently; dependent tests wait only for required corrected outputs; no custom GitHub Actions `timeout-minutes`; do not reuse invalid A1–D4/16-state or incorrect traced-grid mappings/results; do not assume a transformative-circle rule without evidence.

- **Test 4 — Original-language lexical reconstruction.** Depends on Test 1. Reconstruct meaning-bearing ancestral forms from multilingual same-meaning evidence using the corrected 36-phoneme inventory and exact Man Grid.
- **Test 5 — Full dictionary expansion and stability.** Depends on Test 4. Expand toward 12,000+ entries only where supported; test leave-family-out and shard stability.
- **Test 6 — Nearest current and historical language.** Depends on Tests 4–5. Re-rank attested languages by closeness to the corrected reconstruction; do not reuse old rankings.
- **Test 7 — Origin/family enrichment + held-out-family stress test.** Depends on Tests 4–5. Test unusual family closeness while excluding that family from predictor construction to avoid circularity.
- **Test 8 — Reverse-family convergence.** Depends on Tests 4–5. Test whether independently reversed families converge on the same ancestral attractor rather than arbitrary modern languages.
- **Test 9 — Data-driven sibling-language anchor discovery.** Depends on Tests 4–8. Discover the two sibling branches from data; do not hard-code Occitan/Indonesian.
- **Test 10 — Common-parent test of discovered sibling anchors.** Depends on Test 9. Infer a parent from the two discovered siblings and compare with the independent root, held-out languages, and random controls.
- **Test 11 — Sibling-constrained candidate-language reconstruction.** Depends on Test 10. Reconstruct a second full lexicon using sibling evidence only as constrained additional evidence.
- **Test 12 — Independent candidate validation.** Depends on Test 11. Compare correct sibling anchors, no anchors, and wrong/shuffled anchors on unseen languages, families, and meanings.
- **Test 13 — Historical language drift through the correct Man Grid.** Depends on Test 1. Learn documented ancestor→descendant changes with held-out historical, shuffled-target, and wrong-meaning controls.
- **Test 14 — All-language transformation-rule discovery.** Depends on Tests 1 and 13. Learn supported substitutions, insertions, deletions, contextual changes, Man Grid movements, mirror effects, and circle behaviour only if statistically supported.
- **Test 15 — Rule-augmented original-language reconstruction.** Depends on Tests 5 and 14. Compare cross-validated historical rules against unaugmented and shuffled-rule systems on held-out evidence.
- **Test 16 — Final phonetics/language/dictionary consistency pass.** Depends on Tests 1–15. Freeze the corrected phonemes, language, supported rules, evidence-supported dictionary, pronunciation/audio representation, confidence, failures, limitations, and evidence boundaries.

Dependency map: **4 ∥ 13 → 5 ∥ 14; after 5, 6 ∥ 7 ∥ 8; 4–8 → 9 → 10 → 11 → 12; 5+14 → 15; all 1–15 → 16.**

“Running Tests 4–16” means the whole dependency graph is active; tests not yet eligible are queued until their required corrected outputs exist.
