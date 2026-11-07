# Runtime acceptance tests

**Execution status: not run.** No X4 executable, matching installed catalogs, save or post-0.2.5 game log is available. Supplied logs through debug(6).log were reviewed; debug(5) runs 0.2.3 and establishes the failures repaired in 0.2.4. Every row below remains UNVERIFIED. Static XML/reference/packaging checks are reported separately in `STATIC_TEST_RESULTS.json` outside the installed extension.

## Current crystal acceptance: 0.2.5

Use the seven-step matrix in [CRYSTAL_REVIEW_0.2.5.md](CRYSTAL_REVIEW_0.2.5.md): forward-only gun, non-beam turret, L/XL, missile-only with real ammunition, native drop removal, immediate player-inventory counts, partial/retried transfer, saved pending drops, direct orders, Inventory Collector and loaded/unloaded scenes. No current auto-sale, beam-only or captain holding-limit control should appear. Crystal deliveries are item quantities, not financial ledger payments. Historical 0.2.2/0.2.3 crystal acceptance below is superseded by this section.

## 0.2.4 evidence and recovery checks

Follow [JOB_REVIEW_0.2.4.md](JOB_REVIEW_0.2.4.md) for transient-sector, wreck/pilot-bail, scanner geometry, periodic Logbook and per-job outcome tests. The first activity report should appear within a minute of registration, with later per-ship reports about every five to six game minutes. These reports are always enabled independently of optional verbose diagnostics. Completed counters must change only with the task's real effect; tour stops and incomplete attempts cannot count as paid contract completions. Income is observed positive payments, not a periodic reward. Save/load and direct-order interruption must preserve these counters and all original passenger actors.

## Setup

Use a manual-save copy of an existing game; a new game is unnecessary. Record the exact X4 version/build, DLCs, enabled extensions, ship class/equipment and whether the player is nearby. Enable Diagnostics on the assigned occupation. For a detailed game log, launch X4 with `-debug all -logfile galactic-occupations.log`, then locate that log in the X4 user-data directory. Search for `GO activity:`, `GO completed:`, optional verbose `GO:` lines and script/XML errors. A clear log alone is not evidence of successful gameplay.

Start with one ship per occupation and Home/Range = local sector/0. Increase to range 2 and then 99 after local success. Use a ship with an AI captain, a route through discovered sectors, and appropriate docking access. Keep a before/after record of installed equipment, crew, ownership, turret modes and the direct-order queue.

## Per-occupation matrix

