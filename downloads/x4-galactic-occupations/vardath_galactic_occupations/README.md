# Galactic Occupations

Version 0.2.0 development build, 7 November 2026. Author: Vardath.

**Runtime verification is pending for all twelve occupations.** This extension contains executable AI orders, MD state/passenger handling, and Lua menu integration. The build environment cannot run X4. Source checks and mocked UI tests do not establish gameplay success.

## Install and assign

1. Close X4. Extract `Galactic_Occupations_0.2.0_DEV.zip` into the X4 installation directory, producing `extensions/vardath_galactic_occupations/content.xml`. Replace this extension's older files in place.
2. Enable Galactic Occupations and load your existing save. No new game is required by the implementation.
3. Select an eligible player-owned ship with an AI captain, open Behaviour, and select a Default Behaviour below.
4. Use range **99 for the whole connected galaxy**, 0 for the home sector, or 1–98 for a jump radius. Risk 0/1 avoids hostile destinations; 2 permits them. Normal travel blacklists remain enforced.
5. Direct orders have native priority. Existing occupations receive a one-time internal recovery signal on upgrade; default orders and direct-order queues are preserved. Re-select the behaviour if an older saved call does not resume correctly.

## Occupations

| Behaviour | Actual task implementation | Payment or qualification |
|---|---|---|
| Galactic Escort Service | Reads a commercial vessel's actual station destination, escorts it and verifies meaningful proximity plus arrival. | Custom 12,000 Cr fee and small faction reputation after success. No vanilla mission-offer acceptance is claimed. |
| Galactic Taxi Service | Picks a friendly station, reserves up to ten free crew berths, places actual passenger actors at its dock, uses vanilla NPC movement to board, flies to a preferably different-sector destination and disembarks them. | 8,000 Cr per delivered passenger. Every accepted NPC must physically enter before departure. Other crew are retained. |
| Station and Component Scanner | Selects unscanned modules and defence elements, approaches actual surface positions, retries three viewing angles and sustains ten seconds of clear LOS. Publishes native per-component scan data and checks for a real level/information increase. | Explicit custom survey equivalent. The documented scan action uses the player's scan cap; the AI ship needs scanner software but does not need to match the player's active scanner level. No whole-station scan flag. |
| Wormhole and Anomaly Mapper | Surveys real anomalies, gates and accelerators; logs actual anomaly destination sets separately from ordinary links. | Optional transit fallback first attempts traversal, then may move the same ship to a permitted real exit. Mission anomalies/capitals excluded. |
| Galactic Sightseeing Tour | Boards up to ten real passengers, visits ten distinct global sights by default, dwells at viewing distance, covers at least three sectors where available and returns to a station for drop-off. | Luxury fare defaults to 500,000 Cr per passenger; up to 5,000,000 Cr. Ticket price and 10–20 stops are configurable. No payment for isolated visits, boarding or unfinished tours. |
| Autonomous Crystal Miner | Searches real asteroid `class.crystal` deposits, uses selected suitable turrets on the deposit, records its real drops and runs native collection. | Mine Crystals is a custom Loadout option backed by direct control. S/M, suitable deployed weapons and high attention are required. Actual pilot-inventory sales are accounted separately. |
| Hostile Lure and Interception | Provokes a manageable hostile, tests actual pursuit, retreats toward a stronger friendly defender and breaks off on danger/failure. | Does not force enemies to pursue or create a completion reward for failed pursuit. |
| Asteroid Demolition | Fires actual weapons at destructible asteroids; checks destruction, times out ineffective attacks and can collect real drops. | S/M physical high-attention work. No simulated OOS destruction. |
| Fleet Morale Booster | Approaches a friendly crewed ship, performs sustained support and increases eligible non-passenger crew morale by one step, capped at 15. | Reputation requires an observed improvement. Six-hour target cooldown by default and shared faction cooldown. |
| Traffic Control and Cargo Inspection | Performs a close timed NPC-style inspection, checks local police-faction cargo/inventory laws and reports actual contraband. | Custom inspection equivalent. Selecting a neutral ship does not make it hostile. Reputation requires a genuine contraband result. |
| Emergency Ship Recruitment | Negotiates with capturable non-mission hostiles below 25% hull and transfers the existing ship on success. | Conservative probability, failure cooldown, retained damage/equipment and crew-allegiance handling. Runtime transfer safety still needs testing. |
| Trade Route Patrol | Follows actual trader destinations, escorts vulnerable traffic and intercepts manageable threats along their route. | Routes follow commercial voyages. Verified arrivals may earn small reputation; no ambient patrol income. |

## Galaxy coverage

Jobs use a cached native connected-sector graph and rotate sectors after an assignment instead of consuming local work indefinitely. The tour catalogue queries the entire operating scope and records distinct visits. Range 99 is an unlimited sentinel, rather than a literal 99-jump ceiling. Travel may discover paths and respects native travel blacklists/access restrictions. Disconnected or story-locked spaces are not fabricated as reachable.

