# Implementation and verification report

## Delivery status

All twelve occupations have native infinite-order declarations and executable task implementations. **All in-game acceptance checks remain unverified.** There is no claim of a finished stable release, working native “Mine Crystals” dropdown entry, accepted vanilla mission, or successful runtime test.

Static validation checks XML parsing, documented command attributes and context, child signatures, local labels, script references/parameters, English text references, namespacing and archive/source identity. Full installed-game XSD and expression-engine validation were not available. The optional `--reference` validator path can use the matching extracted game files for full AI/MD XSD checks and native call signatures.

## Repository inspection

The existing website repository stores extensions in `downloads/x4-*`, with extension-local `content.xml`, `aiscripts`, `md`, `libraries`, `assets`, `t` and sometimes `ui` folders. Inspected collections: Living Factions and Builders; Kopis Production Cheat; Yaki Terran Habitats; Station Auto Drones; Universal Cargo Teleport. Faction Invincible was identified in the repository tree. Their existing packagers and validators were inspected.

Relevant overlap: builders patch native build orders; cargo teleport patches trade/ware-exchange orders; auto drones supplies its own MD/Lua UI; Kopis modifies ship/weapon assets and supplies its own MD scripts. Galactic Occupations changes none of them and adds no patches at their paths. Its only new workflow validates this extension and does not repackage other mods.

## Evidence used

