# DeepThorT v44 — actual quiet Godot scene tests

Date: 2026-11-23. Baseline: v43 main at `9285be33fc91aaa13fc33dd4789e0ab5ac4acbfa` (concurrent unrelated Scratch-Chat commits preserved). No ONNX or JANUS/Sentinel changes.

## What was implemented

- `deepthort_local/quiet_playtest.py`: fixed, bounded `godot --headless --path PROJECT --quit-after 360` plan, only for a declared main scene and a valid Godot executable; no model-provided CLI. Strictly reject unsafe symlink/path-traversal/missing scene/unknown executable, bad/corrupt receipts, and uncapped Windows launches. A main-scene UID is resolved by Godot itself, not falsely asserted as verified.
- Godot `--headless` suppresses normal window/audio output; it still runs scene scripts and may mutate files with the active user's permissions. No display, keyboard or mouse automation, and therefore no proven actual gameplay quality. No X4/RimWorld silent client execution yet.
- Desktop Work queue explicit `Quiet Godot scene test` and `Stop quiet test` controls. Separate serial process slot and no new game window or modal alert for a failed test. Results in Process log and exported diagnostics. Each test starts with an atomic receipt, bounded output and 120-second wall timeout; process is not replayed blindly after restart.
- Windows guard verifies the parent is already in a Job Object with an active <=20% hard CPU cap; child inherits the same cap. Windows `CREATE_NO_WINDOW` and `IDLE_PRIORITY_CLASS` are applied only to a genuine headless CLI. It is NOT a separate 20% allocation; job RAM limit is committed bytes rather than hard resident RAM. No hard GPU percentage cap.
- Native read-only CPU/RAM sampling yields to foreground games: if under 10% RAM available or 90% CPU for three checks during a detected game, the scene test is terminated and documented as preempted. An ordinary test can run while a game is active; heavy background tests/installs remain gated by the earlier game-protection policies.

## Guarantees and limits

- User starts a quiet scene test with one action; this is NOT an automatic global playtest policy, silent third-party software installer, a VM sandbox, or a guarantee of visual playability.
- Failed/terminated Godot scene tests are not automatically fed into the v41 source repair cycle; adding such a loop requires deterministic acceptance contracts for the gameplay property under test.
- If a game cannot run headlessly, DeepThorT must use a separate isolated session/test device or schedule an attended visual pass. Hiding a GUI window is not sufficient: it can steal focus, use GPU or register global input.
- Native Windows Godot/Windows Job Object acceptance is not covered by Linux CI and requires user testing.

## Next development pass

Windows GUI app launch supervision and isolated program testing with evidence, then Godot gameplay probes and X4/RimWorld/Android platform-specific adapters. See NEXT_STEPS.md and PLAYTEST_ACCEPTANCE_V43.md.