Galaxy coverage describes target discovery and travel. Physical effects still depend on engine simulation: crystal harvesting and demolition need high attention; module surface raycasts need loaded collision geometry; real NPC boarding needs loaded, walkable docking/ship interiors. The taxi stays docked and reports this dependency until it can place and board the actual NPCs. It does not substitute a passenger template for physical boarding. Full unattended/OOS physical boarding and harvesting are not delivered.

## Passengers and tours

Capacity is rechecked at pickup and native `create_npc_template force="false"` reserves only available berths. The manifest accepts at most ten passengers and does not dismiss service crew or marines. NPCs are placed at the actual docking module, then sent aboard with vanilla `npc_move_to`. Per-passenger room-context acknowledgments gate departure. A reserved seat is insufficient.

Contracts and partial boarding/delivery survive interruptions. Resume the same passenger occupation to finish passengers already aboard; switching between taxi and tour does not silently reclassify their contract. Old single-passenger taxi state is adopted without replacing the actor/template and requires actual boarding confirmation.

Tours book only when the available catalogue contains enough distinct sites. Range 0 may offer too few; increase the range. Each trip records sites and sectors separately from the long-term itinerary. Ten stops and three sectors are defaults, with the sector minimum limited by actual catalogue coverage. Booked fare/stops persist during the trip. A destroyed drop-off station is replaced by a suitable accessible station. Off-screen drop-off uses the native passenger manifest only after previous physical boarding and actual docking.

## Mine Crystals in Loadout

For an existing player S/M ship, open Map → Information → Loadout → Turret Behaviour. **Mine Crystals** is added to the all-turret, individual and group dropdowns. Existing-ship outfitter mode controls receive it too; unbuilt ship plans do not contain custom engine mode IDs. The Loadout panel also shows the current occupation status, including boarding counts and survey progress. A loaded menu addon is required; it may take up to ten seconds to attach after load. Docked cockpit-menu integration is not included.

This is a selectable UI option backed by MD/direct turret control, not an additional engine enum. Selecting it records a per-turret flag. Selecting any native mode clears that overlay and calls the original handler. Normal modes and armed states are not rewritten. The standalone controller targets real nearby deposits within turret range without issuing ship movement or collection orders. Assign Autonomous Crystal Miner for searching, approaching, collecting and selling. An unconfigured miner initially selects eligible turrets; beam-only is the conservative default.

The controller excludes missiles/repair weapons, checks operational state/range/LOS/traffic and releases manual aim on invalid targets or danger. Engine firing arcs, accurate hits, disarmed behavior, native-mode coexistence and menu appearance have not been demonstrated in game. These remain dedicated acceptance tests.

## Payments and the main ledger

Open the player's main **Transaction Log**. Its existing transaction list now displays job labels on unambiguous matching native payments and clearly identified verified receipt rows for journaled credits without a matching detailed entry. The list uses its existing search, time window and page controls. Native transaction IDs, times and amounts are preserved. The native account graph remains. The **Occupation & builder income** preview section below the graph is also retained for comparison. Switch between individual payments and lifetime earnings; filter by occupation or builder hire, construction wages, standby wages and final settlement. Each record includes game time, amount, ship and service/employer details. Descriptions and receipt rows are a UI integration with verified payment data; the game exposes no direct description argument on reward_player, so this does not claim to rewrite its internal transaction database.

Occupation service fees use the documented native reward action after verified work. Records use the observed account increase. Passenger contract IDs and per-ship completion serials prevent repeated rewards. Tours pay only after the required distinct visits and passenger drop-off. Crystal sales record successful accounted sales, not collected or generated inventory. Discovery, scanning, lure, demolition and recruitment have no invented cash rewards; their total remains zero unless a genuine payment path is added.

The recent detailed journal retains 5,000 payments shared by both extensions; lifetime job totals are not truncated. Older payments before this update cannot be reliably reconstructed. Either extension can display the shared income section without requiring the other.

Small external-faction reputation awards follow eligible verified escort/taxi/tour services, actual morale improvements, genuine contraband reports and completed trade-route escorts. A shared thirty-minute faction cooldown limits accumulation. Accounted crystal broker sales use a smaller trade award. Proximity alone does not grant reputation.

## Compatibility and verification

X4 9.00+; no required DLC/third-party mod for this extension. Other mods retain their own dependencies. All scripts/assets use namespaced paths; no vanilla XML/AI script is replaced. Kopis Forge, Astrid equipment, ownership and crew are untouched. Inventory Collector can remain enabled; already removed drops cannot be credited twice by native collection.

The shared income addon wraps the existing transaction-log builder once. The crystal addon wraps selected existing-ship menu builders and delegates native choices. Other UI replacements or a changed game menu structure may require integration changes. Protected-UI operation is unverified; neither addon requires FFI or a third-party support API.

See `IMPLEMENTATION.md`, `TESTING.md`, and `CHANGELOG.md`. Development checks pass separately from all still-pending in-game lifecycle and failure tests.