| Occupation | Setup and first action | Required observed effect and completion | Status |
|---|---|---|---|
| Escort | Choose a non-player friendly freighter with an active station voyage. Assign Galactic Escort Service. | Escort follows the actual freighter; attackers provoke defence without a long abandonment. Freighter docks at the recorded destination after meaningful escort proximity. Exactly one 12,000 Cr custom fee; next voyage is selected. | UNVERIFIED |
| Taxi | Use an S/M ship with a free person slot and two friendly dockable stations. Assign Galactic Taxi Service. | Ship docks at pickup; 1–10 actual NPCs walk from the docking module into the ship. Every accepted actor must enter before departure. The reserved count never exceeds free crew space. At destination, only those passengers disembark; one 8,000 Cr fee per delivered NPC. It finds another pickup. | UNVERIFIED |
| Scanner | Find a partly known station. Install normal scanner software; specifically test the common case where the AI scanner level is below the player's active level. | Ship approaches individual modules, remains within survey range/LOS for ten seconds, and only surveyed module information changes. Unvisited modules are not bulk-unlocked. It moves to other modules/stations. | UNVERIFIED |
| Mapper | Use a scout in a sector with an anomaly or gate. Initially leave transit fallback off. | Ship approaches and surveys; logbook contains the actual anomaly exit set or a separate ordinary gate entry. Same connection is not endlessly selected. Verify map-linked catalogue location. | UNVERIFIED |
| Tour | Use a sector containing a classified landmark/data vault/headquarters or curated object. | Up to ten actual NPCs board first. Ten distinct global sites and at least three sectors where available are recorded with dwell. Drop-off follows the route, then exactly 500,000 Cr per passenger at default settings. No early fare; route/batch survives reload. | UNVERIFIED |
| Crystal miner | Use an M ship with operational deployed beam turrets; keep player nearby in a crystal-bearing field. Assign Autonomous Crystal Miner, beam-only on, selling off first. | Logged/observed target is the crystal component itself. A turret aims, emits real shots, damages the deposit, stops on loss, and physical crystal drops appear. Native collection removes actual drops and increases pilot inventory. Next deposit is selected. See dedicated checks below. | UNVERIFIED |
| Lure | Use a fast armed ship, a manageable hostile and a friendly defender with greater firepower. | Short provocation attracts actual pursuit. Ship retreats toward the defender; no pursuit is treated as a failed attempt. It escapes or breaks off when appropriate and finds another target. | UNVERIFIED |
| Demolition | Use an armed S/M ship near destructible asteroids with player present. | Real weapons damage and destroy a chosen asteroid. Indestructible scenery is excluded; no-damage attempts time out. Next rock is selected. Optional collection picks up real released drops. | UNVERIFIED |
| Morale | Choose a friendly crewed ship with at least one non-passenger crew member below morale 15. | After the sustained support action, morale actually increases one step, never over 15. A non-player eligible faction gains the small reputation award if its shared cooldown permits. No improvement means no reward. Ship cooldown prevents immediate reuse. | UNVERIFIED |
| Inspection | Use commercial traffic in a sector whose police faction allows player access; compare legal and illegal cargo examples. | Close timed inspection identifies actual illegal cargo under that faction's law; log entry is correct and sector police signal is sent. Selecting or legally scanning a neutral ship does not directly change its relation. It selects other traffic. | UNVERIFIED |
| Recruitment | Use a capturable non-mission hostile ship below 25% hull. Record hull, exact modules/equipment and crew. Increase base chance only for a controlled test. | Failed attempt starts target cooldown. Success changes the existing object to player ownership with the same damage/equipment/crew. Captured orders and player Attack orders aimed at it are cancelled; Wait becomes available for normal reassignment. | UNVERIFIED |
| Route patrol | Use an actively trading freighter with a station destination and occasional manageable threats. | Patrol follows that actual commercial corridor, temporarily escorts/intercepts, and reselects after arrival. Route changes with traffic, rather than fixed random-sector patrol points. | UNVERIFIED |

For **each row**, also verify all ten requested lifecycle checks: menu presence, assignment, valid target selection, executable movement/action, actual intended effect, completion recognition, a second assignment, save/load recovery, target loss and interruption recovery. Merely seeing the order name is not a pass for the job.

## Shared failure and persistence cases

1. While a job travels, issue a direct Move/Dock/Attack order. Confirm the direct order takes priority and its existing queue remains intact. The default occupation should resume when native order handling returns control.
2. Save/reload during search, travel, work and immediately after completion. Confirm no duplicate payment, duplicated passenger, reset cooldown or duplicated physical drop. Verify a second assignment after reload.
3. Make the target unavailable before arrival, during work and at completion. Confirm timeout/cleanup and a replacement target. Test blocked docking access and unreachable routes.
4. Assign several ships to the same occupation. Confirm reservations prevent inappropriate duplicate work; destroying a reservation owner allows recovery after its lease.
5. Repeat with the player far away. Normal navigation, escort, commerce, morale and recruitment must be measured separately. Crystal mining and demolition should explicitly wait for high attention and create no goods or destruction while waiting. Station ray casts and anomaly traversal need their own OOS result.
6. Test risk 0/1/2, range 0/2/99, preferred-faction selection, minimum paid-contract reward and repetition off. Only relevant controls should appear, and each must affect the selected behavior.
7. Change the default occupation, take the pilot seat, or remove a target during physical firing. Within the watchdog interval, direct turret control must release. Existing turret modes, armed states and weapon equipment must match the recorded values.

## Dedicated crystal-controller tests

