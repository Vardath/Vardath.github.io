# DeepThorT v30 development handover — 22 November 2026

## Current verified release

- Desktop release: `DeepThorT_Desktop_v30_Windows.zip`, built directly from local v29 source.
- Windows launcher/executable, ONNX model worker, JANUS worker and original GUI geometry unchanged.
- 368 Python tests passed in 45 independently isolated GUI/test modules (Xvfb, Linux).
- One combined-process test attempt suffered the previous Tkinter cross-thread destructor crash, so do not claim combined-run success.
- Real Windows X4 game execution, Godot editor/builds, Android APK production, and the Xenon PE implementation remain unverified.

## Implementation

- `engine_environment.py`: read-only, bounded selected-project toolchain inspection. Checks actual Godot executable paths (including user-set `GODOT_EXECUTABLE` and version-named binaries), Android Gradle/Java/SDK prerequisites and configured X4 game/extracted reference directories. It does not execute anything.
- `x4_reference_links.py`: bounded comparison of actual local macro/component references with selected extracted X4 vanilla index names, returning source fingerprints. Missing identifiers are unresolved, not automatically invalid due to DLC/other extensions.
- `engine_acceptance.py`: new full asset macro/component definitions under their expected `assets/.../macros` or `/components` folders must have matching local index entries; diffs are excluded. This is static registration only.
- `computer_inventory.py` and `desktop_app.py`: Existing Computer & Tools scan shows selected-project readiness; Godot approved verification command requires a real executable file rather than a registry hint. No UI changes, no automatic test execution.
- `engine_environment_cli.py`: read-only CLI for inspectable local environment evidence.
- Tests: `test_engine_environment_v30.py` plus updated Godot mocked-command and long asynchronous X4 GUI test cases.

## Next test required from the user's actual PC

1. Close DeepThorT and extract v30 over `D:\deepthort`, preserving models/state/cache/references/projects.
2. Select one actual X4 extension folder (containing `content.xml`) in DeepThorT.
3. Under Computer & Tools, point X4 paths at the installed game and extracted XML (if available), then click **Scan this computer**.
4. Use **Export diagnostics** and send the ZIP. Confirm whether X4 game dir is recognized, vanilla macro and component indexes are found, and the source-link report has unresolved references.
5. Do not treat this scan as an in-game Xenon PE mod test. On-PC tool invocation and save-compatible mod gameplay are later acceptance stages.

## Remaining work

- Real Windows tool process execution and measured performance, verified against actual games/SDKs.
- Actual vanilla PE macro/equipment reference checks using the user's extracted game files (not fabricated IDs).
- Verification of independent projectile damage 50,000 per hit, compatible installed weapons/turrets, player-only scope, respawn after 60 seconds and save compatibility.
- Godot/Android editor/build/packaging and game-simulation tests for Faction Command, using approval gates and requirement traceability.
- GitHub source synchronization must be explicitly verified; preparing a source-sync JSON alone is not a commit.
