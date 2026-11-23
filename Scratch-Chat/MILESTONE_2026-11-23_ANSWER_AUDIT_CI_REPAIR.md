# Scratch Chat — indexed answer audit CI repair (2026-11-23)

## Verified failure
GitHub Actions [45136980722](https://github.com/Vardath/Vardath.github.io/actions/runs/45136980722) failed in `test_audit_near_duplicates.py::test_index_matches_exhaustive_reference`: the expected candidate count was 2, actual 3. All other dialogue/protocol suites in that job passed. The recently added assistant-answer screening correctly introduces an additional cross-split candidate for the duplicated bee question and its identical hash-derived answer; the old test expected prompt-only counts.

## Change
Commit `f4dcb54b0bba91d7f6ac1ca9525c52fb554ff693` updates the reference expectations to three candidate pairs and three findings, and asserts the kinds are exactly two prompt matches and one answer match. This retains answer leakage detection instead of weakening the auditor.

## Acceptance and blockers
Follow-on push CI must be independently verified; this milestone is not a claim of a passing workflow. No approved real dialogue corpus or new trained checkpoint was produced. Dolly remains quarantined. The next substantive step is source licensing/privacy review and admission of decontaminated dialogue splits, followed by bounded training from random initialization, held-out quality evaluation and actual DeepThorT JSON-line tests. CPU GitHub Actions cannot establish large-scale conversational capability.