- First confirm Mine Crystals appears in Map → Information → Loadout for all/individual/group turrets and existing-ship outfitter controls. Select it, reload, and verify the selected flag persists. Select Attack, Missile Defence or Mining and verify the native callback/mode still works. Also test the standalone mode near a real crystal without changing ship orders.
- First use ordinary beam turrets and an exposed crystal on a large asteroid. Confirm aim points at the attached crystal rather than the asteroid center. If aim/fire calls do not visibly control turrets, record that as a failure; command availability is not a runtime pass.
- Test deposits on the opposite side of the asteroid, behind the ship, outside turret arcs, beyond firing range and beside a friendly ship/station. No-damage attempts must release; unsafe line of sight must withhold fire. Never count damage to the parent rock as a crystal harvest.
- Test a ship with no turrets, missile-only turrets, retracted/disarmed turrets, a capital ship and unsuitable weapons. It should explain/wait or be unavailable for assignment, without installing or changing equipment.
- Destroy the deposit externally during aiming and during a burst. Confirm firing stops and native collector ignores stale drops.
- Count individual real drops, pilot inventory gains and remaining physical objects. Save/reload during collection. Enable Inventory Collector and repeat: an object removed by that mod must never create a second credit here.
- Test each native crystal drop tier. Confirm valuable accessible crystals are preferred and depleted deposits are not selected.
- Enable selling; set a low threshold and collection limit. Confirm actual docking, inventory deduction, faction payment, stock ledger and return to work. Block all suitable stations and verify inventory remains owned, collection stops at the cap, and no payment appears.
- Move the player away during firing. It must stop/wait, not simulate destruction or crystals. Move the player back and verify recovery.

## Feature-specific failure tests

- Passenger: fill the last crew slot before pickup; destroy or revoke docking at the destination; interrupt while aboard; reload and reassign taxi. Existing service crew and marines must never be removed. Multi-passenger optimization is outside this version's scope.
- Scanning: interrupt dwell at nine seconds, obstruct LOS and compare scanner levels. No reveal should occur without the completed survey. Confirm the `set_object_scanned` call accepts the selected module on this engine build; a runtime error is a failed scanner test.
- Anomalies: test native traversal first, then opt-in fallback on a non-story anomaly with a known permitted exit. Confirm it preserves the same ship/equipment/crew/order. Test empty/multiple exit sets, unavailable exits and protected/story anomalies.
- Morale: all crew at maximum, only passengers aboard, externally assisted target under cooldown, and repeated services to the same faction. No successful improvement means no reputation; cooldown limits still apply after reload.
- Police: change jurisdiction mid-scan, legal cargo in a different faction, a noncompliant departing freighter and actual hostility. Do not treat police response as guaranteed; confirm signals against the installed police scripts/logs.
- Recruitment: target reaches 25% hull, target is mission/protected, Xenon/Kha'ak/noncommable crew, target dies during communication, success with projectiles already in flight. Compare exact hull/equipment/crew afterward. Unrelated player orders must remain.

## Reproducible static checks

From `downloads/x4-galactic-occupations`:

```sh
python tools/validate.py
python tools/package.py
python tools/validate.py --zip Galactic_Occupations_0.2.3_DEV.zip
```

For official schema and installed native-signature checking, extract the matching game catalogs with Egosoft's X Catalog Tool, preserving `libraries` and `aiscripts` paths, install `lxml` and run:

```sh
python tools/validate.py --reference /path/to/extracted/X4 --report installed-schema-results.json
```

Schemas may take several minutes to compile. This validates XML structure and signatures, not X4 expression semantics or game effects. Record the runtime matrix, game log excerpts and exact build separately before promoting this development package to a stable release.

## 0.2.0 targeted acceptance cases

