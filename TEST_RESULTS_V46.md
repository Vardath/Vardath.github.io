# DeepThorT v46 verification

- Structural parsing, project-scoped exclusions, exact-context continuation, restore/atomic persistence and no-source-deletion checks: `tests/test_inspection_and_continuation_v46.py`.
- GUI headless test checks Treeview exclusion, persistence after restart and unchanged source bytes.
- Existing X4 validator, auto-preflight and capability-library tests rerun under Xvfb.
- Final release gate is GitHub Actions: all independent `tests/test_*.py`, Python compile, SHA-256 manifest check and source-overlay ZIP packaging only after green tests.
- **Not verified here:** actual Windows 10 resource consumption, Qwen generation quality, native GUI menu interaction, mod creation or X4 playtesting.
