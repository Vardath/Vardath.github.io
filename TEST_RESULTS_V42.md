# DeepThorT v42 regression evidence — 23 November 2026

## Focused implementation tests (completed)

- `python -m unittest -q tests.test_task_graph_v42 tests.test_source_checkpoints_v42`: 19 tests passed. Includes exact approved-job graph construction, ordered dependencies, requirement links, observed executable presence, interrupted leases, source receipts, immutable revision identity, restoration to missing/existing/empty files and explicit consent.
- `xvfb-run -a python -m unittest -q tests.test_task_graph_gui_v42 tests.test_gui_flow tests.test_development_cycle_gui_v41 tests.test_hierarchical_gui_v25 tests.test_project_authority_v40`: 17 tests passed before the final help/UI layout adjustment. The v42 GUI flow uses actual Python unittest subprocess execution, the same local-model mock API seam used in v41, then a confirmed user rollback invalidating verification and quarantining newly created files.
- `python -m compileall -q .`: source compilation passed locally.
- A broad local isolated-module sweep hit a local tool execution limit before reaching all modules, so it is **not** a pass. Complete validation must use GitHub Actions on the exact release commit.

## Release protocol

A green build of `.github/workflows/deepthort-tests.yml` must compile all code, test each isolated `tests/test_*.py` module under Xvfb, CRC-check a ZIP source overlay, and verify the unchanged v41 ONNX runtime hash and immutable v41 Windows-launcher preservation. Report exact `main` SHA, GitHub Actions run, final test count and artifact SHA-256 after completion. Do not label pending CI tests green.

## Still unverified

- Physical Windows launcher execution, real local Qwen generation, WinGet, UAC or game-priority Job Object caps.
- Actual game engine, Android APK, X4 save/gameplay, resource enforcement and correctness of model-generated repairs.
- Multi-file rollback is sequential and source-scoped, not a guaranteed atomic Git transaction or automatic recovery after mid-restore crashes.
- A fixed test command can execute untrusted project code under the user's normal account privileges; it is not sandboxed.