- Galaxy: assign each occupation at range 99 in a sector with abundant local work. After an assignment, observe another sector being selected. Test 0 and 2 as boundaries, inaccessible gates and blacklisted routes. For tours, inspect targets in distant sectors before local sights are exhausted.
- Boarding: test 0, 1, 5, 9, 10 and more than 10 free crew berths. The manifest must be min(10, free). Fill space between assignment and docking. Save while 0/5/9 NPCs are aboard and while walking through the hatch. No actor/template duplication or unrelated crew removal. Disable interior streaming by leaving the area: the ship must wait rather than treat seats as boarded. Return and observe real boarding.
- Tours: record actual site identities and sector identities. Stops 0–9 must not award fares. Required sites without drop-off must not pay. Test one passenger (500,000 Cr) and ten passengers (5,000,000 Cr); changing fare after booking must preserve the booked amount. Destroy a route target/drop-off station and test recovery. A range with fewer than ten unique sights should reject a new booking with an explanatory status.
- Surveys: use a basic AI scanner with a stronger active player scanner; it must no longer skip every module. Test a large station with more than eighty components, obstructed first viewing angles, ten-second interruption, destroyed modules and OOS collision geometry. Compare actual component scan levels and station discovery before/after. No success when data remains unchanged.
- Main ledger acceptance is specified in the 0.2.1 section below; the 0.2.0 preview panel is removed.
- Builder: observe the 200,000 Cr hire entry, active payroll at 100,000 Cr/hour and standby at 25,000 Cr/hour, including SETA and final settlement. Compare each displayed amount to actual account movement. Save/reload around payout and confirm neither money nor journal rows duplicate. Lost ships/stations should retain a useful recorded label.

Additional developer checks (no X4 runtime):

```sh
python tools/tests/source_contracts.py
lua5.1 tools/tests/ui_contracts.lua vardath_galactic_occupations
```

The 36 UI checks mock menu/widget data and execute the addon Lua; they do not create real game menus or fire weapons.


## 0.2.1 native-ledger acceptance (Protected UI kept enabled)

1. Fully exit X4, install the current three-mod ZIP over the existing folders, then restart and load the existing save. A UI reload alone can retain the old wrappers.
2. With Protected UI enabled, open Player Information → Transaction Log before earning anything. Confirm its normal list, graph, native time controls, search, paging and account selection work, and the income preview panel is gone.
3. Complete an actual taxi delivery, a full luxury tour, an escort and a builder hire/active/standby/final settlement. Note the balance change. Each payment must have one native monetary entry, with no receipt row added to its total. Check job/type and ship labels plus service/employer details and lifetime totals in the hover text if UIX supplies the published callback.
4. Filter by the job or ship using the existing search field; change the time range and verify its totals count each payment once. Inspect a different station account: it must not inherit the player's job labels.
5. Test two ships receiving the same amount in one frame; each new receipt must bind to a different real transaction ID. An ambiguous historical match must remain vanilla. Old condensed entries must not generate synthetic financial rows.
6. Verify every new paid result also appears with its amount in the ordinary Logbook. With no compatible callback, native payment labels remain generic and the ledger must still open. Keep UI protection enabled throughout.
7. Save/reload and check that the payment history/totals and native-ID bindings persist without re-paying anything. Test Occupations alone, Builders alone and both together; descriptions must not be added twice.
8. Resume the previously registered occupation ships. Check that defaults restart once when editable, that direct orders finish first, and that no `Failed to set component...$vgo_*`, missing event-source or visible-attention parser errors recur. Re-select an occupation once if an older imported stack cannot recover.
9. Re-run the individual occupation tests above, especially physical boarding, crystal deposits/drops, module scanning and failed/destroyed targets. These effects remain runtime-unverified until performed in X4.
10. With the player walking on a station or outside an occupied ship, confirm Astrid brake polling no longer logs a null `player.occupiedship.isplayerowned` lookup. Check the Forge's special main gun still mounts and fires.

## 0.2.2 priority acceptance: Hold Position and missing receipts

