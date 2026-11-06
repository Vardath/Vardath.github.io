# Galactic Occupations

Version 0.1.0 development build, 6 November 2026. Author: Vardath.

**Runtime verification is pending for every occupation.** This package contains actual order definitions, AI task scripts and Mission Director state/transfer handling. The build environment cannot run X4. Do not interpret the static test result as proof that the Behaviour menu or any gameplay effect works in your installed build.

## Installation and assignment

1. Close X4. Extract `Galactic_Occupations_0.1.0_DEV.zip` into the X4 installation directory. The result must be `X4 Foundations/extensions/vardath_galactic_occupations/content.xml`.
2. Enable Galactic Occupations in Extensions. Load your existing save.
3. Select a player-owned ship with an AI captain. Open Behaviour and choose one of the occupation names below as its Default Behaviour.
4. Select a home sector and range: 0 means that sector, 2 means nearby sectors, 99 is the galaxy range. Risk is 0 cautious, 1 balanced or 2 aggressive.
5. Issue direct orders normally. These occupations run through the native default-order system; no scheduler replaces your order queue.

The scanning, crystal and demolition orders are restricted to S/M ships. Crystal work requires suitable deployed turrets; beam turrets are the conservative default. It pauses outside high attention rather than synthesizing harvested goods. The script does not install weapons, arm turrets or rewrite their saved modes.

## Occupations

| Behaviour | Implemented action | Qualification or alternative |
|---|---|---|
| Galactic Escort Service | Reads a commercial ship's actual trade/navigation destination, repeatedly runs native escort segments and checks its docking arrival. | Custom 12,000 Cr service contract; no automatic acceptance of vanilla mission offers. Arrival, time and proximity samples gate payment. |
| Galactic Taxi Service | Docks at pickup, creates a real passenger actor/template, flies to a dockable destination and disembarks that passenger after docking. | Custom 8,000 Cr passenger contract. One passenger journey at a time. A saved passenger contract can resume after interruption. |
| Station and Component Scanner | Approaches individual unscanned modules, checks range and line of sight for ten seconds, then publishes scanner-limited module information. | Custom survey equivalent. It does not activate the player's scanning mode or mark the entire station scanned. Both the ship and player's scan-level constraints are enforced. |
| Wormhole and Anomaly Mapper | Visits actual anomalies, gates and accelerators, records real anomaly destination sets and writes a map-linked catalogue. | Anomaly transit fallback is opt-in; it first attempts physical traversal, then can warp the existing ship to a real permitted exit. Mission anomalies and capitals are excluded from the fallback. |
| Galactic Sightseeing Tour | Visits a curated macro catalogue plus actual landmarks, data vaults, faction headquarters, derelicts and anomalies found in the installed universe. | Waits at viewing distance. Records a persistent itinerary and resets it after a search cycle through the allowed sectors. DLC/mod content participates through game classifications. |
| Autonomous Crystal Miner | Finds `class.crystal` components attached to asteroids, prioritizes native valuable drop types, aims/fires selected turrets at the deposit and collects that deposit's physical drops. | “Mine Crystals” is scoped direct turret control, **not a new entry in the native turret-mode dropdown**. Its runtime firing behavior is unverified. S/M, suitable turrets and high attention are required. |
| Hostile Lure and Interception | Finds a manageable hostile and a stronger friendly defender, provokes a short burst, checks actual pursuit and retreats to the defender. | Failed pursuit is not counted as success. Enemies are not forced to chase. Survival thresholds and normal attack-response handling apply. |
| Asteroid Demolition | Selects destructible asteroids, fires actual non-missile weapons/turrets and checks hull destruction. | Physical high-attention operation. Optional ordinary drop collection and resource-bearing-asteroid preference. No simulated OOS destruction. |
| Fleet Morale Booster | Approaches an eligible crewed ship, performs a sustained operation and increases non-passenger crew morale by one step, capped at 15. | External-faction reputation requires at least one observed morale increase. Default six-hour ship cooldown and shared faction reward cooldown. |
| Traffic Control and Cargo Inspection | Performs a close timed NPC-style inspection, checks cargo/inventory against the local police faction's illegal-ware rules and reports genuine contraband. | Custom NPC inspection equivalent; does not use the player-only scan-target control, manufacture crimes or directly set neutral ships hostile. |
| Emergency Ship Recruitment | Negotiates with capturable hostile ships below 25% hull, applies a conservative probability and transfers the existing ship on success. | Excludes mission/protected/invalid targets. Preserves hull/equipment and transfers crew allegiance. Cancels that ship's old orders and player Attack orders targeting it, then assigns it Wait. |
| Trade Route Patrol | Reads real commercial destinations, follows/escorts a trader along its route and intercepts manageable threats near that traffic. | A moving commercial corridor, not a random sector patrol. Re-selects traffic as voyages end or fail. |

