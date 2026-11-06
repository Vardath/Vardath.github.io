# Runtime acceptance tests

**Execution status: not run.** No X4 executable, installed catalogs, save or live game log is available in the development environment. Every row below remains UNVERIFIED. Static XML/reference/packaging checks are reported separately in `STATIC_TEST_RESULTS.json` outside the installed extension.

## Setup

Use a manual-save copy of an existing game; a new game is unnecessary. Record the exact X4 version/build, DLCs, enabled extensions, ship class/equipment and whether the player is nearby. Enable Diagnostics on the assigned occupation. For a detailed game log, launch X4 with `-debug all -logfile galactic-occupations.log`, then locate that log in the X4 user-data directory. Search for `GO:` and script/XML errors. A clear log alone is not evidence of successful gameplay.

Start with one ship per occupation and Home/Range = local sector/0. Increase to range 2 and then 99 after local success. Use a ship with an AI captain, a route through discovered sectors, and appropriate docking access. Keep a before/after record of installed equipment, crew, ownership, turret modes and the direct-order queue.

## Per-occupation matrix

| Occupation | Setup and first action | Required observed effect and completion | Status |
|---|---|---|---|
| Escort | Choose a non-player friendly freighter with an active station voyage. Assign Galactic Escort Service. | Escort follows the actual freighter; attackers provoke defence without a long abandonment. Freighter docks at the recorded destination after meaningful escort proximity. Exactly one 12,000 Cr custom fee; next voyage is selected. | UNVERIFIED |
| Taxi | Use an S/M ship with a free person slot and two friendly dockable stations. Assign Galactic Taxi Service. | Ship physically docks at pickup; passenger appears in people/passenger data, not cargo. It docks at the recorded destination and only that passenger leaves. Exactly one 8,000 Cr custom fee. It finds another pickup. | UNVERIFIED |
| Scanner | Find a partly known station. Install scanner software supporting at least the player's maximum scan level. | Ship approaches individual modules, remains within survey range/LOS for ten seconds, and only surveyed module information changes. Unvisited modules are not bulk-unlocked. It moves to other modules/stations. | UNVERIFIED |
| Mapper | Use a scout in a sector with an anomaly or gate. Initially leave transit fallback off. | Ship approaches and surveys; logbook contains the actual anomaly exit set or a separate ordinary gate entry. Same connection is not endlessly selected. Verify map-linked catalogue location. | UNVERIFIED |
| Tour | Use a sector containing a classified landmark/data vault/headquarters or curated object. | Ship approaches at viewing distance, remains for configured dwell, logs the visit and visits other destinations. Recent itinerary is retained across save/load and completes a search cycle before resetting. | UNVERIFIED |
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
python tools/validate.py --zip Galactic_Occupations_0.1.0_DEV.zip
```

For official schema and installed native-signature checking, extract the matching game catalogs with Egosoft's X Catalog Tool, preserving `libraries` and `aiscripts` paths, install `lxml` and run:

```sh
python tools/validate.py --reference /path/to/extracted/X4 --report installed-schema-results.json
```

Schemas may take several minutes to compile. This validates XML structure and signatures, not X4 expression semantics or game effects. Record the runtime matrix, game log excerpts and exact build separately before promoting this development package to a stable release.