The inspected game script snapshot is [loewenherz-projekt/X4-Scripts, commit c45e48e77e5e9fe195d24ffe8935dbea7ad864a2](https://github.com/loewenherz-projekt/X4-Scripts/tree/c45e48e77e5e9fe195d24ffe8935dbea7ad864a2). That public snapshot is dated August 2025; it is **not** asserted to be the user's installed build. X4 8.00/9.00 command metadata was also inspected from [the schema-derived reference](https://github.com/chemodun/chemodun.github.io/tree/main/src/commands/data), generated 28 August 2026. The validator records its provenance and keeps factual interface signatures, not copies of game scripts or schemas.

Concrete reference files inspected:

| Mechanism | Actual source inspected | Implementation consequence |
|---|---|---|
| Default orders and UI | `08/aiscripts/order.move.follow.xml`, `order.fight.patrol.xml`, `08/ui/addons/ego_detailmonitor/menu_map.lua` | New `infinite="true"` orders and required sync points; native queue priority. |
| Travel and docking | `move.generic.xml`, `order.dock.xml` | Native pathing, gates/highways, docking and blacklists; bounded watchdog deadlines. |
| Escort/combat | `order.fight.escort.xml`, `order.fight.attack.object.xml` | Actual escort segments and combat routines; no fabricated escort arrival. |
| Passenger structure | `08/md/gm_transport_passengers.xml`, `rml_transport_passengers_v2.xml`, `08/libraries/scriptproperties.xml` | Actual actors/passenger NPC templates and docking verification; no passenger-as-cargo shortcut. |
| Module discovery | `08/md/rml_scan.xml`, `scenario_tutorials.xml`, scan actions/properties in schema metadata | Native player scan controls are player-specific. A timed close module survey is an explicitly custom equivalent. |
| Crystals | `08/md/lib_generic.xml`, `FindCrystalsNearPlayer`; `tutorial_mining.xml`; `08/libraries/drops.xml` | Real `class.crystal` components attached to asteroids, with genuine drop IDs and values. |
| Turret targeting | `mining.collect.ship.capital.xml`; schema `aim_turret`, `fire_turret`, `reset_turret`, `set_turret_targets`; weapon-mode enum | Per-turret direct control; no invented additional engine enum. Arcs, firing and deployment remain runtime questions. |
| Inventory collection | `order.collect.ship.xml`, `move.collect.ship.smallship.xml` | Native collection explicitly handles inventory wares and calls `collect_drop` on real objects. |
| Anomalies | Anomaly datatype `destinations`, transition flags; `placedobjects.xml`; `rml_scan_anomaly.xml`; `event_object_entered_anomaly` | Catalogue real destinations; optional same-ship fallback uses an allowed exit only. |
| Morale | `08/md/conversations.xml`, `rml_deliver_crew.xml`, entity/npctemplate skill properties | `add_skill` on existing crew, actual before/after checks, 0–15 limit. |
| Inspections | `order.move.recon.xml`, `order.move.recon.police.xml` | Native NPC police use range/time and faction-law cargo/inventory checks. A direct call to Police would retarget to player police jurisdiction, so the custom equivalent avoids that ownership assumption. |
| Surrender | `08/md/boarding.xml`, `lib_generic.xml`, `set_owner` metadata | Transfer the existing ship, override NPC allegiance, detach former commander, clear captured orders and cease fire. Do not use the boarding library's crew-removal path. |
| Rewards | `transfer_money`, `add_faction_relation`, relation-change reason metadata | Fixed custom service fees after verified outcomes and small cooldown-limited reputation. |

No full third-party mod script was copied into this extension. Subsystem Targeting Orders and KUDA source were inspected for architecture and compatibility considerations; neither is a dependency.

## Framework and accounting

Each order calls `vardath.go.worker` with an occupation number and only relevant configuration. The worker searches local targets, maintains a cached allowed-sector itinerary, reserves targets before blocking work, dispatches a task and releases the reservation afterward. Native movement honors blacklists. The normal default-order queue supplies direct-order interruption and save persistence.

Reservations contain owner/expiry fields and are ignored when expired or their owner no longer exists. A two-second watchdog inspects the registered workers, releases stale turret control/leases and signals timed-out scripts to recover. It does not discover all ships globally or inject occupation orders over player commands. Direct physical firing has an additional short heartbeat expiry.

Custom money/reputation uses a per-ship serial ledger. Tasks must arm `$vgo_verified` after their final gameplay condition; `vardath.go.reward` consumes a serial once. Taxi delivery additionally requires the specific passenger to exist and physically dock at the recorded station before disembarkation. Morale rewards require an observed skill improvement, a per-target cooldown, and a shared 30-minute faction reputation cooldown. No reward timer creates a success.

## Explicit remaining limits

- Every menu-assignment, travel, gameplay-effect, repeat, interruption and save/load check requires an X4 runtime. No game error log from this build was available.
- Escort and taxi are custom autonomous services. Vanilla mission-offer acceptance/completion is not implemented and is not represented as completed.
- “Mine Crystals” is a custom controller within Autonomous Crystal Miner, not a new native turret dropdown mode. The documented turret API is present in the reference; aim, firing arcs, deployment, accurate crystal hits, target cleanup and resulting drops have not been demonstrated in game. This is the largest outstanding verification item.
- Crystal mining and asteroid demolition require high attention and S/M ships. They wait outside that simulation rather than inventing OOS destruction, drops or inventory. Autonomous physical harvesting across unattended sectors is therefore not delivered.
- Station surveys are timed proximity/line-of-sight operations followed by a per-module `set_object_scanned` action. This is a documented custom equivalent, not execution of the player's scan mode. The action uses the player's maximum scan level, so the surveying ship must support at least that level; success on station subcomponents still needs runtime proof.
- Taxi supports one custom passenger journey per ship, with same-sector or nearby drop-off stations while ships seek work across the allowed galaxy. Multi-passenger route optimization is not implemented. Custom passengers remain aboard if an assignment is interrupted, allowing resumption.
- Anomaly destination lists may contain several exits and can change. The survey stores the actual set at inspection time. The optional fallback chooses only a valid listed non-mission exit; it is not proof of native autonomous traversal. Map logbook entries are used rather than adding a custom graph UI.
- Sightseeing uses a curated base-game macro list and actual landmark/data-vault/headquarters/anomaly classifications. It does not supply a hand-authored list of every DLC's scenic coordinate. Unclassified scenery will not automatically become a destination.
- Cargo inspection is the NPC-style timed law check. It reports contraband through the native sector police signal and logbook, but does not grant a legal police licence, guarantee police response, force surrender or add a punishment system.
- Recruitment does not remove story protection. Other-faction ships may still have projectiles in flight during ownership change. Player Attack orders explicitly targeting the captured ship are cancelled; unrelated queues are left intact.
- Custom broker sales are accounted inventory exchanges, not automated clicking of the player's trader UI. Inventory Collector can race for real drops; no duplicate credit is supplied if it collects first.
- Per-ship search staggering and bounded local result sets are implemented. Large-fleet performance, DLC/mod-specific classification and load-order behavior require profiling against the actual installation.

## Static results

See the adjacent collection's `STATIC_TEST_RESULTS.json` for machine-readable results and `TESTING.md` for the per-job runtime acceptance matrix. The GitHub workflow is explicitly named “static validation”; a successful check does not change the runtime status.

Reputation update: completed escort/taxi services, actual morale improvements, verified trade-route escort arrivals and genuine contraband reports can award a small faction increase. Completed accounted crystal broker sales use a smaller trade increase. The shared 30-minute faction cooldown prevents stacking; discovery, sightseeing, demolition and captures do not grant reputation by proximity.
