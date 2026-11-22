# DeepThorT v38 — test results, 23 November 2026

## Locally verified

- `python -m compileall -q .` from the unpacked v38 source: passed.
- **75 focused tests passed** across eight modules: `test_reviewed_install_v38`, `test_online_tool_inspection_v37`, `test_online_tool_search_v36`, `test_ui_help_v35`, `test_execution_safety_v34`, `test_tool_acquisition_v32`, `test_state_health_v34`, `test_regression_cli_v37`.
- The tests validate exact package version/ID/source command, expiry, metadata fail-closed parsing, hash requirements, explicit typed approval, refusal without consent, persistence before process launch, failure to persist blocking installation, and truthfully unverified successful exit.
- UI screenshot `assets/overview_v38.png` captured from actual Tk desktop on a virtual Linux display at 1450×990 with the ONNX worker deliberately not started.
- Pre-existing nonfatal Tkinter stale `after` callback teardown warnings appeared during combined GUI tests; these did not fail assertions.
- A full **local** isolated module run advanced through 24 passing modules and stalled on the next pre-existing JANUS/Sentinel module; no local all-modules pass is claimed. The run was terminated. Use the new GitHub CI result as a separate independent check.

## Not verified by local test

- Actual Windows WinGet search/inspection/installer download or installation, Authenticode publisher signature, software functionality, UAC behavior, child installer cancellation, and independent publisher provenance.
- Real Windows ONNX performance or game-priority measurements. ONNX server and launcher are unchanged from v37.
- X4 in-game mod function, Android APK export or general autonomous project completion.

## GitHub CI

This file describes the local result. GitHub Actions full-suite status must be checked separately after syncing v38; do not infer green CI from these Linux-focused tests.
