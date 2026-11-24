# DeepThorT v45 — isolated-desktop Windows GUI smoke testing

Date: 23 November 2026. Baseline: v44 `cffc2ff7d9aec4b2dcd04a0485fc46b7529a4126`. This pass changes neither Qwen ONNX inference nor JANUS/Sentinel.

## User operation

1. Launch DeepThorT normally through the existing `DeepThorT.exe` supervisor, select a **trusted** project folder, and ensure no other project test or installation is running.
2. Work queue → **Isolated GUI smoke test…** → choose a **project-local, already built `.exe`**. Review the explicit native-code consent and click Yes. Other executable files, outside-project binaries, symlinks, and changed binaries are rejected.
3. The test runs a maximum of 25 seconds at low priority, on a separately created Win32 desktop, without switching desktops, posting messages or injecting mouse/keyboard input. No user-facing game window opens on the active desktop. **Stop isolated GUI test** requests cancellation.
4. Processes shows the observed project-owned window titles/bounds, responsiveness, process exit and status. `state/isolated-gui-v45.json` records bounded durable receipts; explicit Export diagnostics includes those receipts. No completed GUI test is reissued following restart.

## Engineering scope

`deepthort_local/isolated_gui.py` validates and SHA-256 fingerprints the exact program, and immediately revalidates before launch. The Windows native helper creates a distinct Win32 desktop, `CreateProcessW` suspended and IDLE priority, a **nested kill-on-close Job Object** assigned before the child resumes, and bounded read-only `EnumDesktopWindows` observation for exactly the target PID. The child still inherits the parent DeepThorT.exe 20% **aggregate** CPU cap and RAM commit budget, not an additional quota. Window title, rectangle, responsiveness, exit code, cancellation and pressure preemption are persisted. A window-observed outcome is **not** gameplay validation. Stopped, exited or hung programs and their test child descendants are terminated at cleanup; no third-party installer/Windows UAC bypass is introduced.

A GUI process may fail when run on a non-input desktop, have no visible top-level window, render via GPU in an unsupported way, or play audio. Windows GPU power and audio are **not** capped or muted. The source **has not been acceptance-tested on the user's Windows PC**. The separate desktop is **not a security sandbox**; trusted native programs execute with the current Windows user's privileges, and may access files and network. User approval is intentionally required per executable test, and the existing game's foreground focus is not manipulated by DeepThorT. Do **not** treat this as X4/RimWorld/Android unattended playtesting or screenshot/visual inspection. We deliberately avoid unsupported global keyboard injection or trying to hide arbitrary graphical games on the active desktop.

## Acceptance procedure on Windows

Use a disposable trusted Windows GUI demo executable stored in a test project folder; back up original user state. Check that a separate test window never appears in the active desktop, the foreground game retains focus, the test stops within 25 seconds and nothing survives via the nested test job. Inspect the Processes status and receipts. Repeat during a foreground game while monitoring RAM/CPU/GPU/audio and check **Stop isolated GUI test**; remember GPU contention can remain and sounds may still play. Verify a changed binary is denied; test after restarting to ensure no replay. If CreateDesktopW, nested-job assignment or EnumDesktopWindows is unsupported, the result must be a reported failure rather than an uncapped/invasive fallback. Run `tests/test_isolated_gui_v45.py` under actual Windows; Linux CI cannot prove Win32 desktop behaviour.

## Next

v46: engine-supplied Godot scripted gameplay probes with explicit assertions and physics/input telemetry where available, isolated offscreen rendering and genuine visual evaluation with screenshots only under a supported renderer, then Android emulator, RimWorld and X4 disposable-profile adapters. Ensure executable ownership, file/Steam profile backup, resolution/audio controls and a non-invasive GPU budget. True game/mod playtesting, automated repair based on runtime failures and APK installation remain outstanding.
