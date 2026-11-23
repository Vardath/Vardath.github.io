# DeepThorT v49 development continuity — 23 November 2026

Baseline: verified v48 DeepThorT source overlay, Windows Tk original eight tabs, local Qwen2.5-Coder-1.5B-Instruct ONNX only, JANUS and Sentinel independently persistent, Windows 20% process-tree CPU/commit cap, no extra cloud model.

Diagnosis: `DeepThorT-Diagnostics-20261123-144315.zip` export taken 14:43 Queensland time. Request #26 planning 03:23:55–04:42:41 UTC, 40 indexed roadmap repair calls; 9 unmet criteria at all twelve recorded accepted-model revisions; no approved source files, jobs or live playtests. Peak sampled near end Qwen process ~18.38% CPU, 2216 MiB resident memory. The model answered; progress—not wall time—was the problem. ZIP privacy intentionally omits raw model answers; do not speculate about exact malformed output.

v49 adds per-accepted-section 40-call batch continuation, per-closed-X4-check 40-call revision batch continuation, eight-call X4 stall pause, eight invalid-source-response pause, persisted acceptance outcomes in `specification_revision_outcomes` tied to source SHA256 and exact revision serials, strict nonregression of validator gaps even when a file was added, and shorter one-focus correction prompts with exact original section. No arbitrary code, hidden model changes, or guessed game identifiers. `desktop_app.py` enables `continuous=True` only for indexed large-spec plans, not for ordinary chat or built/tested jobs. Tests and docs updated.

`MAX_PLAN_ATTEMPTS=40` is still a batch safeguard. Model inference may proceed for hours or longer only with objective progress; user Stop still cancels. Existing SQLite state retains sections and authorized progress across app restart, but an interrupted conversation may still need explicit user retry. Separate milestone approval and source writing remain gated; do not claim months of autonomous executable game development exist already.

Next pass: actual local X4 plan quality and real game-mod acceptance, multi-milestone project scheduling, continuous verified build/test/repair with resource/game pressure controls and user approval boundaries. Need Windows diagnostic after updated v49 use.
