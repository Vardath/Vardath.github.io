# DeepThorT v45 verification

- Focused new test module: `tests.test_isolated_gui_v45`, covering scoped executable plan, SHA256 change/replay rejection, symlinks, size/duration bounds, bounded durable receipts, stopped/background worker, GUI confirmation, queue/process integration and non-Windows fail-closed behaviour. Executed in Linux virtual display.
- GUI regression modules: v41 repair, v42 graph/checkpoints, v43 tool probes and v44 quiet Godot test should remain unchanged.
- Full release gate: isolated module-by-module Python unittest via GitHub Actions plus compile and v45 source checksum verification; source overlay uploaded **only after** all tests pass. Record final GitHub run and numbers in the release response, not predicted here.
- No native Windows desktop, GPU contention or user-facing X4/RimWorld/Android acceptance in Linux CI. The test's `window_observed` status is a smoke observation, never full gameplay or visual acceptance.
