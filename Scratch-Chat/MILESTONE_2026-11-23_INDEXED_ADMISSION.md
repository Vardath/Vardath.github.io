# Scratch Chat indexed admission milestone — 2026-11-23

Previous verified source CI: [45021359475](https://github.com/Vardath/Vardath.github.io/actions/runs/45021359475) passed. The last indexed near-duplicate change at e350375 returned no runs from the connector's PR-only commit workflow lookup; that is **not** proof of push CI success.

This pass fixes a separate quadratic scan in `capability/dialogue_admission.py`: the final approved-source admission gate previously compared every conversation with every preceding conversation. It now indexes normalized tokens and only compares records sharing a token, while retaining the existing exact multiset-Jaccard threshold (0.85), minimum token-count condition, cross-split restriction and fail-closed hash/provenance checks. Candidate retrieval is exact for positive Jaccard; worst-case common-vocabulary corpora can still be quadratic.

Added `tests/test_dialogue_admission_index.py` with clean and near-duplicate cross-split fixtures, and wired it into bounded GitHub Actions source tests. Commits: b30cc716, c808ac99, ce6d640b. Pushes should trigger CI; do not claim green until a completed run is independently verified.

Dolly is still quarantined and not approved for training. No external dataset training, original-weight checkpoint, GPU allocation, conversation-quality gain, multi-turn tool-use acceptance or actual DeepThorT application acceptance is claimed. Next: verify CI, resolve license/consent and benchmark contamination, approve only reviewed data, train an original-weight dialogue pilot, and evaluate independently.