## Configuration and status

Every behaviour exposes home, range, risk, repetition and diagnostic logging through native order parameters. Preferred faction is available for service/inspection/patrol jobs: select a ship or station belonging to that faction. Minimum reward is shown only for the paid escort and taxi contracts.

Additional controls appear only where used: recruitment base chance; morale cooldown; crystal sales, selling threshold, collection limit and beam-only control; anomaly transit fallback; demolition resource preference/collection; sightseeing dwell time.

Native order names, activity indicators and destination markers provide the normal Behaviour UI information. More detailed status is stored on the ship's `$vgo_status` blackboard field and emitted to the game debug log when Diagnostics is enabled. Contract completions, anomaly catalogue entries, sightseeing visits, inspection reports, recruitment and sales also produce logbook records. No Lua menu replacement is installed.

## Crystals and sales

Detection follows the native tutorial's asteroid-component search. The firing controller receives the crystal object, not its parent asteroid. It filters out missile/repair turrets, checks range and ray-cast line of sight, pauses for aiming, fires, stops on target loss, and abandons attempts with no hull damage. Nearby traffic or stations withhold firing. The engine still determines firing arcs, deployment and physical shots; these require the dedicated tests in TESTING.md.

The Mission Director listens to drops from the selected crystal. Native `order.collect.ship` collects those actual drops, including inventory wares, into the collecting ship's pilot inventory. No crystal creation or manual duplicate pickup is implemented. If another Inventory Collector gets a drop first, the native collector skips the unavailable object; no replacement crystal is credited.

Optional sales use a **custom broker transaction**, after docking at a real non-player station with walkable facilities. Actual pilot crystal inventory is removed, the faction pays the ware's defined average price, and the items are credited to an instantiated trader or recorded in that station's broker stock ledger. A failed payment restores the items and reverses any partial payment. This does not drive the player's inventory-trading UI. Crystals remain in the pilot inventory if no valid station is available. Collection stops at the configured inventory limit until goods are sold or transferred.

## Persistence, compatibility and preservation

Designed to load into an existing save. AI locals, ship state, reservations, passenger templates, itineraries and cooldowns use normal saved script/game state. The MD watchdog inspects only registered occupation ships, with staggered per-ship searches and timed recovery. Save/load behavior has not been runtime tested.

Only new namespaced `vardath.go.*` AI files, `VGO_*` order IDs, `VGO_State`/`VGO_Catalogue` MD scripts and page 191180 are added. There are no vanilla diffs, equipment/loadout changes, turret-mode changes, ship replacements or third-party dependencies. The Kopis Forge and its special main weapon are untouched. The essential Inventory Collector is not replaced or required to be removed.

The source baseline in this repository declares X4 9.00 dependencies. This package also declares 9.00. The exact installed game build, DLC set and complete installed mod list were unavailable; compatibility with those cannot be certified here. Physical crystal mining and demolition deliberately wait in low attention. Station ray casts, anomaly traversal, NPC transfer, surrender allegiance and direct turret controls need runtime checks.

To stop an occupation, change that ship's Default Behaviour. Before removing the extension, change all occupation defaults to native behaviours and finish or disembark custom taxi passengers. `save="1"` records the extension requirement in saves while custom orders are present.

See IMPLEMENTATION.md for evidence and constraints, TESTING.md for reproducible tests and CHANGELOG.md for version history.

Reputation update: completed escort/taxi services, actual morale improvements, verified trade-route escort arrivals and genuine contraband reports can award a small faction increase. Completed accounted crystal broker sales use a smaller trade increase. The shared 30-minute faction cooldown prevents stacking; discovery, sightseeing, demolition and captures do not grant reputation by proximity.
