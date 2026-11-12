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

## Pass 3 — First ship travel orders
- Date: 2026-11-13
- Scope: Add deterministic route finding across the connected starter sectors, a queue of player ship fly-to orders, five-tick sector crossings, visible map movement, and destination/order controls. The ship panel scrolls to keep controls visible.
- Files changed: `faction-command/scripts/world.gd`, `galaxy_map.gd`, `main.gd`, `tests/run_tests.gd`, `README.md`, and this journal.
- Commit SHA: `ae4944e51aeefeeccc68f6f0fe6b1f3d595fa824`.
- CI workflow/check runs: `Faction Command foundation` / `validate`.
- CI result: **SUCCESS** on `ae4944e51aeefeeccc68f6f0fe6b1f3d595fa824`. [Foundation validate](https://github.com/Vardath/Vardath.github.io/actions/runs/43248122786/job/131286232609) passed all 123 checks on Godot 4.4.1; the Pages build and deployment also succeeded on the same SHA.
- Automated tests: Local Godot 4.6.3: 123 checks passed, including routing, reachability, queued order sequence, crossing timing, ownership, deterministic tick batching, and UI controls. CI uses Godot 4.4.1.
- Manual/device tests: Desktop Godot: queued First Light from Hearthreach to Vellum Gate; observed travel via Meridian and arrival after 10 ticks. Sector and ship selection, pause/resume and long-detail scrolling were inspected. Android device not tested.
- Defects and limitations: This is still an early prototype: no order cancellation, docking, trading, economy, save/load, station construction, Android export, or APK. Crossing times are placeholders, and touch/device performance remain unverified.
- Next task / gate: Green verified. Implement the user's newly requested faction-origin selection for new games while retaining an independent player faction; then verify the exact commit before proceeding.

## Pass 4 — Faction origin selection
- Date: 2026-11-13
- Scope: Add a new-game origin selector with four NPC factions, a preview of each starting sector and initial relations, and data-driven creation of the player's independent faction and ship. Record the chosen origin and current relations in world state.
- Files changed: `Faction Command.md` (design was updated in the preceding planning commit), `faction-command/data/starter_galaxy.json`, `scripts/world.gd`, `scripts/main.gd`, `tests/run_tests.gd`, `README.md`, and this journal.
- Commit SHA: `bf46de43016f057b0d27678d013810236518770b`.
- CI workflow/check runs: `Faction Command foundation` / `validate`.
- CI result: **SUCCESS** on `bf46de43016f057b0d27678d013810236518770b`. [Foundation validate](https://github.com/Vardath/Vardath.github.io/actions/runs/43249576281/job/131291371634) passed all 189 checks on Godot 4.4.1; Pages build and deployment also succeeded on the same SHA.
- Automated tests: Local Godot 4.6.3: 189 checks passed, including all four origins, complete relation tables, correct starting sectors, player ownership, unchanged NPC sector ownership, rejection of invalid origins, and menu interactions.
- Manual/device tests: Desktop Godot: previewed Vesper Guild, started in Vellum Gate with +20 Vesper relations, and verified the ship still belongs to the player's own faction. Android device not tested.
- Defects and limitations: Initial relations (+20 chosen faction, 0 others) are provisional. Save/load, reputation changes, economy, and Android export are not yet implemented; the origin and relations currently live only in memory.
- Next task / gate: Green verified. Implement persistence so the selected origin, evolving relations and orders can survive a restart; then check that task's exact commit before proceeding.

## Pass 5 — Saved games and recovery
- Date: 2026-11-13
- Scope: Add one offline save slot, manual saving, autosaving on new games, queued orders, pauses, app background/close and every 30 simulation ticks; add Continue and an overwrite confirmation. Preserve faction origin, relations, credits, crew, tick, orders and mid-crossing state. Use versioned, checksum-checked data, a verified temporary file and a previous-save backup.
- Files changed: `faction-command/scripts/save_store.gd`, `scripts/main.gd`, `tests/run_tests.gd`, `README.md`, and this journal.
- Commit SHA: `ff4f2593fe2fd46dffcdbb00b01d0bc781e6b47c`.
- CI workflow/check runs: `Faction Command foundation` / `validate`.
- CI result: **SUCCESS** on `ff4f2593fe2fd46dffcdbb00b01d0bc781e6b47c`: [foundation validate](https://github.com/Vardath/Vardath.github.io/actions/runs/43300489431/job/131470033032) passed all 219 checks on Godot 4.4.1; the Pages build and deployment also succeeded on the same SHA.
- Automated tests: Local Godot 4.6.3: 219 checks passed, including round-trip of a mid-journey multi-order game, deterministic continuation, changed relations, corrupted primary recovery, backup preservation, checksum and structural validation, unsupported versions, autosave, background pause, and overwrite confirmation. Test saves use isolated directories.
- Manual/device tests: Desktop Godot: queued a trip, saved during a crossing, restarted the game, confirmed the overwrite warning, and continued the saved journey. Android device not tested.
- Defects and limitations: One slot plus one previous-save backup; multiple save slots and migration from future formats remain future work. Autosave can lose up to 30 simulation ticks after an abrupt stop since the last event/save. There is no Android APK, trade or station construction yet.
- Next task / gate: Green verified. Implement the first physical economy and trading slice, then verify its exact commit before proceeding.

## Pass 6 — First physical trading loop
- Date: 2026-11-13
- Scope: Add four NPC markets, two wares, ship cargo and capacity, station inventories/storage and budgets, explicit sector-level docking, manual buy/sell, a transaction ledger and a trade screen. Trades transfer physical goods and credits atomically; failed trades leave the world unchanged. Upgrade pre-economy saves without resetting existing progress.
- Files changed: `faction-command/data/starter_galaxy.json`, `scripts/world.gd`, `scripts/main.gd`, `scripts/save_store.gd`, `tests/run_tests.gd`, `README.md`, and this journal.
- Source commit: `c6d3afb83a90667d8bb87169b019f2c6f12ae314`. Follow-up adds the full scrollable ledger; its exact SHA and final checks will be recorded after verification.
- CI workflow/check runs: `Faction Command foundation` / `validate`.
- CI result: **PENDING FOLLOW-UP**. The game check on `c6d3afb83a90667d8bb87169b019f2c6f12ae314` passed all 271 tests, but its Pages deployment was cancelled when newer X4 commits arrived. The later descendant `092bd9ae5872d20acdde4181949fb415c29501cb` retained the game changes and its Pages deployment succeeded. The same trading pass now adds a scrollable full ledger; verify that follow-up commit's exact checks before proceeding.
- Automated tests: Local Godot 4.6.3: 272 checks passed after the full-ledger improvement. Coverage includes a profitable two-way journey, cargo/credit conservation, docking and travel requirements, insufficient stock/credits/capacity, transaction atomicity and ledger, save/load, future-version protection, and migration of an older mid-journey save.
- Manual/device tests: Desktop Godot: loaded an earlier save, travelled to Vellum Gate, docked and bought alloy, carried it to Hearthreach, docked and sold it; cargo, station stock, balances and ledger reflected both trades. Android device not tested.
- Defects and limitations: Prices and initial inventories are fixed; stations do not yet produce or restock, NPCs do not trade, docking is an immediate sector-level action, and production is not yet simulated. There is no Android APK or station construction yet.
- Next task / gate: Verify the follow-up source commit's exact checks and record the result; then add deterministic production and replenishment from actual inputs before expanding trader automation.
