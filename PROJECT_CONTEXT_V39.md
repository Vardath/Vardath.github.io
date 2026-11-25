# DeepThorT v39 — engineering handover (23 November 2026)

## Constraint and direction

Owner explicitly requests less micromanagement: routine project tool installs
and upgrades should run without asking for permission at every action. When
Windows itself needs administrator elevation, Windows should continue to present
its ordinary UAC prompt. **ONNX remains the only conversational model.** No
Scratch Chat dependencies, external AI calls or changes to JANUS/Sentinel.

## Changes

- `deepthort_local/software_autonomy.py`: visible persistent routine policy,
  curated ID-only commands (`winget install` / `winget upgrade`), audit hashes,
  project tool planning and bounded retry/cooldown rules. No model-made shell
  commands, arbitrary URLs, `--all`, bypass flags or UAC workaround.
- `deepthort_local/computer_inventory.py`: broaden the curated WinGet catalog
  for actual creative and technical workflows, including Java 21 LTS, FFmpeg,
  Audacity, LibreOffice, Inkscape, GIMP, Krita, FreeCAD, Pandoc and 7-Zip.
  `plan_tool_needs` is still a keyword heuristic, NOT a full dependency graph.
- `deepthort_local/tool_sources.py`: fixed reviewed vendor page references for
  the expanded catalog; these are informational, not independent signatures.
- `desktop_app.py`: add two explicit persistent controls in Computer & Tools.
  **Only an approved and queued build plan** can create automatic tool work;
  draft plans and ordinary chats cannot. Maximum 3 tools/request, one active
  process, game/queue/disk/process gates, 3600-second supervised limit,
  2 MiB output limit, interrupt-aware audit and rescan after exit code zero.
  Network search and exact-ID inspection buttons themselves imply the user's
  intention to run those *read-only* queries when policy is enabled; redundant
  per-query Yes dialogs are removed. Manual fixed-tool install similarly has
  no second dialog while standing permission is on.
- `reviewed_install.py`: exact-ID inspected package may be installed/upgraded
  with standing policy plus explicit **Install inspected package…** click;
  avoids misrepresenting that click as a typed confirmation in persisted audit.
  Manual mode retains old v38 typed confirmation semantics. No automatic
  arbitrary package selection or running downloaded raw executables.
- `ui_help.py`, `USER_GUIDE.html`, `assets/overview_v39.png`, `NEXT_STEPS.md`
  reflect actual UI, boundaries, new routine policy and future autonomy work.
- `tests/test_software_autonomy_v39.py` uses mocked executables, catalog rows,
  persistence and GUI paths; does not install or elevate anything.

## Critical limitations

Only the tool management path is made more autonomous. Project source edits,
model-proposed procedures and individual engine test runs still have prior
approvals. The next pass should implement *project-scoped standing permissions*
for bounded reversible file edits and verified tests, not global unbounded
shell execution. Record exact requirement/project boundaries and Git backups.
Unknown software still requires human selection of the package ID, inspection
and an explicit install-button click. Source metadata from the WinGet community
catalog is not independent provenance; package hash checks are WinGet's own.
Windows UAC interaction, installer child processes and actual tool success have
not been tested on the target Windows PC. Do not claim production verification
from simulated subprocess tests or Linux GUI tests. Continue to respect 20%
resource caps, game priority and durable state. Retain original code when
merging with unrelated Scratch Chat commits in the website repository.

## Test protocol

1. Backup state, close the app, extract over D:\deepthort; press F1, check
   hover tips, verify the two policy checkboxes in Computer & Tools.
2. With a **disposable** Godot or Python project and a required missing tool,
   draft and approve a plan. Check Processes: a fixed WinGet ID should be
   queued automatically. No DeepThorT Yes prompt should recur. If Windows
   normally requires UAC, it must remain visible.
3. Toggle **Allow tool upgrades** off, approve a second test plan, verify
   existing tools are not upgraded. Toggle routine software management off,
   verify no new routine installs are queued. Existing running installs may
   need separate cancellation.
4. Test a known package manually, then an exact-ID inspected package under
   standing policy (prefer a disposable Windows VM). Verify audit source.
5. Export diagnostics and collect actual WinGet output, process and feature
   verification. Do not use unverified unknown packages on your main machine.

Baseline: v38 full release, GitHub commit
`09c3e5f889b69e342ad596798271724aeedf92cd` with 460 passing tests / 57
modules in Actions run 45070583842. v39 results are recorded separately.
