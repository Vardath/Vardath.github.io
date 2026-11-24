# DeepThorT v55 — honest JANUS handoff verification and format recovery (23 Nov 2026)

Baseline: the installed and locally verified v54 source overlay, with the original Windows exe, 30% combined Job Object, dual supervised Qwen2.5-Coder-1.5B-Instruct ONNX, persistent 11-core JANUS/Sentinel, and no changes to user project files or approval boundaries.

## Windows evidence

The user supplied `DeepThorT-LatestTest-20261123-221821.zip` and `DeepThorT-Diagnostics-20261123-222301.zip`. The 22:18 test reported six successful probes and **inconclusive** concurrent inference because the primary worker was idle. JANUS was unpaused, cycle 1777; the later 22:23 diagnostic reached cycle 1806 and Sentinel was tracking it. Primary and council ONNX PIDs were 33400 and 34196, respectively. Memory remained below 2.1 GiB resident for each ONNX worker. The launcher reported 30/30 caps, but neither that log nor Job membership prove 30% observed throughput.

The major hidden failure is JANUS instruction #1: the desktop log at 19:11:34 QLD recorded `JANUS instruction #1 needs review; council inference failed: Expecting value: line 1 column 1`. The old `janus_inbox` probe returned passed merely because the DB was readable (one item, zero pending); it did **not** establish successful neural translation or handoff.

At 20:16:58 QLD the Xenon PE planning conversation #28 failed safely after eight zero-gain corrections: **all nine checks remained unmet**, no approved files created, no development-cycle execution and no game playtest. The installed X4 reference scanner is ready and the selected output project is x4mods. This is currently a model/strategy planning correctness issue, not missing game references.

## Changes

- `deepthort_local/dual_onnx.py` accepts a clearly fenced JSON response but not arbitrary prose or fragments; an invalid JANUS or Sentinel answer gets **one** format-only retry, with strictly typed schema validation. If still invalid, the instruction remains reviewable. No model output can approve source changes.
- `deepthort_local/instruction_inbox.py` adds `inbox_acceptance`: redacted state counts, and honest classification of pending, interpreting, failed, review-required, staged versus actually handed-to-planner advice. The latest instruction's actual state determines the probe status, not SQLite readability.
- `desktop_app.py` uses `inbox_acceptance` in the one-click Latest Test. `LATEST_TEST.json` has new v55 ID/title but the same seven safe probe identifiers.
- 7 new focused handoff tests, updated existing GUI test expectations, no external tools launched, model weights untouched, no change to shared 30% cap.

## Limits

Staged advice is not evidence of planning consumption. Handoff-to-planner does not imply implementation, test acceptance or completed X4 extension. A repeated model-format failure still needs user review/retry. v55 does not cure the observed Qwen inability to close the nine X4 plan requirements. The offline unit tests use scripted model replies; Windows acceptance remains necessary. Source release not automatically an independently verified GitHub CI release.
