# Hyperion Ascendant 1.0.2

A separate upgraded L-class Hyperion builder with expanded storage and slow consumable/drone replenishment, plus a targeted repair for the original Hyperion story's cached gate routing. Requires X4 9.00, **Hyperion Pack** and **Cradle of Humanity** for Yaki crew. More X3 Sectors – Reunion is optional; routing uses the actual installed gate network.

## The ship

| Feature | Configuration |
|---|---|
| Hull | 640,000 |
| Main shield | 416,540 capacity; 2,840 recharge per second; zero recharge delay |
| Main batteries | Six dedicated batteries; 2,000,000 base damage per projectile; 0.65 shots/second before heat limits. Astrid Tours: 82,000 per projectile, eight shots/second burst ceiling before magazine reload |
| Turrets | Eight dedicated medium beam turrets; 1,600,000 damage and 1,600,000 shield-damage parameters per turret; ten times Astrid Tours’ 160,000 beam damage. Matching 160/240 aim rates and one-second turret reload overrides; five-second bullet reload and three-second beam lifetime |
| Drive | Normal, boost, travel and reverse thrust are three times version 1.0.0: forward 47,115; reverse 155,493. Boost (2) and travel (23) multipliers, hull drag and travel timings remain unchanged, avoiding an accidental ninefold mode increase |
| Handling | Lower angular inertia and drag; scoped player braking assist with a 2.5 game-second deadline after idle input |
| Crew | 700 total berths; new ships retain the Yaki captain and 80% service/marine fill policy. Existing crew are preserved |
| Cargo | Private 2,000,000 m³ container, solid and liquid bays: twice Kopis Forge’s 1,000,000 m³ per type. Legacy bays are retained and can add extra capacity |
| Consumable capacity | 10,000 shared deployables; 1,000 countermeasures; 10,000 missiles. Missiles do not regenerate |
| Drone capacity | 1,024 shared slots; new ships start with 30 construction, 20 cargo and eight repair drones |
| S-ship storage | 1,000 internal slots through the existing physical pads. Legacy upgrades retain the original two slots as well |
| Construction | Native L builder role, Find Build Tasks and Deploy to Station; optional Builder Hire payroll compatibility |
| Equipment layout | Native Hyperion's six gun hardpoints, eight turret group positions, docks, bridge, storage and repair/cargo drones |

The custom macro IDs are unchanged: existing Ascendants receive the revised drive/weapons on reload without re-equipping or replacing the ship. The extension checks once per game minute for a **player-owned Ascendant** across the galaxy, including remote/docked ships. If none remains, it attempts to create one safely 8–12 km from your ship, equipped and crewed. A vanilla Hyperion does not block this separate variant. Renaming your Ascendant does not cause another spawn. Existing copies are not re-equipped, renamed or re-crewed. Losing or selling the last player-owned copy makes a replacement eligible at the next check.

These are explicit custom parameters, not a claim of measured current-game DPS, top speed or braking. The engine and hull shell were derived from stock definitions retained in the VRO author's reference comments; the mod does **not** install VRO's replacements or depend on VRO. All referenced physical component and connected macro names were checked against pinned native indexes. Models, interiors, effects and sounds come from the installed game/DLC; no model files are redistributed.

The brake assist applies only while the player actually controls this exact variant with flight assist enabled, no autopilot, no matching speed, no boost, and all relevant flight inputs idle. It does not operate on other ships or during spacesuit/teleport transitions. Normal turret modes are preserved.

## Cargo, hangar, building and replenishment — 1.0.2

The ship stays **L class**, with its original model, native pads, bridge, weapons and special S-ship repair module. The native construction orders require `purpose.build`, not XL size; native defaults supply the construction-vessel connection to every ship class, and the native build-drone rules explicitly include L. The station’s automatic construction-vessel search is extended from XL to L/XL while retaining its build-purpose and relation checks. If Living Factions and Builders 1.75 is installed, a separate optional patch lets its unchanged real-assignment payroll discover L builders. No Builder Hire source, payment rate or UI is replaced. Choose **Find Build Tasks** as the default behaviour or issue the normal **Build** command at a player station. Building consumes the station’s supplied resources and uses real construction drones; this extension does not fabricate station progress or trade wares.

New ships use the private container bay and 1,000-slot S storage directly. A minute-scale maintenance cue uses native `create_module` to add missing private bays to an existing Ascendant and checks their real parent and final capacities. It preserves the old bay, its cargo and all docked ships. Consequently an older ship can have slightly more than 2,000,000 container capacity and 1,002 S slots. No existing ship, installed equipment, orders, people or docked vessels are removed or recreated. The existing physical landing pads feed the internal storage; this is not 1,000 exposed landing pads. A new General Logbook/debug status says **verified** only after actual cargo/crew/drone/ammunition and S-storage getters meet their targets. A refused attachment stays **pending** and is not repeatedly attempted. Existing universal cargo is protected from mixing with new single-type bays and remains pending for a separate review.

**Native creation/registration of these additional ship modules, existing-save migration and storage/launch require live X4 verification.** The supported command and parameters are source-checked; mocked creation is not proof that a running ship accepts or registers the modules. No new game is required by the implementation, and no destructive replacement is used as a fallback.

A separate maintenance cue replenishes only the following stored inventory every **10 game minutes** (checked once per minute):

