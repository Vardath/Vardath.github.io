# Galactic Occupations 0.3.1 development build

Thirteen persistent, autonomous ship behaviours, plus a queued single-station hacking command. Author: Vardath. Updated 7 November 2026. **X4 runtime verification remains pending.** Static validation and mocked tests do not establish NPC pathing, weapon hits, native panel effects, live payments or save/load execution.

## 0.3.1 repair: station menu and crystal activity

The station menu now replaces its cached Checking row **before** requesting the native redraw. It polls for missed replies while open, normalizes MD boolean values, and uses the native UI clock for a ten-second timeout/retry, even if simulation time is paused. Mission Director lookups still need the game unpaused. Empty/unavailable replies are displayed explicitly; no generic panel list is fabricated. The confirmed source defect and corrected draw-only tests are described in [MENU_CRYSTAL_REVIEW_0.3.1.md](MENU_CRYSTAL_REVIEW_0.3.1.md).

Crystal Miner now has **Follow active crystal simulation** (default on). Out of active simulation, firing cannot harvest crystals. With the fallback enabled, the ship travels normally to the player's permitted active sector and stays with materialised objects instead of endlessly rotating through sectors where its firing task refuses to run. This does **not** enable out-of-sector crystal physics. All-sector range remains supported; the fallback operates wherever permitted active simulation is available, and respects range, risk, blacklists and direct orders. Turn it off to retain ordinary galaxy-sector exploration. For reliable verification, be in an asteroid field so real crystals and collision geometry are loaded. Re-select Crystal Miner after upgrading if the new setting is absent from an old order.

The miner also recovers actual nearby crystal drops from their native ware contents, independently of the shooting task's event. It waits briefly for native pickup and, if an NPC pickup leaves the actual drop untouched, tries native collection by the player's occupied ship to route it directly into player inventory. No crate is manually destroyed and no replacement crystal is generated. Only observed player credit is recorded. If native pickup still fails, the real drop stays queued for retry. `GO crystal search:`, `GO crystal fire result:`, `GO crystal pickup:` and `GO crystals:` separate discovery, damage, collection and actual delivery in the new log.

**The user has not yet observed any crystals returned.** This repair addresses concrete control-flow and recovery limits; its physical firing, native pickup and resulting inventory still require in-game verification. [Current report and tests](MENU_CRYSTAL_REVIEW_0.3.1.md).

## Install and operate

1. Fully exit X4. Extract `Galactic_Occupations_0.3.1_DEV.zip` into the game installation directory, producing `extensions/vardath_galactic_occupations/content.xml`. Overwrite this extension in place. Keep Protected UI enabled and Inventory Collector installed.
2. Load the existing save. The implementation does not require a new game. Existing passengers, itineraries, equipment, crew, ownership and diagnostic history are retained. Reassign jobs that an older build already lost to Hold Position; intentional player orders are not overwritten.
3. Select a player ship with an AI captain, then select the occupation in Default Behaviour. Range **99 means the entire connected accessible galaxy**, 0 means the home sector, and 1–98 specifies a jump radius. Native travel blacklists still apply. Risk 0/1 avoids hostile territory; 2 permits it.
4. Inspect vanilla General Logbook for `Galactic Occupations: activity`, `completed` and `Vardath Payment`. Five-minute activity reports show observations, not paid completions. Debug lines `GO completed:` identify successful work; `GO payment:` includes promised/actual money and before/after balances.

## Behaviours

