# Galactic Occupations

Version 0.2.3 development build, 7 November 2026. Author: Vardath.

**Runtime verification is pending for all twelve occupations.** This extension contains executable AI orders, MD state/passenger handling, and Lua menu integration. The build environment cannot run X4. Source checks and mocked UI tests do not establish gameplay success.

## Install and assign

1. Close X4. Extract `Galactic_Occupations_0.2.3_DEV.zip` into the X4 installation directory, producing `extensions/vardath_galactic_occupations/content.xml`. Replace this extension's older files in place.
2. Enable Galactic Occupations and load your existing save. No new game is required by the implementation.
3. Select an eligible player-owned ship with an AI captain, open Behaviour, and select a Default Behaviour below.
4. Use range **99 for the whole connected galaxy**, 0 for the home sector, or 1–98 for a jump radius. Risk 0/1 avoids hostile destinations; 2 permits them. Normal travel blacklists remain enforced.
5. Direct orders have native priority. Registered occupations receive a one-time restart of their current default behaviour through the native editable home parameter; its value and other parameters are retained. Recovery waits while a direct order or player control is active. Re-select the behaviour if an older saved call does not resume correctly.

## Occupations

| Behaviour | Actual task implementation | Payment or qualification |
|---|---|---|
| Galactic Escort Service | Reads a commercial vessel's actual station destination, escorts it and verifies meaningful proximity plus arrival. | Custom 12,000 Cr fee and small faction reputation after success. No vanilla mission-offer acceptance is claimed. |
| Galactic Taxi Service | Picks a friendly station, reserves up to ten free crew berths, places actual passenger actors at its dock, uses vanilla NPC movement to board, flies to a preferably different-sector destination and disembarks them. | 8,000 Cr per delivered passenger. Every accepted NPC must enter the ship context through walking or a verified off-screen room transfer before departure. Other crew are retained. |
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

Jobs use a cached native connected-sector graph and rotate sectors after an assignment instead of consuming local work indefinitely. The tour catalogue queries the entire operating scope and records distinct visits. Range 99 uses the native unlimited search form (omitting maxdistance), rather than a literal 99-jump ceiling. Travel may discover paths and respects native travel blacklists/access restrictions. Disconnected or story-locked spaces are not fabricated as reachable.

Galaxy coverage describes target discovery and travel. Physical effects still depend on engine simulation: crystal harvesting and demolition need high attention; module surface raycasts need loaded collision geometry; real NPC boarding needs valid, walkable docking/ship room connections. The taxi stays docked and reports this dependency until it can place and board the actual NPCs. It does not substitute a passenger template for physical boarding. Off-screen boarding/unloading attempts real cue-actor room transfers with context proof; engine room availability still needs runtime verification. Off-screen crystal harvesting is not delivered.

## Passengers and tours

Capacity is rechecked at pickup and native `create_npc_template force="false"` reserves only available berths. The manifest accepts at most ten passengers and does not dismiss service crew or marines. NPCs are placed at the actual docking module, then sent aboard with vanilla `npc_move_to`. Per-passenger room-context acknowledgments gate departure. A reserved seat is insufficient.

Contracts and partial boarding/delivery survive interruptions. Resume the same passenger occupation to finish passengers already aboard; switching between taxi and tour does not silently reclassify their contract. Old single-passenger taxi state is adopted without replacing the actor/template and requires actual boarding confirmation.

Tours book only when the available catalogue contains enough distinct sites. Range 0 may offer too few; increase the range. Each trip records sites and sectors separately from the long-term itinerary. Ten stops and three sectors are defaults, with the sector minimum limited by actual catalogue coverage. Booked fare/stops persist during the trip. A destroyed drop-off station is replaced by a suitable accessible station. Off-screen drop-off attempts to transfer the same accepted cue actors into real destination rooms. Only a successful connection and actual station/outside-ship context count as disembarkation; missing rooms retain the manifest without a fare. Visible passengers walk off with the native NPC movement signal.

## Mine Crystals in Loadout

