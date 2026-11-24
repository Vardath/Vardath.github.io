**v44 implementation status:** A real headless Godot scene smoke-test runner now exists; this document's remaining acceptance criteria are still unimplemented. A `headless_smoke_passed` result is only evidence that the launched process exited zero, not that any scene mechanic or graphical behaviour was correct. Visible playtests and X4/RimWorld game execution still need separate platform adapters.

# DeepThorT build, install, launch and playtest acceptance contract

**Status: forward design, NOT an implemented v43 playtesting feature.**
The v43 code independently locates and version-probes selected development
software. v42 already performs bounded approved source generation and fixed
headless checks. Neither proves that an application or game can be played.

A project should be recorded as `playtested` only with all of the following:

1. The requested source and assets exist, with hashes and approval scope.
2. The real target build succeeds and the expected artifact is actually on disk.
3. An isolated or explicitly approved install/staging step uses a known target
   and preserves existing user files, saves and mods; UAC remains native.
4. The real target runtime launches (not merely a compiler or static analyzer).
5. The adapter observes process start, time-bounded behaviour, testable input
   and output, crashes and diagnostics. A script returning zero alone is not
   proof of successful interaction.
6. Acceptance checks are derived from the approved requirements and supported
   by runtime observations: real windows/scenes, UI actions, player/ship/pawn
   state, filesystem artifacts or in-game logs. Visual observation and human
   sign-off are required when instrumentation cannot support a claim.
7. Failure yields bounded diagnosis, source revision, reinstallation/relaunch
   where safe, retesting and recoverable checkpoints, with an explicit stop.
8. The report distinguishes tested, not tested, blocked, unobservable and
   failed requirements. Never mark non-observed behaviour successful.

## Platform-specific future adapters

- **Windows desktop programs:** controlled launch in a test account/profile,
  GUI automation only after selecting the correct window, operations and
  prompts, bounded screenshots/log captures, exit/crash detection.
- **Godot games:** headless import first, real play mode separately, scene
  telemetry and scripted player input, screenshot comparison, physics/docking
  or gameplay assertions relevant to the game, resource-aware stop.
- **Android games:** verified Java/Android SDK, actual Gradle APK build,
  explicit ADB device/emulator selection and consent, install with a separate
  package ID, launch/activity/UI observations and logcat crash reporting.
- **X4 Foundations mods:** deploy as a separate extension in a disposable
  test profile (never overwrite game archives), check XML/source references,
  start the actual game, verify ship spawn/equipment and ownership, takeoff,
  docking, passenger access, asteroid-model collision, save/reload and loss
  respawn; inspect real debug logs. Some of these require direct gameplay
  observation and cannot be inferred from a build log.
- **RimWorld mods:** test installation in a separate mod profile, start game,
  read load-order/error logs and run scenario/ability interaction checks. A
  successful XML parse is not proof that pawns, turrets or gravships work.

By default, the adapter must never overwrite a live game profile, save, source
checkout, Android device data or existing installation without a specific
approved and reversible operation. Tests may run untrusted generated code;
Windows normal user permissions are not a sandbox. Game-aware resource limits,
UAC and the original GUI controls remain mandatory.
