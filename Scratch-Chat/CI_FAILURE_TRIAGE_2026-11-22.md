# Scratch Chat CI failure triage — 2026-11-22

GitHub Actions source-tests run [44955467765](https://github.com/Vardath/Vardath.github.io/actions/runs/44955467765) on commit e9e0b230 completed **failure**. The unit-tests job installed PyTorch successfully, then failed at "Run checkpoint-independent dialogue and protocol tests"; compilation was skipped. The same workflow also failed on 44955460214 and 44955453052. Earlier progress reports that found no commit statuses did not establish successful CI.

Commit 3cdcf4ec changes the workflow to run each suite independently, with GitHub Actions error annotations and a final nonzero exit when any suite fails. It additionally includes previously omitted near-duplicate, split-preparation, independent subprocess acceptance, and JSONL transport tests. This is diagnosis and coverage, **not** a fix for the unknown failing assertion. Read the new run's annotated suite names and output before editing the responsible implementation. Never relax assertions just to turn CI green.

The separate original-dialogue smoke workflow already contains an 80-step random-initialized CC0 pilot with held-out task-family evaluation and a real JSONL subprocess bridge; it is not proof of general conversational competence. Do not repeat Shakespeare-only experiments. Do not treat CI CPU as large-scale pretraining. External datasets remain pending verified license/provenance approval; no external training or independent DeepThorT application acceptance is claimed in this milestone.


## 2026-11-23: confirmed CI regression and repairs

GitHub Actions source-test run [45031586265](https://github.com/Vardath/Vardath.github.io/actions/runs/45031586265) **failed** (not green). Two independent faults were identified from job logs: `capability/dialogue_admission.py` used `r"\\w+"` instead of `r"\w+"`, producing empty token counters and silently bypassing cross-split lexical near-duplicate detection; `test_audit_near_duplicates.py` expected cross-split candidates from pairs incorrectly located within the same split. Commits `c5ddb713e645ef3c9c177d701c21924366137bcb` and `499a5a148ba1c99704aad6d5d3e0c079d7a9539d` correct these separately. The next push-triggered source-test workflow must be inspected before claiming green. No new dataset was approved or trained on. Actual independent model quality and live DeepThorT integration remain unverified.