| Behaviour | Actual implemented work | Money and constraints |
|---|---|---|
| Galactic Escort Service | Follow a trader's actual station destination; require arrival, time and meaningful close-range protection. | Custom 12,000 Cr fee for a verified foreign-faction service, plus controlled reputation. Does not accept vanilla mission offers. |
| Galactic Taxi Service | Board up to ten actual NPC passengers according to free crew berths, travel to a station and disembark the accepted manifest. | 8,000 Cr per delivered passenger; no fare for reservations, approach or timer expiry. Native NPC movement and verified off-screen room transfer are used; real interiors are required. |
| Station and Component Scanner | Approach unscanned module surfaces, retry viewing angles, sustain ten seconds of clear line of sight, then verify native per-component scan information increased. | Explicit custom survey equivalent using the player's scan cap. No global station-scanned flag or employer payment. Geometry may require loaded simulation. S/M ships. |
| Wormhole and Anomaly Mapper | Survey real anomalies/gates/accelerators; catalogue actual destinations separately. | Optional safe transit fallback uses a permitted real anomaly exit and the same ship. No invented links or wage. |
| Galactic Sightseeing Tour | Board up to ten real passengers; visit ten distinct global sights and normally at least three sectors; dwell, return and disembark. | Default 500,000 Cr per delivered luxury passenger, multiplied by verified stops divided by ten. Fare requires the booked route and completed disembarkation. |
| Autonomous Crystal Miner | Find real asteroid crystal components, aim forward guns/turrets, harvest and collect attributed native drops; forward existing captain-held crystals to player inventory. | All normal ship sizes and armed turret/weapon types may undertake it. Suitable range/arcs/ammunition and physical simulation remain required. No cargo hold, automatic sale or free crystals. |
| Hostile Lure and Interception | Provoke an eligible hostile with a forward laser, verify pursuit and retreat toward actual friendly forces. | No success when pursuit fails, no automatic fee. Physical weapon simulation required. |
| Asteroid Demolition | Fire at actual destructible asteroid targets and verify destruction; optional resource collection. | S/M ships, suitable forward weapons and loaded simulation. No reward for a vanished reference. |
| Fleet Morale Booster | Improve actual eligible crew morale at interaction distance; enforce vessel and faction cooldowns. | Small reputation reward only after a real improvement, no approach reward or automatic cash. |
| Traffic Control and Cargo Inspection | Use native cargo inspection and the jurisdiction's cargo illegality rules. | Respects relations and jurisdiction; no forced neutral hostility or automatic wage. |
| Emergency Ship Recruitment | Communicate with a capturable hostile below 25% hull; conservative configurable morale/crew/class probability and retry cooldown. | On success transfer the existing ship without replacing hull/equipment. Protected and mission targets excluded. No guaranteed surrender or fee. |
| Trade Route Patrol | Follow actual commercial traffic and its live destination, protect it, then choose another corridor. | **8,000 Cr per verified protected foreign-trader arrival**. Own traders remain unpaid. Arrival, minimum duration and close-range samples are required. |
| Galactic Station Hacker | Retrieve real tools remotely, dock at non-player faction stations, send an existing crew actor to a real native panel, verify the native effect and wait for their physical return. | Native tool/price costs apply. No employer, cash payment or reputation grant for sabotaging a station. Risk defaults to 2; docking permission still required. |

## Galactic Station Hacker

The job searches locally between staggered galaxy-wide sector changes. It can use any eligible faction station with a suitable dock, walkable interior and actual hacking panel. It prefers an existing idle service crew member or marine; otherwise it uses the existing captain. It does not create a replacement crew actor, remove a crew template, change crew ownership/role, or teleport a crew member ashore.

Panel rooms and labels come from native control-panel data. The thirteen supported native panel types are turrets, construction, discounts, engineering, production, shield generators, storage, security/watchdogs, hiring discount, modification discount, repair discount, trader discount and radar. Only panel types found on the actual station appear. Already active effects are disabled.

Before travel, the job obtains the native panel type's required items from player inventory and loans only quantities actually removed to the chosen actor. At dock, the actual panel's native API supplies the final tools and price. Missing tools cause a wait and another inventory check **every ten game minutes**. Partial withdrawal/credit/return failures retain accounting and do not create tools. Native consumption is serialized so another hacker does not borrow those tools during the call. Unused loans return to player inventory.

