# DeepThorT project handover — v31 (22 November 2026)

Current release: v31, based on v30 (v30 source had not been synchronized to GitHub). All earlier architecture and constraints remain: one local ONNX Qwen model; separate JANUS/Sentinel; 20% gaming CPU/commit limits; no automatic approvals; explicit user approval before writing project files or running tools; preserve original desktop geometry, dependencies, models, references and local state.

The 21:28 user diagnostic ZIP reported Windows 10 (19045), model ready/idle, no active/pending conversation and no approved jobs, and project `vardath_faction_camouflage`. The X4 source inspection logged only `reference candidates found`; it did not include the underlying X4 source findings. `desktop_init` still advertised version 27 in v30. This was an observability issue, not evidence that PE references were correctly extracted.

v31 adds `deepthort_local/diagnostic_evidence.py` with bounded read-only X4/engine snapshots, persists them across restarts tied to selected project, exposes them via the pre-existing diagnostic ZIP, and corrects `desktop_init` version. Tests: 373 passed across 46 isolated modules. Monolithic Tkinter run still aborts on teardown; Windows, game and inference not tested.

Next: User installs v31; selects actual X4 project and runs **Scan this computer** and **Inspect X4 sources**; exports ZIP. Inspect `summary.json` → `application_state.x4_source_inspection` and `engine_readiness_scan`. Address actual blockers such as PE macro absent, component slot tags absent, missing usable M weapons/turrets, nonexistent vanilla indexes. Do not repeat 40-pass planning until source evidence is sound. Then test a small model-generated X4 plan/implementation and verify in game. Do not invent game identifiers or claim in-game success without testing.

Release source: /DeepThorT in https://github.com/Vardath/Vardath.github.io . The complete v30 changes (13 source files) and v31 changes must both be synchronized; do not claim GitHub updated unless verified.