For an existing player S/M ship, open Map → Information → Loadout → Turret Behaviour. **Mine Crystals** is added to the all-turret, individual and group dropdowns. Existing-ship outfitter mode controls receive it too; unbuilt ship plans do not contain custom engine mode IDs. The Loadout panel also shows the current occupation status, including boarding counts and survey progress. A loaded menu addon is required; it may take up to ten seconds to attach after load. Docked cockpit-menu integration is not included.

This is a selectable UI option backed by MD/direct turret control, not an additional engine enum. Selecting it records a per-turret flag. Selecting any native mode clears that overlay and calls the original handler. Normal modes and armed states are not rewritten. The standalone controller targets real nearby deposits within turret range without issuing ship movement or collection orders. Assign Autonomous Crystal Miner for searching, approaching, collecting and selling. An unconfigured miner initially selects eligible turrets; beam-only is the conservative default.

The controller excludes missiles/repair weapons, checks operational state/range/LOS/traffic and releases manual aim on invalid targets or danger. Engine firing arcs, accurate hits, disarmed behavior, native-mode coexistence and menu appearance have not been demonstrated in game. These remain dedicated acceptance tests.

## Payments and the main ledger

Open the player's main **Transaction Log**. The extra income panel and every transaction renderer, graph, table-body, search and paging override from 0.2.0 are removed. The replacement uses only the published `createTransactionLog_on_before_adding_entry` callback when UI Extensions supplies it. It annotates the text of real native payment rows. It cannot add rows, change amounts or create transactions.

Each unambiguously identified payment shows the occupation or builder payment type and ship in the normal transaction label. Its description includes the service, employer/station where relevant and lifetime earned total/payment count for that job. Use the native search box and time range; native filtered totals remain based on actual transactions. Builder hire, construction, standby and final-settlement payments are distinct labels. Crystal brokerage labels actual inventory-sale transfers.

**Keep Protected UI Mode enabled.** This extension does not change that setting or replace protected game UI files. It imports only the native `ffi` module and uses functions already declared by the vanilla helper. The optional callback is supplied by UI Extensions and HUD; availability in the actual Protected UI/load-order combination still needs an in-game check. If that callback is unavailable, the vanilla ledger retains its normal generic payment labels. Every new verified payment also receives a detailed native Logbook receipt with its amount. The Logbook is a separate vanilla screen, not a substitute claim that custom financial labels work without the callback. In 0.2.2 a shared saved cursor writes paid-journal receipts from MD independently of ship AI, at up to five receipts per five-second batch. It recovers at most the newest twenty prior records on first use, includes their original game time, and never re-pays them. Clear the Logbook search and select General/All; search for `Vardath Payment`.

Service fees use native `reward_player` only after verified work. The journal records the observed account increase; crystal sales record the successful native transfer. Each new receipt is bound to an actual engine transaction ID, amount, event type and timestamp. Equal simultaneous payments are bound at payout time; ambiguous historical payments and condensed/deleted engine records remain vanilla. No historical income is replayed or added to totals a second time. The existing 5,000-payment journal and lifetime per-job counters are retained on the player entity, without the removed preview UI. In the new adapter, the financial ledger's engine retention/condensation rules still apply.

Passenger contract IDs and completion serials prevent repeated fares. Tours pay only after the required distinct visits and passenger drop-off. Discovery, scanning, lure, demolition and recruitment do not receive invented cash rewards.

Small external-faction reputation awards follow eligible verified escort/taxi/tour services, actual morale improvements, genuine contraband reports and completed trade-route escorts. A shared thirty-minute faction cooldown limits accumulation. Accounted crystal broker sales use a smaller trade award. Proximity alone does not grant reputation.

## Compatibility and verification

X4 9.00+; no required DLC/third-party mod for this extension. Other mods retain their own dependencies. All scripts/assets use namespaced paths; no vanilla XML/AI script is replaced. Kopis Forge, Astrid equipment, ownership and crew are untouched. Inventory Collector can remain enabled; already removed drops cannot be credited twice by native collection.

Job, reservation, scan, passenger and turret state now lives in persistent tables on the **player entity**, because X4 supports entity blackboards, not ship/turret/component blackboards. The turret UI receives a small exported list; it does not query a nonexistent turret blackboard. Physical weapon commands run in visible-attention blocks. The crystal task listens for drops from its exact deposit, and the passenger room listener uses a live actor group.

