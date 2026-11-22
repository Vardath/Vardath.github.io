# DeepThorT v34 continuation context — 22 November 2026

Base: `DeepThorT_Desktop_v33_Windows.zip` and its unpacked source. Original layout, JANUS/Sentinel, supervised offline ONNX, user approval and game priority preserved.

User request: anticipate unhandled failures before Windows testing tomorrow. The most important discovered risks were stale approved commands, unauthorized target changes while a user reviews code, runaway subprocesses/logs, power-loss temp-file blockage and missing crash-state integrity reporting. See `APPROVAL_SAFETY_V34.md`.

Source changes: new `deepthort_local/action_guards.py`, new `deepthort_local/state_health.py`, modified `deepthort_local/janus_engine.py`, `janus_worker.py`, `deepthort_local/tool_acquisition.py`, `deepthort_local/workspace.py`, `deepthort_local/flight_recorder.py`, `desktop_app.py`. New tests `tests/test_execution_safety_v34.py`, `tests/test_state_health_v34.py` and `regression_cli.py`. New documentation `APPROVAL_SAFETY_V34.md`.

Tests ensure legacy JanusStore actions upgrade with default `[]` guards, old v33 tool recipes still run, generated scripts are separately approved, new queued actions fail closed when inputs change, process runtime/output/disk limits, and prior source edits are not overwritten if changed after review. The on-demand state health diagnostic does not copy DB contents. The `regression_cli.py` runner isolates Tkinter modules under a fresh Xvfb display on Linux.

Known limitations: scripts are NOT sandboxed; a valid Python AST is NOT a safe script; hashes at process startup do NOT prevent adversarial filesystem races; runtime kill may leave partial writes; multi-file transactions/rollback not implemented; no Windows end-to-end Blender, Godot or X4 gameplay verification. Do not claim success for an actual Xenon PE mod or the Faction Command Android game. Existing combined Tkinter teardown issue has not been corrected in production.

GitHub repo: `Vardath/Vardath.github.io/DeepThorT`; v30–v33 changes had not yet been committed at the beginning of this pass. Only state GitHub synchronization complete if actual remote file hashes/commit are verified. Never force-push or replace unrelated `Scratch Chat` changes.
