# DeepThorT — v35 continuity, 22 November 2026

Baseline is the exact complete v34 Windows ZIP, not a reconstructed subset of older GitHub files. New capabilities are **offline self-help**, reviewed publisher links and passive broader tool recommendations; the source changes preserve the original model, JANUS/Sentinel, windows, memory and approval boundary.

**Changed:** `desktop_app.py`, `deepthort_local/computer_inventory.py`, `README.md`, `START HERE.txt`. **New:** `deepthort_local/ui_help.py`, `deepthort_local/tool_sources.py`, `USER_GUIDE.html`, `NEXT_STEPS.md`, `PROJECT_CONTEXT_V35.md`, `assets/overview.png`, `tests/test_ui_help_v35.py`.

The screenshot in the user guide was captured from the running Tk v35 desktop in an Xvfb test window; model not started, no project selected. Hover help is passive (delayed Tk `Toplevel`, no model or network), and every primary button has help text. F1/guide opens `file:///` local document. The reviewed official-source lookup uses a fixed dictionary of eight known package entries and asks before opening a browser; never interpret this as general web discovery or installer execution. The original winget install path remains approval-gated, unmodified.

**Engineering next:** actual Windows startup/hover and native installer acceptance, then P1 through P4 backlog in `NEXT_STEPS.md`, focusing on authenticated online discovery, verified safe download, exact installer approval, tool-specific adapters, requirements-linked tests, genuine game builds, and long-running autonomy. No automatic cloud inference fallback. Preserve maximum 20% total system CPU / 20% memory-commit restrictions when launched through the existing Windows executable, and priority to games.

**Verification scope:** Python compileall passed; 53/53 isolated Xvfb modules and 430 tests passed, with detailed output in `TEST_RESULTS_V35.json` and `TEST_RESULTS_V35.md`. ZIP CRC/integrity and source-v34 preservation are checked after packaging. These tests do not establish Windows model performance, elevated installer behavior, X4 gameplay, or Android/Blender builds. Existing monolithic Tk teardown warning is known.

**Install:** Exit program, back up `D:\deepthort\state`, extract v35 ZIP over `D:\deepthort`, preserving `state`, `models`, `node_modules`, `reference`, `cache`, all projects. Do not reset the GitHub repository or overwrite concurrent `Scratch-Chat` changes. Verification and GitHub source synchronization require distinct evidence; don't call a CI run green unless its success is observed.
