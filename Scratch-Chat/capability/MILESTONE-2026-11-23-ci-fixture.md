# Scratch Chat milestone — 2026-11-23: CI failure repaired

## Verified before changes
- GitHub Actions push run 45048451202 (commit c25afd0) **failed** at checkpoint-independent source tests. Job 137288087361 logs show `test_dialogue_admission_index.py` expected a `near-duplicate` error, but the strengthened admission gate correctly rejected an **identical user prompt across splits** first. The test was also executed twice by overlapping test patterns.
- Prior run 45035111424 had completed successfully; it did not validate the newer role-order change.

## Change
- Commit b7857afd858bcb8d1398e8e1faa6af452d3ec73f modifies the regression fixture so the held-out user prompt differs by one word while the full conversation remains lexically near-identical. This exercises the indexed near-duplicate path rather than the earlier exact-prompt gate.
- No changes to production admission thresholds or approval policy. No Shakespeare-only training.

## Remaining blockers
- Confirm the new push-triggered CI run passes. A committed fix alone is not a green result.
- Dolly acquisition/review artifacts are **quarantined**, not a license/consent approval. The source manifest must include independently verified terms and approval before any external-data SFT run.
- Complete decontaminated dialogue export, original-weight training with reproducible checkpoints, held-out multi-turn/tool-use quality evaluations, and real DeepThorT JSONL subprocess integration. Transport smoke tests do not demonstrate model competence.
- GitHub-hosted CPU should remain limited to tests and small pilot training. Free GPU environments (e.g. Colab/Kaggle subject to current availability and quotas) must be configured by an authorized account; no GPU access has been verified.
