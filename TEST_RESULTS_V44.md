# DeepThorT v44 regression evidence

## Focused validations (local Linux under Xvfb)

- `tests/test_quiet_playtest_v44.py`: deterministic headless CLI, Windows job-cap guard and idle flags, reject unsafe paths/executables, main-scene requirements, bounded audit, interruption recovery, CPU/RAM foreground pressure preemption, GUI action, a real simulated-engine subprocess, and no unwanted modal or application focus changes.
- v41 development cycle and v42 task graph GUI tests continue to pass in focused runs.

## Release gate

The entire suite must complete and pass on GitHub Actions against the final exact commit, with v44 source SHA-256 manifest verification and verified artifact. Source changes and installer overlays must not include `models`, `state`, `node_modules`, user projects or replace the original Windows launcher.

## Not validated by CI

Real Windows Job Object `QueryInformationJobObject` compatibility; actual Godot executable and scenes; physical GPU/load contention; Windows 20% CPU/RAM commit behaviour; real foreground application focus; X4/RimWorld install, launch, collision, docking or gameplay; Android emulator; actual ONNX repair efficacy.
