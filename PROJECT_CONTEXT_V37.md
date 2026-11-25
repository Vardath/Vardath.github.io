# DeepThorT v37 continuation — 23 November 2026

Base: complete `DeepThorT_Desktop_v36_Windows.zip` (148 files), synchronised
commit `80a0c56032a6b9ba1709be6ff7449492947a3bcf` with verified green CI
(436 isolated tests, run 45032623866). No source rewrites from stale GitHub.
Keep the original desktop layout, local 1.5B Qwen/ONNX inference engine,
JANUS/Sentinel split, gaming priority, 20% process resource profile, explicit
approvals, pending state and project folders intact.

v37 adds `Inspect package ID…` to Computer & Tools. User enters a complete
WinGet `vendor.package` ID and confirms one `winget show --id ID --exact
--source winget --locale en-US` network query. A strict parser reconciles a
bounded 64 KiB result with the exact command, requires package header/version/
publisher, rejects ambiguous/corrupted data, and sanitizes unsafe URLs.
A JSON receipt with the manifest hash (when present) and catalog-output SHA256
is stored in state but explicitly marks download and installation **unauthorized**.
Catalog metadata is NOT independent publisher or signature verification.
The existing eight reviewed WinGet install IDs are the only installable ones.
The new query is limited to 90 seconds, observes cancellation/gaming priority,
and never executes installers or shell instructions from result text.

The old local regression harness was also hardened to kill the entire
isolated process group on timeout (not production JANUS processes), with two
tests verifying child process cleanup. The local sequential run before this
fix hung on a preexisting Sentinel module; standalone Sentinel and focused
suites succeed. GitHub CI is the authoritative complete suite result.

New code/tests: `deepthort_local/online_tool_search.py`, `desktop_app.py`,
`deepthort_local/ui_help.py`, `tests/test_online_tool_inspection_v37.py`.
Updated `USER_GUIDE.html`, screenshot and `NEXT_STEPS.md`. Existing state
migration is unnecessary; read-only receipt is a new isolated file. All code
checks are synthetic on Linux; no live Windows winget show or package signing
verification has been performed. Combined-process Tkinter teardown warnings
remain from older versions. Source/ZIP parity and CI should be checked after
publishing. Do not claim gameplay or fully autonomous tool installation.

Next: inspect the actual Windows v37 diagnostic ZIP and observed `winget show`
format; add independently checked package provenance, signed installer
quarantine, true per-download/per-install approvals and rollback in stages.
Then implement version-aware engine adapters and real mod/game acceptance.
Never overwrite unrelated `Scratch-Chat` changes in the shared repo.
