# Scratch Chat milestone — 2026-11-24 — capacity-training readiness preflight

Baseline verified: GitHub Actions source-test run 45235492652, job 137905974831, completed successfully. This verifies checkpoint-independent tests only, not trained model capability.

Commits in this pass:
- f1bbd39923fa9aa8a0f892be1dc41cea804a6679: add `capability/dialogue_readiness.py`.
- e6ef1b8d346648465891473c9296aec70f1fe992: regression test on repaired 24-conversation CC0 seed.

The new preflight counts train/validation/test records, checks source-conversation isolation, requires explicit allowlisted license labels, and runs cross-split prompt/answer near-duplicate screening. Default *minimum* corpus sizes are 1000/100/100 records; these are engineering gates, not a claim that 1200 conversations suffice for general chat. It deliberately never declares the corpus fully approved: self-reported license labels cannot independently establish copyright provenance. The 24-record original seed must fail the capacity gate even if its split mechanics pass.

No external dataset admitted, no new weights, no training, no Shakespeare-only experiment. CI for these new commits was not yet verified at time of writing. The workflow's existing `test_dialogue*.py` pattern includes the new test; the push path filter includes these files.

Next: independently review source license and redistribution terms; acquire a substantial conversational corpus; freeze hashes and split membership; train a larger random-initialized model with reproducible checkpoints using appropriately available GPU compute; evaluate held-out multi-turn/tool use and actual DeepThorT JSONL subprocess transport. Never interpret a successful source test or low token loss as conversational acceptance.