The income callback never wraps `Helper.createTransactionLog` or `Helper.transactionLogSearchHelper`. The crystal addon still delegates native mode selections to existing handlers. Existing-ship turret integration under Protected UI is unverified; this update neither disables protection nor changes third-party UI mods.

See `IMPLEMENTATION.md`, `TESTING.md`, and `CHANGELOG.md`. Development checks pass separately from all still-pending in-game lifecycle and failure tests.

## 0.2.2 startup recovery and crystal acceptance

Fully exit X4 before replacing files. Load the existing save, open the vanilla Logbook with all categories/search cleared, and check for the one-time `Galactic Occupations 0.2.2 loaded` entry. Assign an occupation again to any ship already on Hold Position. New running order objects produce `behaviour active`; this acknowledges the running AI, not task success. Retained current default occupations receive a one-time native editable-parameter restart; direct orders keep priority. Previously damaged imported call stacks may still report an initial import warning before recovery. This has not been tested in X4 here.

The twelve order location expressions now always return a valid component, including before state is initialized. Missing legacy passengers are guarded inside the template lookup, no-police sectors are skipped, restored navigation has a safe empty list, and candidate searches yield between candidates. A helper returning early does not intentionally end its default behaviour: wrappers wait and retry.

For crystal mining, use a player-owned S/M ship with an AI captain and at least one operational compatible deployed turret. With the conservative beam-only option enabled, it must be a beam turret. Select Mine Crystals for that turret if manually configured. A missing compatible selection leaves the occupation running with a Logbook/status explanation; it does not equip anything or select Hold Position. Main guns alone do not satisfy this turret-control implementation.

Test startup separately from harvesting. After the `behaviour active` acknowledgment, remain near a real asteroid field so the engine loads crystals. Verify the selected target is a real deposit, a turret aims and actually damages it, the deposit's drop event supplies real objects, native collection removes those drops and increases the pilot's inventory, and any later sale produces exactly one native payment/receipt. Try a blocked arc, no beams, a destroyed deposit and an interruption/save/reload. Until these have been observed in the game, crystal harvesting remains UNVERIFIED. The turret preflight and parser corrections alone do not establish a working harvest cycle.

## 0.2.3 closed passenger trip and patrol changes

Taxi now explicitly undocks after the complete batch boards, including for same-sector delivery, travels to a suitable station, docks and waits until the whole accepted manifest has left the ship. Tours select their first sightseeing target after boarding, explicitly undock and cover the booked itinerary before using the same docking/unloading/fare path. An already docked, interrupted unload resumes without needlessly departing again. Walkable destinations are preferred/replaced when unsuitable. Stopped NPC paths retry; no elapsed-time branch marks a passenger delivered.

The shared movement helper also fixes leaving docks for scanners, mappers, crystal brokerage, morale, recruitment and other navigation. It preserves the native player pilot-seat guard. NPC interiors must support valid room connections; unsuccessful walking/transfer attempts remain unpaid and may need the relevant scenes loaded.

Escort/patrol now follow actual commercial destinations using a persistent convoy record. They use temporary, separately queued native defensive attacks, bounded to sixty seconds; an attack ending or failing cannot cancel the occupation default. Player commands retain priority. Normal player-created orders are not cleared by the combat watchdog. The old native fleet escort subroutine required matching owners and could replace the job with AssignCommander/Hold; it is no longer called.

See `JOB_REVIEW_0.2.3.md` for every occupation, concrete native-source findings and remaining acceptance work. User-observed boarding does not verify the full tour, drop-off, patrol, crystal harvesting or other still untested gameplay effects.

Outside rendered simulation, boarding also attempts an actual same-actor transfer from a real pickup-station room to a valid ship room. It still requires the exact passenger entity to exist in ship context and its native passenger template to be out of transit. No seat reservation or elapsed timer alone acknowledges boarding. The user-verified visible walking branch is retained. If the engine cannot connect either room, the batch waits unpaid. This alternative remains runtime-unverified.
