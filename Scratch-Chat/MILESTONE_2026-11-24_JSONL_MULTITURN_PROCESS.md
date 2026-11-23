# Scratch Chat milestone — 2026-11-24 — multi-turn JSONL subprocess verification

Baseline: source-test GitHub Actions run 45246119831 completed successfully on commit 1d7c402757fb5fc74b70b576c28ce8d27272ffa0 (2026-11-23 19:10 UTC). This is source-test evidence only.

Change: commit c9daea98d5af84335dd569343fdf42a6f2365ba2 extends the existing bounded random-initialized dialogue smoke workflow to send eight requests through the real DeepThorT JSON-line subprocess, including a four-message conversation, a system message, malformed JSON, invalid role order, repeated user roles, unknown method, and post-error health recovery. The assertions verify protocol framing and errors, not response semantics. This is NOT a claim of working conversational memory or tool execution.

The workflow still trains a tiny random-initialized checkpoint for 80 CPU steps on original dialogue, evaluates held-out families and uploads diagnostic artifacts. It does not use Shakespeare-only training or pretrained weights. This change to the workflow is push-triggered, but the new run's conclusion must be checked separately.

External licensed dataset admission and large-scale GPU training remain blocked pending independent source licensing/provenance and privacy review. The 24-conversation CC0 seed is insufficient for capacity training. No new conversational acceptance result or GPU availability is claimed.

Next: verify smoke workflow execution and raw outputs; obtain approved dialogue corpus with immutable hashes and group-isolated splits; train an appropriately sized random-initialized model on suitable compute; measure independent multi-turn and tool-use quality and actual DeepThorT application integration.
