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
- Source commits: `c6d3afb83a90667d8bb87169b019f2c6f12ae314`; full-ledger follow-up `4f4ec2caf46914ded578f89d2af9e55d8509a834`.
- CI workflow/check runs: `Faction Command foundation` / `validate`.
- CI result: **SUCCESS** on `4f4ec2caf46914ded578f89d2af9e55d8509a834`: [foundation validate](https://github.com/Vardath/Vardath.github.io/actions/runs/43303271352/job/131479768707) passed all 272 checks on Godot 4.4.1; Pages build and deployment also succeeded on that SHA. The earlier `c6d3afb83a90667d8bb87169b019f2c6f12ae314` game check passed 271 tests, but its Pages deployment was cancelled when newer X4 commits arrived. The later descendant `092bd9ae5872d20acdde4181949fb415c29501cb` retained the game changes and its Pages deployment succeeded.
- Automated tests: Local Godot 4.6.3: 272 checks passed after the full-ledger improvement. Coverage includes a profitable two-way journey, cargo/credit conservation, docking and travel requirements, insufficient stock/credits/capacity, transaction atomicity and ledger, save/load, future-version protection, and migration of an older mid-journey save.
- Manual/device tests: Desktop Godot: loaded an earlier save, travelled to Vellum Gate, docked and bought alloy, carried it to Hearthreach, docked and sold it; cargo, station stock, balances and ledger reflected both trades. Android device not tested.
- Defects and limitations: Prices and initial inventories are fixed; stations do not yet produce or restock, NPCs do not trade, and docking is an immediate sector-level action. There is no Android APK or station construction yet.
- Next task / gate: Green verified. Add deterministic production and replenishment from actual inputs before expanding trader automation; verify that task's exact commit before proceeding.

## Pass 7 — Resource-backed station production
- Date: 2026-11-13
- Scope: Add Ore, data-driven production recipes and fixed-tick modules. Solar arrays use an explicit renewable sunlight source; an extractor consumes Energy Cells and a finite ore deposit; a smelter consumes Ore and Energy Cells to produce Alloy Plates. Inputs and output change atomically at cycle completion, and shortages or full storage pause progress. Show recipes, progress, shortages and remaining deposits in the Trade screen. Upgrade older saves without resetting existing inventories, credits, trade rules, ships, orders, relations or ledger.
- Files changed: `faction-command/data/starter_galaxy.json`, `scripts/world.gd`, `scripts/main.gd`, `scripts/save_store.gd`, `tests/run_tests.gd`, `README.md`, and this journal.
- Commit SHA: `e54945dc8fa80ef5ac853014aa821fe01743915c`.
- CI workflow/check runs: `Faction Command foundation` / `validate`.
- CI result: **SUCCESS** on `e54945dc8fa80ef5ac853014aa821fe01743915c`: [foundation validate](https://github.com/Vardath/Vardath.github.io/actions/runs/43307692468/job/131495219567) passed all 340 checks on Godot 4.4.1; Pages build and deployment also succeeded on the same SHA.
- Automated tests: Local Godot 4.6.3: 340 checks passed. Coverage includes production timing, physical inputs and deposit depletion, shortages and recovery, full storage, competing modules, deterministic save/load mid-cycle, older-save migration, unsupported schema protection and a 2,000-tick run.
- Manual/device tests: Desktop Godot: loaded a prior trading save and inspected solar, smelter and extractor recipes, shortage states and remaining deposit on the market screen. Android device not tested.
- Defects and limitations: Player deliveries are required; NPC traders, dynamic prices, player-built stations and Android export remain unimplemented. Solar energy is an abstract renewable natural input; existing saves receive no free initial ore stock. Production runs at the same fidelity in all sectors and has not been profiled at the planned galaxy scale.
- Next task / gate: Green verified. Implement NPC logistics and autonomous trading against actual inventories, budgets, routes and station needs; verify that task's exact commit before proceeding.

## Pass 8 — Autonomous faction supply freighter
- Date: 2026-11-13
- Scope: Add one NPC-owned autonomous freighter that receives working capital from its own station, identifies profitable factory input shortages, buys actual station stock, travels over sector links, docks and sells physical cargo against station budgets and storage. Revalidate deals at arrival; retain cargo and seek another buyer or wait when conditions change. Display faction traffic and identify each actor in the shared ledger. Upgrade previous saves without resetting player property, finances, orders, station stock or production.
- Files changed: `faction-command/scripts/npc_trade.gd`, `scripts/world.gd`, `scripts/galaxy_map.gd`, `scripts/main.gd`, `scripts/save_store.gd`, `tests/run_tests.gd`, `README.md`, and this journal.
- Commit SHA: `6fdca21863eb93d0a8524866893c7a1b6af16870`.
- CI workflow/check runs: `Faction Command foundation` / `validate`.
- CI result: **SUCCESS** on `6fdca21863eb93d0a8524866893c7a1b6af16870`: [foundation validate](https://github.com/Vardath/Vardath.github.io/actions/runs/43310523690/job/131505098268) passed all 388 checks on Godot 4.4.1; Pages build and deployment also succeeded on the same SHA.
- Automated tests: Local Godot 4.6.3: 388 checks passed. Coverage includes real station funding, travel and input delivery, credit and cargo invariants, player/NPC ownership, stock disappearing, an insolvent buyer, missing destinations, save/load mid-trip, migration, and a 2,000-tick NPC economy run.
- Manual/device tests: Desktop Godot: loaded an earlier save, watched the NPC diamond travel across the map, inspected its sector traffic and observed its separately identified funding, purchase and sale in the transaction ledger. Android device not tested.
- Defects and limitations: Only one prototype NPC trader; player-selectable trading roles, dynamic pricing, diplomacy checks, more factions/ships and Android export remain unimplemented. Long-run and galaxy-scale device performance are not yet profiled.
- Next task / gate: Green verified. Implement a player-owned autonomous trader role with real routes, cargo, station constraints and ledger entries; verify that task's exact commit before proceeding.

## Pass 9 — Player-owned autonomous trader
- Date: 2026-11-12 (UTC).
- Scope: Add an opt-in trader role for player-owned ships. It spends the player's credits on real factory supply runs, observes routes, stock, prices, budgets and cargo/storage limits, records purchases and sales, preserves manually acquired cargo, and revalidates interrupted or unavailable trades. Manual orders remain queued and take precedence before the role resumes; disabling the role leaves existing orders and cargo intact. Upgrade older saves without enabling automation or resetting their world.
- Files changed: `faction-command/scripts/world.gd`, `scripts/npc_trade.gd`, `scripts/main.gd`, `scripts/save_store.gd`, `tests/run_tests.gd`, `README.md`, and this journal.
- Commit SHA: `3b3bad72208f8d7ff9005a2965a4b2feca1a3fa1`.
- CI workflow/check runs: `Faction Command foundation` / `validate`; Pages build and deployment.
- CI result: **SUCCESS** on `3b3bad72208f8d7ff9005a2965a4b2feca1a3fa1`: [foundation validate](https://github.com/Vardath/Vardath.github.io/actions/runs/43321943084/job/131544563979) passed all 430 checks on Godot 4.4.1; Pages build and deployment also succeeded on the same SHA.
- Automated tests: Local Godot 4.6.3: 430 checks passed, including role opt-in, real purchases and sales, player and NPC credit conservation, retained pre-existing cargo, manual sales and queued orders, unavailable buyers, insufficient funds, save/reload in transit, migration, unsupported save versions and concurrent traders.
- Manual/device tests: Desktop Godot: selected Auto trader, resumed time, observed First Light buy eight Energy Cells, travel to Vellum Gate and sell them; both transactions appeared in the ledger. Android device not tested.
- Defects and limitations: One prototype player ship and one NPC trader; traders target factory input shortages and use fixed prices. Orders are queued rather than instantly interrupted. Android export and device testing, station construction, dynamic prices and broader roles remain unimplemented.
- Next task / gate: Green verified. Configure the Android debug export pipeline and CI artifact build; physical-device testing remains required.

## Pass 10 — Android debug APK pipeline
- Date: 2026-11-12 (UTC).
- Scope: Add a Godot Android export preset for ARM64 and ARMv7, include the starter-galaxy data in exported builds, configure Godot's Android texture import, and extend game CI to create and verify a signed test APK and upload it with a checksum. A public debug-only signing key and distinct debug package ID keep test-build updates compatible; release signing remains separate.
- Files changed: `.github/workflows/faction-command.yml`, `faction-command/export_presets.cfg`, `project.godot`, `.gitignore`, `build_support/public-debug.keystore.b64`, `README.md`, `Faction Command.md`, and this journal.
- Initial source commit: `34cc59812f94941aac922e62db120371ad0c715c` (workflow rejected before jobs started); corrected source commit: `1fda2d1f8e24487357e771a0cb02799b7def008c`.
- CI workflow/check runs: `Faction Command foundation` / `validate` and `android-debug`; Pages build and deployment.
- CI result: **SUCCESS** on `1fda2d1f8e24487357e771a0cb02799b7def008c`: [validate and Android debug](https://github.com/Vardath/Vardath.github.io/actions/runs/43323441341) passed, including all 430 Godot 4.4.1 checks, APK signing, ARM64/ARMv7 and embedded galaxy-data checks; Pages build and deployment also succeeded. The initial commit's workflow was rejected before jobs started; the follow-up replaced the unsupported job-level `runner` context.
- Automated tests: Local Godot 4.6.3 passed 430 foundation checks, imported the project, and exported a resource pack containing `data/starter_galaxy.json`; workflow YAML parsed and the public debug key was verified. Android APK export runs in GitHub Actions because the local Android SDK and templates are unavailable.
- Artifact verification: Downloaded `FactionCommand-Android-debug`; the APK checksum matched, its embedded starter galaxy matched the source, and its package metadata identified ARM64 and ARMv7. The GitHub artifact expires 2026-12-12.
- Manual/device tests: No Android device test yet.
- Defects and limitations: This is a debug-only build signed with a public test key, not a production release. Actual installation, touch layout, playability, performance and save survival on Android remain unverified.
- Next task / gate: Green verified. Continue the vertical slice with galaxy-map pan and zoom and sector-level navigation; physical-device installation and playtesting remain required.

## Pass 11 — Accessible galaxy and sector navigation
- Date: 2026-11-13 (Australia/Brisbane).
- Scope: Record the goal of X4-level depth with simple, progressively disclosed controls. Add pinch, drag, mouse-wheel and button zoom/pan to the galaxy and sector views; provide Fit and a simple sector overview of real connections, stations and ships. Selecting a connection opens its neighboring sector, a station opens its existing market and production details, and a ship shows its current details. Camera changes do not modify simulation or save data.
- Files changed: `Faction Command.md`, `Faction Command Progress.md`, `faction-command/scripts/map_interaction.gd`, `galaxy_map.gd`, `sector_map.gd`, `main.gd`, `tests/run_tests.gd` and `README.md`.
- Commit SHA: `3fc74a3b8013330693a8c45596557f86ebfe8b00`.
- CI workflow/check runs: `Faction Command foundation` / `validate` and `android-debug`; Pages build and deployment.
- CI result: **SUCCESS** on `3fc74a3b8013330693a8c45596557f86ebfe8b00`: [foundation validate](https://github.com/Vardath/Vardath.github.io/actions/runs/43335865996/job/131591746693) passed 454 checks on Godot 4.4.1, [Android debug](https://github.com/Vardath/Vardath.github.io/actions/runs/43335865996/job/131591904239) exported and verified the APK, and Pages build and deployment succeeded.
- Automated tests: Local Godot 4.6.3 passed 454 checks at the intended landscape viewport and under the 64×64 headless display override. Coverage includes touch taps, panning, pinch zoom, anchored coordinates, zoom bounds and reset, selecting real entities after transforms, live ship movements, queued orders, save-state preservation and visible map controls. A local resource-pack export included the new scripts.
- Artifact verification: Downloaded the rebuilt APK, verified its checksum and embedded galaxy data, confirmed both new map scripts were packaged, and checked that the package and signing certificate match the previous debug build.
- Manual/device tests: Desktop Godot: zoomed the galaxy, opened a sector, opened a station market and followed a connection to its actual neighboring sector. Android touch and device playtesting remain unverified.
- Defects and limitations: Sector view is explicitly schematic: intra-sector spatial positions, tactical movement, combat and continuous galaxy-to-sector zoom are not implemented. More fleets, sectors and station objects will need scale and layout profiling.
- Next task / gate: Green verified. Begin the station planner's module selection, quantities and sourcing preview, while retaining the longer-term goal of a physical construction queue.

## Pass 12 — Station production planner preview
- Date: 2026-11-13 (Australia/Brisbane).
- Scope: Add a read-only station planner with module quantities, touch-sized increment/decrement controls and self-sufficient, selective-import and import-all modes. Calculate supporting whole modules and per-60-tick production, consumption, imports and surplus from the current recipes; aggregate shared inputs and respect explicitly selected production. Warn about unsurveyed sunlight and finite deposits, missing producers and cyclic dependencies. Improve galaxy-map label placement when names overlap markers.
- Files changed: `Faction Command Progress.md`, `faction-command/scripts/station_planner.gd`, `main.gd`, `galaxy_map.gd`, `tests/run_tests.gd` and `README.md`.
- Commit SHA: `229259859dffc89ddbf77edeefb8143f3665cecb`.
- CI workflow/check runs: `Faction Command foundation` / `validate` and `android-debug`; Pages build and deployment.
- CI result: **SUCCESS** on `229259859dffc89ddbf77edeefb8143f3665cecb`: [foundation validate](https://github.com/Vardath/Vardath.github.io/actions/runs/43337881128/job/131598585607) passed 482 checks on Godot 4.4.1, [Android debug](https://github.com/Vardath/Vardath.github.io/actions/runs/43337881128/job/131598764981) exported and verified the APK, and Pages build and deployment succeeded.
- Automated tests: Local Godot 4.6.3 passed 482 checks, including whole-module rounding, shared inputs, all three sourcing modes, mixed local/imported stock, unavailable recipes, cycle detection and startup warning, unchanged world state, touch-sized planner controls and non-overlapping map labels. The landscape and headless viewport tests passed; the Android resource pack included the planner.
- Artifact verification: Downloaded the rebuilt APK, verified its checksum, embedded galaxy data and planner script, and confirmed that its package and signing certificate match the preceding debug build.
- Manual/device tests: Desktop Godot: chose an alloy smelter, inspected the suggested ore and energy modules, and selected ore imports to see the ore module removed and its import rate displayed. Android device testing remains outstanding.
- Defects and limitations: The planner is a temporary preview using three production recipes. Plans are not saved, priced or constructed. Local resources have not been surveyed; advanced recipes, workforce, transport, budgets and physical construction remain future work. The galaxy label layout has not been profiled at the planned full scale.
- Next task / gate: Green verified. Implement the next construction stage with defined costs, physical materials and a persistent queue.

## Pass 13 — Physical station construction
- Date: 2026-11-13 (Australia/Brisbane).
- Scope: Turn station plans into player-owned build sites with upfront builder hire, actual construction materials, a persistent module queue and a physically travelling NPC builder. Materials are purchased and delivered by ship into separate build storage; each module consumes its materials and work time before adding functional production and storage. Allow pausing, resuming and free ship-to-owned-station cargo transfers. Player stations share finite, surveyed sector resources. Upgrade existing saves and protect unknown future construction formats.
- Files changed: `Faction Command Progress.md`, `.github/workflows/faction-command.yml`, `faction-command/data/construction.json`, `faction-command/scripts/construction.gd`, `station_planner.gd`, `world.gd`, `save_store.gd`, `main.gd`, `tests/run_tests.gd` and `README.md`.
- Commit SHA: `bbe86961b5887ac6b1a5c37fbdb8cc947ac453f9`.
- CI workflow/check runs: `Faction Command foundation` / `validate` and `android-debug`; Pages build and deployment.
- CI result: **SUCCESS** on `bbe86961b5887ac6b1a5c37fbdb8cc947ac453f9`: [foundation validate](https://github.com/Vardath/Vardath.github.io/actions/runs/43342516626/job/131613979038) passed 546 checks on Godot 4.4.1, [Android debug](https://github.com/Vardath/Vardath.github.io/actions/runs/43342516626/job/131614217244) exported and verified the APK, and [Pages build and deployment](https://github.com/Vardath/Vardath.github.io/actions/runs/43342516105) succeeded.
- Automated tests: Godot 4.6.3 passed 546 foundation checks at the landscape viewport and with a 64×64 headless display override. Coverage includes fee conservation, purchase and delivery of real cargo, builder travel, waiting for materials, pause/resume, saving and reloading mid-build, station production, shared finite deposits, old-save migration, future-version protection and the game controls. A local Android resource-pack export included the construction data and compiled script.
- Artifact verification: Downloaded the Android APK from the verified build, checked the artifact and APK SHA-256 checksums, confirmed the packaged construction data matches the source and the compiled construction script is present, and verified the package, ARM architectures and signing certificate match the previous debug build. Updated the existing test APK to version 3.
- Manual/device tests: In desktop Godot, inspected the construction quote and finite reserve, placed a site and checked its build queue and material requirement. Android device playtesting remains outstanding.
- Defects and limitations: The builder fee is paid up front; cancellation, refunds and reordering are not yet available. Only one NPC builder and three production modules are implemented. Build materials and imported inputs must be delivered manually, and station positioning remains schematic.
- Next task / gate: Green verified. Continue construction and station logistics, including practical ways to supply sites and manage or cancel queued builds.

## Pass 14 — Automatic build-site supply
- Date: 2026-11-13 (Australia/Brisbane).
- Scope: Assign the player's ship to automatically supply a selected build site. Deliver relevant cargo already aboard, collect from owned station stock, or purchase real materials from reachable NPC markets with faction credits. Respect actual stock, prices, hold capacity and physical travel; repeat trips and account for other suppliers' cargo en route. Show waiting reasons, allow a player to stop or change role while keeping cargo and queued orders, and persist active trips across save/load. Present material shortages and supply controls in the build screen.
- Files changed: `Faction Command Progress.md`, `.github/workflows/faction-command.yml`, `faction-command/scripts/build_supply.gd`, `world.gd`, `save_store.gd`, `main.gd`, `tests/run_tests.gd` and `README.md`.
- Commit SHA: `8f3f4754b99e55c65285e52256ef6b80906cf5a4`.
- CI workflow/check runs: `Faction Command foundation` / `validate` and `android-debug`; Pages build and deployment.
- CI result: **SUCCESS** on `8f3f4754b99e55c65285e52256ef6b80906cf5a4`: [foundation validate](https://github.com/Vardath/Vardath.github.io/actions/runs/43359506770/job/131669401530) passed 577 checks on Godot 4.4.1, [Android debug](https://github.com/Vardath/Vardath.github.io/actions/runs/43359506770/job/131669534755) exported and verified the APK, and [Pages build and deployment](https://github.com/Vardath/Vardath.github.io/actions/runs/43359505707) succeeded.
- Automated tests: Godot 4.6.3 passed 577 foundation checks in the landscape viewport and with a 64×64 headless display override. Coverage includes multi-trip supply, stock and credit conservation, a save in transit, waiting and resuming, full cargo, changing role, multiple suppliers avoiding duplicate purchases, owned stock, existing-save migration and future-version protection. A local Android resource pack includes the new compiled supply script.
- Artifact verification: Downloaded the verified Android build; checked artifact and APK SHA-256 checksums, embedded construction data, compiled supply script, package and ARM architectures. The signing certificate matches the prior debug build. Updated the test APK to version 4.
- Manual/device tests: In desktop Godot, created a station and assigned its supply ship; checked the visible cost warning, assignment feedback and stop control. Android device testing remains outstanding.
- Defects and limitations: The interface currently assigns First Light; broader property selection is future work. Supply uses faction credits without a separate player-set budget. It supplies construction materials, not ongoing station-production imports. Build cancellation, refunds and reordering remain unavailable.
- Next task / gate: Green verified. Continue construction management and station logistics, including cancellation, recovery of materials and handling of the builder fee.

## Pass 15 — Historical archives, media and data copying
- Date: 2026-11-13 (Australia/Brisbane).
- Scope: Extend the master plan for faction-maintained archives, diverse civilizations, physical media, player archives, data manufacture and future research. Add four faction-owned archive stations with 20 original records, named media, homeworlds and research subjects. Visiting a station and docking opens its collection; visits persist. Model faction funding, staff pay and energy upkeep using existing funds and physical stock; traders can supply archives. Add Blank Media and Recorded Data wares and buildable Media Workshop and Archive Scriptorium modules. Faction archives retain their catalogue as a source; player scriptoria need a reusable data source and consume media and energy per copy.
- Files changed: `Faction Command.md`, `Faction Command Progress.md`, `.github/workflows/faction-command.yml`, `faction-command/data/archives.json`, `faction-command/scripts/archives.gd`, `world.gd`, `npc_trade.gd`, `sector_map.gd`, `save_store.gd`, `main.gd`, `station_planner.gd`, `tests/run_tests.gd` and `README.md`.
- Commit SHA: `e1f7e50866820e85b88e527fc5e86243a446ef2d`.
- CI workflow/check runs: `Faction Command foundation` / `validate` and `android-debug`; Pages build and deployment.
- CI result: **SUCCESS** on `e1f7e50866820e85b88e527fc5e86243a446ef2d`: [foundation validate](https://github.com/Vardath/Vardath.github.io/actions/runs/43362179717/job/131678017445) passed 669 checks on Godot 4.4.1, [Android debug](https://github.com/Vardath/Vardath.github.io/actions/runs/43362179717/job/131678179655) exported and verified the APK, and [Pages build and deployment](https://github.com/Vardath/Vardath.github.io/actions/runs/43362179025) succeeded.
- Automated tests: Local Godot 4.6.3 passed 669 checks at the intended landscape viewport and with a 64×64 headless display override. Coverage includes faction ownership, docking and visits, credit conservation, funding and wages, real energy and alloy supply, non-consumed historical originals and reusable data sources, player-built copying, a 2,000-tick autonomous economy, save/reload during production, old-save migration, future-version protection and screen controls. The local Android resource pack contains archive data and the compiled archive script.
- Artifact verification: Downloaded the verified Android build and checked the artifact and APK SHA-256 checksums, archive data against the source, compiled archive script, package, ARM architectures and unchanged debug signing certificate. Updated the test APK to version 5.
- Manual/device tests: Desktop Godot: opened the starting sector, selected and docked at the Auroran archive, and read its collection. Android-device playtesting remains outstanding.
- Defects and limitations: The 20 entries are a starting collection, not the intended full-depth lore. Media and recorded data are aggregate wares, without individual copied-item provenance or player-owned catalogues. Research subjects are shown, but research projects and bonuses are not implemented. The current economy has only one NPC trader and one builder; automatic station-production imports, construction cancellation/refunds and reordering remain future work.
- Next task / gate: Green verified. Continue the broader plan, expanding source-specific collections and connecting relevant archive evidence to research projects in later passes.

## Pass 16 — Research and archive references
- Date: 2026-11-13 (Australia/Brisbane).
- Scope: Add a buildable Research Laboratory that consumes Recorded Data and Energy Cells to make Research Notes. The player selects one active project and lab; notes produce progress, while distinct visited archives contribute subject-matched bonuses with a cap. Display contributing archives, topics, progress and rewards; allow pausing and switching without losing progress. Three projects reduce the cycle time of player-owned scriptoria, media workshops or ore extractors, with updated planner rates and no effect on NPC stations. Reserve a reusable scriptorium source from other modules at the same station.
- Files changed: `Faction Command.md`, `Faction Command Progress.md`, `.github/workflows/faction-command.yml`, `faction-command/data/research.json`, `faction-command/scripts/research.gd`, `world.gd`, `save_store.gd`, `station_planner.gd`, `main.gd`, `tests/run_tests.gd` and `README.md`.
- Commit SHA: `5583930bc823ca5f256e29fe68bd759574c530ce`.
- CI workflow/check runs: `Faction Command foundation` / `validate` and `android-debug`; Pages build and deployment.
- CI result: **SUCCESS** on `5583930bc823ca5f256e29fe68bd759574c530ce`: [foundation validate](https://github.com/Vardath/Vardath.github.io/actions/runs/43410991890/job/131837063377) passed 751 checks on Godot 4.4.1, [Android debug](https://github.com/Vardath/Vardath.github.io/actions/runs/43410991890/job/131837249498) exported and verified the APK, and [Pages build and deployment](https://github.com/Vardath/Vardath.github.io/actions/runs/43410991010) succeeded.
- Automated tests: Local Godot 4.6.3 passed 751 checks at the landscape viewport and with a 64×64 headless display override. Coverage includes an actual built and supplied laboratory, note production and consumption, relevant and unrelated archive visits, duplicate and capped bonuses, pause/switch and mid-cycle save/load, all three player-only effects and planner rates, finite deposits, reserving a reusable data source, save migration and future-version protection. A local Android resource-pack export included research data and the compiled script.
- Artifact verification: Downloaded the verified Android build and checked the artifact and APK SHA-256 checksums, research data against the source, compiled research script, package, ARM architectures and unchanged debug signing certificate. Updated the test APK to version 6.
- Manual/device tests: Desktop Godot: opened a legitimately constructed laboratory in an isolated test save, inspected the research project, its archive bonus and reward, and started it to see the materials wait. Android-device playtesting remains outstanding.
- Defects and limitations: Research currently has three projects and one active project at one selected laboratory. Archive visits provide general learned references, not source-specific copies; Recorded Data remains an aggregate ware. Research staff, prerequisites, complex discoveries and individual collections are future work. Station production imports remain manual; construction cancellation/refunds and reordering remain unavailable.
- Next task / gate: Green verified. Continue broader station logistics, research depth and source-specific archive collections.

## Pass 17 — Budgeted station input supply
- Date: 2026-11-14 (Australia/Brisbane).
- Scope: Add an ongoing player station-supplier role. It delivers matching cargo, collects surplus above working-input and reusable-source reserves from player stations, or physically buys and transports inputs within a player-set total assignment cap. Targets reflect net production demand, storage, reusable sources and exhausted deposits. The existing construction-supplier role also protects working stock. Add station controls, role status and save migration.
- Files changed: `Faction Command.md`, `Faction Command Progress.md`, `.github/workflows/faction-command.yml`, `faction-command/scripts/station_supply.gd`, `build_supply.gd`, `world.gd`, `save_store.gd`, `main.gd`, `tests/run_tests.gd` and `README.md`.
- Commit SHA: Pending verification.
- CI workflow/check runs: `Faction Command foundation` / `validate` and `android-debug`; Pages build and deployment.
- CI result: Pending.
- Automated tests: Local Godot 4.6.3 passed 802 checks at the landscape viewport and with a 64×64 headless display override. Tests exercise actual production, purchases and transfers, budget limits, source protection, multiple suppliers, save/load while travelling, role changes, old-save migration and station controls. A local Android resource-pack export includes the compiled supply script.
- Artifact verification: Pending.
- Manual/device tests: Desktop Godot: opened a constructed laboratory, checked its input targets and spending limit, and assigned the supplier. Android-device playtesting remains outstanding.
- Defects and limitations: The interface currently assigns First Light only. Output sales and per-ware rules are not automated. The cap applies to the total assignment, not a repeating allowance. Net targets assume local production can operate except where natural sources or deposits are unavailable; a closed production loop may need initial inputs. Construction cancellation/refunds and reordering remain unavailable.
- Next task / gate: Wait for the exact source commit's green checks, verify the Android artifact and record results before proceeding.
