# Station menu and crystal review — 0.3.1 development

7 November 2026. This follows the user's live report: the hacker behaviour was found in the roles list, but its right-click submenu remained Checking; Crystal Miner had returned no crystals. No new log was supplied with these reports. The earlier debug(6).log predates these changes and cannot confirm their execution.

## Confirmed station-menu defect

The published native X4 9.00 InteractMenu `onUpdate` handles `menu.refresh` by calling `menu.draw()`. It **does not** call `prepareActions()` to regenerate action lists. The 0.3.0 catalogue callback only set `refresh=true`, leaving `menu.actions.vgo_hack_panels` containing Checking even after the blackboard reply arrived. The original mock manually called `prepareActions()` after the reply and therefore concealed this defect.

The fix updates only the custom submenu's action array before requesting the normal native redraw. A half-second, open-menu poll also reads replies if the Lua event is missed. IDs use consistent 64-bit conversion; MD booleans accept true/false and 1/0. Delayed replies for another station and stale ship selections cannot retarget the current menu. Native prepare/update methods retain their original calls and return values; no ledger renderer or other section is replaced.

The ten-second response deadline uses native UI elapsed time, so a paused simulation cannot leave the menu Checking indefinitely. Timeout offers an explicit retry, without an automatic request flood. Mission Director still needs simulation to run: unpause to process a lookup or queue its resulting order. Catalogue actions now publish an explicit reply for empty/unavailable stations and allow refreshing interiors that were previously unloaded. Empty discoveries are cached only briefly. No fictitious panel list is supplied.

## Crystal control-flow limitation and recovery

The actual firing helper exits at attention below `visible`. The old worker could repeatedly send a miner through remote sectors while never reaching its physical firing path. This is a confirmed code limitation; without a fresh log it cannot be identified as the only cause of the user's zero yield.

- `Follow active crystal simulation`, default on, uses normal native undocking/navigation to reach an accessible sector around the player. It respects the existing scope, risk, blacklists and order priority, with a bounded travel watchdog. It stays in active simulation to search existing asteroid/crystal objects instead of immediately leaving that working bubble. No player/ship warp, forced simulation setting, deposit spawn or simulated damage is used. Disabling it retains normal sector rotation.
- This is a documented fallback, **not out-of-sector crystal harvesting**. Real procedural deposits and weapon/collision simulation must be present. If the player is at a station with no materialised nearby crystals, the miner can still wait for real targets; an asteroid field is needed for meaningful testing. Range 99 continues to allow the entire connected galaxy wherever active simulation is actually available.
- Independently discover nearby real drops whose native ware contents include `inv_crystal_01` through `inv_crystal_05`. This recovers interrupted/missed drop events and existing loose crystals. It does not create a deposit, drop or item, and respects reservations held by another occupation ship.
- After a native pickup, wait briefly for events/inventory. If the actual drop remains untouched and an owned player-occupied ship is available, try the documented native `collect_drop` action with that ship as collector, routing native inventory pickup directly to the player. Both paths act on the same actual drop. They do not manually delete it or mint a replacement item.
- Record only a bounded observed positive player-inventory delta after a native consumption/collection confirmation. Preserve partial captain-transfer rollback from 0.2.5. Failed native collection retains the real object for retry rather than claiming delivery. A collected crate that temporarily remains as a wreck also counts only with actual player credit.
- New diagnostics: `GO crystal search:` includes sector, attention and real asteroid/deposit/drop counts; `GO crystal fire result:` records actual initial/remaining hull and destruction event; `GO crystal pickup:` records native collection state; `GO crystals:` records actual inventory delivery. General Logbook reports real forwarding/direct pickup separately from money.

## Verification and limitations

The actual new inventory return has not been observed in X4. Native API/source checks establish exposed commands, not live execution with this save or installed mod order. No X4 executable, game save, matching installed schemas or live crystal field is available here. Physical firing/weapon arcs, procedural object availability, native player-collector routing, NPC pathing, remote panel effect/cost and save/load recovery remain runtime-unverified.

Tests exercise the actual addon with a **draw-only native-shaped refresh**, reply without a prepare call, lost reply events, paused-time timeout, explicit retry, empty/unavailable results, numeric flags, stale station/selection and existing native action preservation. Existing inventory XML mocks still verify observed withdrawals/credits and rollback. Eight new recovery source contracts cover navigation constraints, real-drop filtering, bounded native collection, diagnostics and unconditional menu replies. These are not game tests.

Static validation, all seven extension/archive audits and CI results accompany this release. No other mod source changed, no cash is awarded for crystal collection, no new financial UI exists, and Inventory Collector, Protected UI, Kopis/Astrid equipment, passengers and existing crew are retained.

## Reproduce in game

1. Fully exit X4; install 0.3.1 over the same extension; restart and load the existing save. Keep Protected UI and Inventory Collector.
2. Right-click a faction station with an AI player ship selected. Open Hack station and leave it open. With the game running, a real reply must replace Checking without closing/reopening the menu. Pause before requesting: after ten UI seconds, timeout/retry must appear. Unpause and retry. Test unloaded/absent panels, station switching and a selected ship change; no wrong target or duplicated order should be queued.
3. Re-select Crystal Miner if its new setting is absent. Leave Follow active crystal simulation on, range 99, and use an AI ship with actual usable weapons/ammunition. Enter a real asteroid field in another ship so deposit physics is present. Verify the miner travels normally into active simulation, detects a real deposit, hits that deposit, releases real drops and increases the matching player inventory count. Repeat with forward-only, turret and capital ships; confirm normal modes/equipment afterward.
4. Record before/after item counts and read the four diagnostic prefixes in a **new** debug log. Zero asteroids/deposits identifies discovery/simulation; no hull decrease identifies firing; actual drops with failed pickup identifies native collection. None may be counted as a successful delivery without the observed inventory change. Repeat interruption/save/load, collector competition and a player on foot.
5. If it still returns zero, supply that new full log so the precise stage is known. The previous beam-preflight log cannot establish what this build is doing.

Primary reference: [native X4 9.00 source](https://github.com/ArtByunex/x4-foundation-artbyunex/tree/e3e8a345e5624db118bff3eb171b60b0993fcc2c), particularly `ego_interactmenu/menu_interactmenu.lua`. Extracted native `lib_generic.xml` finds real crystal components on existing asteroids; native small-ship collection uses `collect_drop`. Command contracts and exposed properties are checked in the existing metadata.