The same NPC receives vanilla `npc_move_to` instructions through the dock and station interior, reaches a native walkable point within four metres of the actual panel, and works for ten seconds. The UI bridge then calls the **same `StartControlPanelHack` API as the native confirmation menu**. That API has no NPC-actor parameter: the native operation is attributed to the player after the crew actor reaches the panel. This is the implemented alternative to an NPC-specific panel-hacking API. It is not a simulated whole-station hack flag. A successful native call alone is insufficient: the requested station panel effect must become active and the same deployed actor must return to an actual ship room before completion.

**The remote native API invocation and NPC paths have not been tested in X4 here.** In particular, whether the engine permits this player-attributed call away from the player and streams a usable NPC path must be checked in game. Missing geometry/API/effect yields waiting or failure with no invented hack/payment. Before deployment, unavailable interiors/panel paths time out after five minutes and return unused tools before another station is tried. Missing-tool waits are separate and retain their ten-minute recheck. Native NPC transit may be handled off screen by the engine; visible physical walking requires loaded interiors. If a direct order takes the ship away while the actor is ashore, that order has priority and the actor waits for the ship to redock before walking back. A captain ashore cannot safely pilot the ship to restore that link; the player may need to restore it. No teleport or duplicate captain is used to conceal that limitation.

## One station, selected panel

Select an AI-controlled player ship on the map and right-click a faction station. **Hack station → actual panel name** adds a finite `Hack selected station panel` order to the existing queue. This additive native submenu lists the station's discovered panel types. It may first say it is checking panels. The existing default behaviour and earlier queued orders remain intact. It uses the same tools, physical actor, effect and return checks as the autonomous job. Choosing several ships does not bypass the station reservation; they wait for access and do not all charge an already-active panel.

## Crystal turret control and inventory

Mine Crystals is a selectable addon option in Map → Information → Loadout → Turret Behaviour for existing player S/M/L/XL ships, including groups and missile turrets. Existing-ship outfitter controls also receive it. It is a controller layered on native turret control, not a new engine enum. Native selections and equipment remain intact; the standalone controller yields to the active crystal occupation. No custom mode ID is written into a build plan.

Only real nearby drops whose native contents include crystal inventory wares enter collection; drop-event attribution and direct loose-drop recovery are both used. Native pickup must consume the actual drop. Only observed withdrawal from the captain and observed credit to player inventory are counted; uncredited remainder is restored. Existing captain-held crystals on an assigned miner are forwarded too. No generated items, cash substitutes, cargo requirements, beam-only restriction, captain holding limit or automatic sale. Accurate firing, pickup and out-of-sector availability still require runtime verification. See the historical [crystal review](CRYSTAL_REVIEW_0.2.5.md).

## Payments, reputation and the vanilla UI

Only verified sponsored services and actual sales can issue money; exploration, hacking and other unsponsored actions do not receive wages. Rewards use the native credit action and only the **observed positive player-balance change** enters the income history. A promised reward with zero balance change generates a warning. Duplicate assignment/passenger payment guards persist. Small eligible service reputation gains use a shared 30-minute faction cooldown; hacking grants none.

The vanilla transaction ledger remains the original renderer. There is no custom income screen, row injection, graph/table/search replacement or fabricated financial transaction. An optional published UIX callback adds descriptions to uniquely matched existing native payment records; without that callback the engine's ordinary descriptions remain. The shared MD consumer writes detailed paid receipts in vanilla General Logbook independently of UIX, including Builders payments. Item delivery is logged separately from credits.

## Compatibility and verification

Requires X4 9.00 or later; DLC content is discovered at runtime. No dependencies on removed mods, no vanilla AI replacements, no ledger screen replacement and no change to Protected UI or Inventory Collector. Other extension sources, including Kopis Forge's special weapon and Astrid equipment, are unchanged in this delivery. The optional four-mod bundle includes their current versions unchanged.

[Hacker/log review](HACKER_REVIEW_0.3.1.md), [reproducible in-game tests](TESTING.md), [implementation notes](IMPLEMENTATION.md) and [version history](CHANGELOG.md) distinguish source checks from unverified runtime stages. Keep a backup before testing this development build.
