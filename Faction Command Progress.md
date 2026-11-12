# Faction Command Progress

Project: Faction Command (Android 2D space economy and faction management game)
Repository: Vardath/Vardath.github.io
Master specification: [Faction Command.md](Faction%20Command.md)

## Workflow contract
Each implementation pass must record date, task, changed paths, commit SHA, checks/workflow names, CI conclusion, tests, defects, and next step. A commit is not green until the relevant GitHub Actions checks for that exact SHA have completed successfully. Do not start the next implementation task while checks are failed, pending, absent, or unverified. Record the blocker and address it first.

## Pass 0 — Planning and specification
Date: 2026-11-13
Scope: Master design for an original Android map-driven space economy game; 300-sector/20–30-faction target, property management, roles, real economy, combat, policing, zoomable map, list-based station building with self-sufficiency, selective imports and construction queues.
Files: `Faction Command.md`; `Faction Command Progress.md`.
Plan commits: `4f9d207a68f28e935b927fbe3beccaeaf3690eec`, `b491b6651bbebd7732f9dcf29201cdeee2119739`.
Implementation: NOT STARTED.
CI status: NOT VERIFIED; do not infer green from successful GitHub file writes.
Tests: Not run; planning-only changes.
Known gaps: No Godot project, no game CI workflow, no Android APK or device validation yet.
Next task (only after verifying required checks for the current commits, or establishing a documented baseline gate): create Godot project skeleton, deterministic simulation harness, and initial CI configuration. Check the resulting commit is green before starting the next task.

## Pass template
### Pass N — [task]
- Date:
- Scope:
- Files changed:
- Commit SHA:
- CI workflow/check runs:
- CI result (success/failure/pending/missing/unverified):
- Automated tests:
- Manual/device tests:
- Defects and limitations:
- Next task / gate:

## Pass 1 — CI foundation bootstrap
- Date: 2026-11-13
- Scope: Added a path-scoped GitHub Actions workflow for future Godot headless project validation and test execution.
- Files changed: `.github/workflows/faction-command.yml`
- Commit SHA: `7c314701753caae37a83797fe31619998d9f6bbe`
- CI workflow/check runs: `Faction Command foundation` / `validate`, [run 43244532913](https://github.com/Vardath/Vardath.github.io/actions/runs/43244532913/job/131273529921), checked against the exact commit SHA.
- CI result: **SUCCESS**. Verified on 2026-11-13; the original status-only query had missed GitHub check runs.
- Automated tests: Not run or not confirmed. The bootstrap workflow intentionally skips Godot validation until a project exists.
- Manual/device tests: Not run.
- Defects and limitations: GitHub check visibility/trigger must be confirmed. The initial workflow is only a bootstrap gate, not Android APK export.
- Next task / gate: The bootstrap check succeeded. The Godot skeleton and test harness are the next task (Pass 2).

## Pass 2 — Godot project foundation
- Date: 2026-11-13
- Scope: Create the Godot project, original starter scenario, presentation-independent whole-tick world state, landscape command screen, and mandatory headless foundation tests. Harden the existing workflow to fail if the project or harness is missing.
- Files changed: `faction-command/` (project, starter data, UI, simulation, README and tests); `.github/workflows/faction-command.yml`; this journal.
- Source commits: `350ce71903c7a8ee5192f08f2c484f45fca4d7d2`, `484d9e9f52f1674d534758105875b043e840ca38` (both failed; see below), and fix `1c792df42ac9ea5d08725c259c537578e6306ca9` (passed).
- CI workflow/check runs: `Faction Command foundation` / `validate`.
- CI result: **SUCCESS** on `1c792df42ac9ea5d08725c259c537578e6306ca9`: [foundation validate](https://github.com/Vardath/Vardath.github.io/actions/runs/43247002575/job/131282240411) passed all 97 checks on Godot 4.4.1, and Pages build/deploy succeeded on the same SHA. Earlier commits `350ce71903c7a8ee5192f08f2c484f45fca4d7d2` and `484d9e9f52f1674d534758105875b043e840ca38` failed the layout check because the 4.4.1 headless runner used a 64×64 virtual window. The test now sets its intended landscape viewport explicitly.
- Automated tests: Local Godot 4.6.3 headless harness: 97 checks passed with both normal and 64×64 initial headless resolutions; JSON parsed successfully. CI uses Godot 4.4.1 and initially exposed a headless viewport mismatch.
- Manual/device tests: Desktop Godot screen opened; sector selection, ship selection, and pause/resume were exercised. Android device not tested.
- Defects and limitations: This is a foundation, not the playable economy. No ship orders, navigation, trading, persistence, station construction, Android export or APK yet. Screen scaling and touch require real-device verification.
- Next task / gate: Foundation check is green. Implement the first deterministic ship travel and order controls, then verify that task's exact commit before proceeding.
