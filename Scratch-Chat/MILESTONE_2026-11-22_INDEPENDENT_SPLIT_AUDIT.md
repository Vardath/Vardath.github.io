# Scratch Chat milestone — 2026-11-22, independent split leakage gate

Previous verified acquisition run: https://github.com/Vardath/Vardath.github.io/actions/runs/45016178851 — success (quarantined Dolly review staging).

Added `capability/audit_dialogue_splits.py` and offline regression tests. This independent pass reopens the three generated JSONL partitions, hashes their actual bytes, and checks normalized user prompts for train/validation/test overlap. The acquisition workflow now runs the tests and fails closed on detected cross-split exact-prompt leakage, retaining the report in its artifact.

All data remains QUARANTINED_NOT_APPROVED; the audit does not confer license or privacy approval. Near-duplicate/semantic contamination, independent benchmark overlap, licensing/consent, model training, checkpoint quality, multi-turn/tool evaluation and real DeepThorT JSONL tests remain outstanding. The newly triggered push workflow must be inspected before claiming green status. GitHub Actions CPU is limited to bounded validation and pilot runs; no GPU entitlement is claimed.
