# DeepThorT v38 — development continuation, 23 November 2026

**Required model choice:** local Qwen **ONNX**; no external AI model, training
pipeline, or alternative conversational backend. `inference_server.mjs` and
`DeepThorT.exe` are unchanged from v37. Existing JANUS/Sentinel, approval
boundaries, state layout, X4 and other project features are preserved.

Base: the complete 154-file v37 ZIP, whose commit was
`1035a857a649c352d6993992ee278cf39bce073c`.
v37 GitHub Actions regression was independently green, with 448 tests across
56 isolated modules (run 45068553721). Continue from this history, preserving
unrelated repository development commits via base-tree Git commits.

v38 extends `winget search` and `winget show` into a **user-driven reviewed
installation** of newly discovered tools. `deepthort_local/reviewed_install.py`
constructs the immutable exact-version WinGet argv, validates a fresh
inspection, manifest SHA, HTTPS URLs, publisher metadata and installer type,
and emits a one-use review plan. GUI `Review inspected install…` requires
interactive Yes plus typing `INSTALL vendor.package` verbatim. The local
model cannot approve an install. Version, source and user scope are pinned;
`--no-upgrade` is set; shell, force, and hash-override flags are absent.
The approval/audit is written to `state/last-reviewed-install.json` before
launch and is never reused on restart. A WinGet exit code of 0 means only
`completed_unverified`, not independent tool verification. Package installs
can still request Windows elevation and run external code; there is no sandbox.
The WinGet client retains responsibility for downloads/hash comparison.

No independently verified code-signing, trusted supplier checks, Windows
successful install proof, automatic rollback or arbitrary direct download yet.
Never claim the WinGet catalog itself guarantees package security. Exact
search/inspection output may vary across Windows/WinGet releases; parser
rejects unfamiliar formats conservatively. Run Windows acceptance on a
trusted disposable test installation, then inspect a real diagnostics ZIP.

Files: `desktop_app.py`, `deepthort_local/reviewed_install.py`,
`deepthort_local/online_tool_search.py`, `deepthort_local/ui_help.py`,
`USER_GUIDE.html`, `NEXT_STEPS.md`, `README.md`, `START HERE.txt`,
`assets/overview_v38.png`, `tests/test_reviewed_install_v38.py`,
`PROJECT_CONTEXT_V38.md`, `TEST_RESULTS_V38.md`.

Upcoming: independent publisher and Authenticode verification, signed
quarantined downloads, install/post-install executable detection, dependency
resolution from actual project requirements, per-application versioned
execution adapters, safe GUI controls, and genuine X4/Godot/Android acceptance.
Do not modify other project folders in the shared GitHub repository.
