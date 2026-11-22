# DeepThorT v35 — verification report (22 November 2026)

## Automated checks in this environment

- Python `compileall -q .`: passed.
- Headless Tk regression modules under isolated Xvfb displays via `regression_cli.py`: **53/53 modules passed; 430 tests observed; zero reported module failures.** Machine-readable per-module results in `TEST_RESULTS_V35.json`.
- New `tests/test_ui_help_v35.py`: all seven tests passed, covering fixed vendor links, refusal of arbitrary unknown URLs, text prompt tool-advisory categories, guide file URL, eight notebook descriptions, all existing primary button descriptions, and refusal to install after declining a vendor link.
- Existing v12 layout tests: passed in a separate focused run at 1320×860 and 1138×765.
- Actual v35 desktop UI was rendered under Xvfb and captured for the offline guide in `assets/overview.png` at 1320×960; this is a real GUI picture with no fabricated activity status.
- Release ZIP is generated from the original full v34 archive plus reviewed changed/new files. CRC integrity, full file preservation and an output SHA-256 are checked after packaging.

## Limitations: not passed and not claimed

- This Linux/Xvfb environment cannot run the shipped Windows executable, ONNX worker with user-installed model, Windows `winget`, elevated installers or actual software-management UI.
- Automated tests do not prove that every tooltip is correctly positioned at every Windows scaling factor; tomorrow's real Windows hover/F1 tests are required.
- The fixed official publisher page lookup is informational. No dynamic web search/download/installation workflow was shipped in v35.
- No actual X4, Blender, Godot, Android APK, RimWorld or GUI-only application operations were executed in this pass.
- The known combined-process Tkinter teardown failure is not claimed fixed; isolated modules avoid the nondeterministic shared event-loop teardown problem.
- No SHA256/signature verification of remote download files exists in v35. Consent/winget protections from v34 are unchanged.

## Required real-PC acceptance

Close the old application; back up `D:\deepthort\state`; extract the complete v35 package while preserving personal folders; check the guide button, F1 and hover help at your real Windows display scaling. Review a known official publisher page and decline an install; verify no installation starts. Finally test a small, disposable, approved local tool/verification command and send a diagnostic ZIP if it fails.
