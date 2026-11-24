# DeepThorT v37 — local test evidence (23 November 2026)

- `python -m compileall -q` on the app modules and desktop source: **passed**.
- Combined focused local regression under Xvfb: **51 tests passed**, covering
  WinGet exact-ID inspection, preserved v36 search approvals, v35 UI/tooltips,
  desktop wiring, execution safety, generated script approval, and the hardened
  local regression test runner. Some preexisting Tkinter teardown callback
  messages remain nonfatal.
- Standalone `tests.test_janus_sentinel`: **11 tests passed** under Xvfb.
- The pre-fix sequential local regression run stalled after 24 passed modules
  (not a source assertion failure). A run with a subprocess timeout also
  stalled on the same module. The new process-group cleanup is unit tested, but
  the complete *local* suite has **not been certified green**. Report GitHub
  Actions full-suite results separately; do not mislabel incomplete runs.
- Windows WinGet network query/metadata, Windows UI and ONNX performance,
  package signatures, downloads, actual X4 gameplay or Android builds have
  **not** been tested in this Linux container.
- `DeepThorT.exe` launcher and ONNX server remain byte-for-byte unchanged
  relative to v36; no model/state data is bundled in this archive.
