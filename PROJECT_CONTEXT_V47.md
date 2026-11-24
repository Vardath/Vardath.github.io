# DeepThorT v47 — recovered planning history, transport resilience

23 November 2026. Baseline v46, commit bcdcf59a7b2f2850f1b753c21456817965d4571b.

The 11:01 diagnostic ZIP demonstrated three Windows error 10054 connection resets during sustained local Qwen inference. Log chronology shows the ONNX process disappeared during a request and a new launcher/model process appeared shortly afterward. The exact crash reason is NOT established: process closure, manual relaunch and memory-commit pressure cannot be distinguished from the redacted logs alone. v47 does not change inference model or resource limits.

## Recovery paths
1. Existing v16 per-pass exact replay on the same session ID and full input.
2. **Historical session migration:** look up complete user/assistant pairs in `state/sessions.sqlite3` by exact original model input. Cross-reference the request ID to `state/conversations.sqlite3`; match original user request, project, chat and no attachments. Ignore dangling user-only messages, changed context and malformed replies. The full plan parser and game/X4 validator remain mandatory. Do not reconstruct model content from model event counts.
3. **Large-document index inheritance:** when the old indexed original specification, source hashes, project and chat match, copy only already reviewed and structurally revalidated section file proposals into the new request's index. Partial review has no approval power. Invalid section progress is not adopted.
4. **Transport recovery:** on a reset/aborted connection, persist pending status rather than a misleading permanent model error. Block scheduler when previous worker is busy, and restart unexpectedly exited, already-ready supervised models at most twice. A stopped model, a model failing before initial readiness or application shutdown does not automatically restart. Two failed transport recoveries per request exhaust the bounded policy. Stop and inspect diagnostics after the budget.

## Model/data limits
40 ordinary plan passes per invocation; 40 local model calls per large-specification batch. Neither counts source files. The latter processes 3,200-character source sections with exact SHA evidence. Existing durable indexes remain under `D:\deepthort\state`. The project folder such as `D:\x4mods` is for approved generated artifacts, not app checkpoint state. Historical replies that were never saved or have since been erased are not reconstructible from a redacted diagnostics archive.

## Acceptance still outstanding
Physical Windows 10 ONNX process exit investigation (exit code, memory limit and Windows Event Viewer), resumed original PE project results, per-pass transfer quality, game behavior, GPU budget, and all actual X4 playtesting. Linux Xvfb simulates GUI logic only and cannot prove Windows process exit mechanics.
