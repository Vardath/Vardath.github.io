# Scratch Chat JSONL transport regression milestone — 2026-11-23

Verified GitHub Actions source-test run [45076317677](https://github.com/Vardath/Vardath.github.io/actions/runs/45076317677): the unit-tests job completed successfully, including the checkpoint-independent dialogue and protocol test step. This result predates the new regression.

Commit [7e2ee9d8a0243a2e62fcdc65a3a5e22e810bae31](https://github.com/Vardath/Vardath.github.io/commit/7e2ee9d8a0243a2e62fcdc65a3a5e22e810bae31) adds `tests/test_dialogue_jsonl_transport.py`. It sends five newline-delimited requests through the real `serve` loop using a randomly initialized transformer: health, one-turn chat, invalid orphan assistant, multi-turn chat, and health after the error. Assertions check one JSON response per request, invalid-request recovery, and explicit non-readiness. This is a protocol regression, not model quality acceptance. The existing source-test workflow discovers `test_dialogue*.py` and is push-triggered for `Scratch-Chat/**`.

This milestone commit itself triggers follow-on source tests. **Do not mark the new test green without inspecting the resulting completed Actions job.** The test exercises the Python JSONL service in-process, not a live installed DeepThorT application; a separate original-dialogue smoke workflow has a subprocess bridge test. No conversational performance metrics or checkpoints were produced in this pass.

The existing CC0 pilot is bounded; Dolly remains quarantined and unapproved for training. Next: verify CI, inspect source manifests and quarantine audit, admit independently reviewed licensed dialogue, run original-initialization training with reproducible checkpoints, and score actual held-out multi-turn/tool-use predictions through DeepThorT.