| Inventory | Added per batch |
|---|---:|
| Flares | Up to 5 |
| Advanced satellites | 1 |
| Resource probes | 1 |
| Navigation beacons | 1 |
| Friend/Foe mines | 1 |
| Cargo drones | 1 |
| Construction drones | 1 |

Both controllers operate across the galaxy on actual player-owned Ascendants, including remote ships. Supply deadlines are saved per ship and advance before the batch; loading repeatedly or skipping a long period does not create extra catch-up stock. Shared storage limits are respected. Deployable priority rotates and drone priority alternates if only one slot is free. Requested/unavailable drones still occupy inventory; they are not replaced merely for being in flight. An older ship with no construction drones receives one bounded starter kit of up to 30, if free slots exist. Existing construction drone stock is retained. Ordinary cargo, trade goods, missiles, repair drones, normal satellites, crew and money **do not regenerate**. Nothing is automatically deployed. Supply maintenance is separate from capacity migration, so a rejected module attachment cannot take over navigation or stop replenishment.

## Hyperion quest repair

More X3 Sectors – Reunion 0.33 changes connections including `720To049` and `720To721`, inserts sectors, and adds links to sector 730. A story route cached before those changes can refer to an unavailable gate or lack a new sector entry.

Each native gate-investigation stage now asks the native `get_jump_path` function for the actual route to the Hyperion home sector, and chooses an existing active gate in the current sector from that path. Only that sector's cache entry is refreshed. If an inserted sector has no gate, the native next-sector handler relocates the search to the next real gate along that same route; it does not count the empty sector as a successful scan. A former entry gate can be used when the new topology requires backtracking. The final arrival records the real gate exit for the next native stage.

For an already-stuck save, a thirty-second watcher can rebuild **only the current sector's scan stage** when its real route differs. Version 1.0.1 waits one second in a separate actions block after a reset, matching the original native transition handler, and confirms the mission, sector and waiting listener again before signalling. It can also resume the waiting stage left by the failed 1.0.0 immediate signal. A changed or finished quest is not replayed. It cancels that stage's stale listeners through the same native reset used by normal sector transitions, preserves the investigation counter and signals the same sector. Prior chapters, acceptance, actors, items, mission rewards and the original Hyperion remain. It does not reset the whole story, teleport the player, construct gates or claim a scan completed. The player must perform the native investigation at the real gate.

If the installed map has **no real connected route**, the quest stays pending and logs a bounded notice instead of fabricating a gate or completing the plot. Repairing a physically disconnected map would require the save and its actual map state. The latest log confirms that 1.0.0 found a real route from Cloudbase Southeast to Third Redemption but signalled too early after reset. Version 1.0.1 corrects that observed scheduling error. New native execution is not runtime-verified here.

## Install and test

Exit X4. Extract the archive into the game directory so this file is at `extensions/vardath_hyperion_ascendant/README.md`. Enable **Vardath - Hyperion Ascendant** and load your existing save. Keep Galactic Occupations, Protected UI, Inventory Collector, Kopis Forge and Astrid Tours installed as before. With Occupations 0.4.8, the Ascendant can be assigned Galactic Sightseeing Tour along with other eligible L/XL ships.

1. Wait up to a game minute with a player ship/sector available. Check the property list for the equipped player-owned Ascendant and its Yaki captain/crew. Inspect all six main guns, eight turrets, shields, drive and free berths. Save/load it docked and remotely; there must be no duplicate and no equipment/crew replacement.
2. In a test save, sell or lose the last Ascendant and verify one replacement. An owned remote or docked Ascendant must suppress another spawn. Verify the original Hyperion, Forge weapon and Astrid remain unchanged.
3. Return to the stuck Hyperion gate-investigation stage, unpause for a minute, and inspect `VCF Hyperion:` diagnostics. Scan the newly selected **actual gate** and verify normal native progression. Save/load the stage, revisit an inserted sector and check final home arrival. A no-route notice is not a successful quest completion.
4. Pilot the Ascendant to check actual handling, damage, docking and the idle-input braking target. Retest with autopilot, active controls, copilot/AI control and spacesuit transitions; the assist must not take control in those contexts.

Forty-two source/mocked contracts pass, with thirty pinned references including the prior drive, published Astrid weapons and native reset/ware definitions. Correct equipment-use metadata and removal of unused blueprint-owner entries addressed eighteen earlier ware warnings; these and the earlier recovery warning do not recur in the latest recording. The ship name uses the native localization-token string form. Two native story selectors apply uniquely, custom components and loadout references resolve, and archive contents match source. **No running X4 environment or save was available.** Native ship creation, weapons, crew, route execution, braking and save/load require these live acceptance checks.

## Version history

- **1.0.2 — 10 November 2026:** expanded cargo/drone/consumable capacities, 700 crew, approximately 1,000 S storage, native L building and optional payroll discovery; slow whitelisted replenishment with saved deadlines and safe capacity migration. See [the latest log review and acceptance checks](LOG_REVIEW_1.0.2.md).
- **1.0.1 — 10 November 2026:** triple the previous normal/reverse/boost/travel drive settings; stronger main guns and ten-times-Astrid beam turrets; native reset delay with guarded saved-stage recovery; valid ware-use metadata and localized ship naming. See [the new log review](LOG_REVIEW_1.0.1.md).
- **1.0.0 — 10 November 2026:** initial separate upgraded ship, Yaki replacement maintainer, scoped braking and current-map Hyperion quest routing/recovery.
