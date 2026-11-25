# DeepThorT v43 verification — 23 November 2026

## Focused local results

- New `tests/test_tool_verification_v43.py`: fixed immutable CLI version probes,
  explicit GUI no-execution classification, bounded timeouts, false exit-zero
  rejection, missing executable and registry-only detection, current-session
  PATH refresh, executable mutation invalidation, durable receipt history and
  desktop queue/game/installer gating.
- Previous `tests/test_software_autonomy_v39.py` continues to validate serial
  WinGet catalog installation, user preference, audit-before-launch and
  cancellation gates.

## Release requirements

The complete isolated Xvfb suite and source integrity check **must** run green
on the exact GitHub commit before announcing a verified release. The v43
source manifest hashes each changed source and document, and the build ZIP
must be CRC and SHA-256 checked. The unmodified ONNX inference server and
original launcher are not recompiled or silently replaced.

## Not verified on Linux

Physical Windows WinGet and UAC; real software publisher identity or signature;
actual local Qwen model repair quality; general application installation;
Android emulator or APK; Godot interactive gameplay; X4/RimWorld installation
and save compatibility; Windows 20% system cap and game-priority behaviour.
