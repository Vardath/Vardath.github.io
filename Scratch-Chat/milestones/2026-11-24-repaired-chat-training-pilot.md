# Repaired four-turn dialogue pilot wiring — 2026-11-24

Baseline: GitHub Actions run 45257993758 failed at JSON-line transport after its 80-step training and held-out evaluation steps. The successful training used 27 legacy single-turn examples, **not** the repaired 24 four-message CC0 conversations. Subsequent newline framing changes have not been independently confirmed by a completed workflow in this milestone.

Changes: fit ByteBPE only on training messages in structured chat records; add fail-closed conversion from group-isolated original CC0 JSONL to role-token chat records; preserve derived SHA-256 hashes, source hashes, and audit findings; switch bounded 80-step CPU workflow from the legacy corpus to the repaired original four-turn seed; add conversion regressions.

Source: data/original_cc0_multiturn_20261124.jsonl. Split seed: original-cc0-20261124. The conversion refuses cross-split lexical near-duplicates at Jaccard >=0.8. This is NOT semantic decontamination, dataset scale sufficiency, or license verification of external data. If the audit fails, training must stop and report the findings, not bypass the gate.

Expected pilot: random initialization, width 64, 2 layers, 4 heads, 80 steps, with actual role IDs; checkpoint and JSON-line tests run only if earlier gates pass. CPU-only pipeline smoke, not conversation readiness. No new metrics or checkpoint asserted in this milestone.

Outstanding: verify workflow execution and failure/success logs; inspect audit findings and repair split policy if necessary without leakage; train on a substantially larger independently licensed corpus; capacity scaling on available GPU; independent semantic multi-turn and tool-use evaluation; test integration against installed DeepThorT rather than only a subprocess bridge.