1. Fully exit X4 and install the four-mod recovery bundle. Keep Protected UI enabled. Start/load the existing save; clear Logbook search/category filters, select General or All, and find the one-time loaded-version entries. Their absence means even MD startup/Logbook visibility needs investigation; it is not proof of a paid job.
2. Reassign each intended occupation to ships already on Hold Position. For an unoccupied player ship with a captain, check `behaviour active` and retained occupation selection after the first target search, including empty sectors. Direct orders must remain ahead of default work.
3. Confirm no recurring null location, `@ cannot be combined with ?`, absent passenger template or no-police relation errors. Saved-stack import warnings may precede recovery; recurring failures after the fresh default starts are failures.
4. Crystal Miner requires a separate startup test and harvesting test. With a suitable S/M beam-turret ship, verify active-order acknowledgment and a real target. With no usable offensive weapon, verify a waiting explanation and retained Crystal Miner behaviour, not Hold. A forward gun alone is now an eligible path.
5. In physically simulated space, observe actual deposit damage, harvested drops and native pickup with immediate forwarding into player inventory. Compare before/after item counts; no items may be generated for waiting. Test normal turret-mode recovery, blocked arcs, save/load and player interruption. Do not report the crystal job as working until these succeed in X4.
6. Complete a real paid delivery/service or builder invoice. Within the bounded receipt interval, check General Logbook for one `Vardath Payment` receipt with job, ship, details, amount and original time. Native account balance must change only once. With both mods active, check receipt numbers do not repeat. Previously recorded newest twenty receipts can appear without any new credit.
7. A successful unpaid task produces `work completed`, not a fictitious financial transaction. Ordinary trade income does not become an occupation receipt without a corresponding paid mod-journal record.
8. On a Yaki wharf already planning all three habitat sizes, wait beyond the retrofit interval and verify no duplicate habitat task. Test a missing-size plan without moving/removing existing modules. No foreach-on-constructionsequence errors should recur.
9. Revisit the heavy sector and retain a post-fix log/crash dump if it still crashes. This update removes known script-error flooding and repeat-habitat risk; it does not establish the original crash cause or remove existing station modules.

## 0.2.3 priority runtime acceptance

1. Fully close X4, update the existing folders, restart and load the current save with the existing boarded tour passengers. Retain Protected UI. Release the pilot seat to the captain. Check that the new current default selects a real sightseeing destination, undocks and moves without replacing/duplicating passengers. Reassign only jobs already lost to Hold.
2. Complete the booked distinct stops/sectors, return to the station and observe all passengers walk out. Verify the manifest and passenger templates clear only after they leave; then exactly one fare and receipt. Stop midway through unloading, save/reload or issue a direct order, then resume: no passenger duplication or extra fare.
3. Taxi: test both different-sector and same-sector destinations. After real boarding, it must undock, travel directly, dock and unload all accepted NPCs before payment. It must not need a tour stop. Try batches of one/ten and a ship with fewer free berths.
4. Off-screen unloading: verify an actual same-actor connection to a real destination room, outside the ship, before the delivered flag. An unavailable room or failed connection must keep the manifest/unpaid state. No fifteen-second success fallback. Bring the scene into attention to test streamed walking if the engine cannot connect off-screen rooms.
5. Escort/patrol: choose active non-player/player traders with real queued commercial destinations. Confirm foreign-owner escort no longer creates AssignCommander or Hold. Track the trader along its actual route. During a suitable hostile encounter, the separate temporary Attack order may run, then the occupation resumes its stored convoy. Test failed/out-of-ammo combat, direct player orders, route changes and trader destruction.
6. Re-test the other ten jobs' assignment, target/effect/repeat, save/load and failure cases above, especially starting while docked. Diagnostics should name the current activity; neither source validation nor a clear log counts as proof of an effect.
7. Inspection: use legal and actually illegal cargo; no `.illegalto...count` errors. Yaki: verify native plan macro lookup no longer errors and no duplicate habitat expansion is queued. The update does not delete existing habitat modules.
8. Crystal mining remains a separate unverified acceptance test: actual deposit target, aim, hits, drop event, collection and player-inventory delivery must be observed. Departure repairs alone do not verify it.

Off-screen pickup acceptance: at a valid station dock, verify the same cue actor is first connected to the pickup room and then the ship room, with a native non-transit passenger template, before the boarded acknowledgment. A failed room connection must preserve the batch and award no payment. Recheck the previously successful visible walking path unchanged.
