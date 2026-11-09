# Galactic Occupations 0.4.8 development build

Thirteen persistent, autonomous ship behaviours, plus a queued single-station hacking command. Author: Vardath. Updated 10 November 2026. **X4 runtime verification remains pending.** Static validation and mocked tests do not establish NPC pathing, weapon hits, native panel effects, live payments or save/load execution.

## 0.4.8: capital tours and scanner physics

Galactic Sightseeing Tour now accepts S, M, L and XL ships with spare crew berths and a compatible station dock or pier. Visible L/XL services use actual ship/station transporter waypoints: the booked NPC walks to the source, transfers to the receiving room, and must be confirmed aboard or ashore before progression. Capacity remains up to ten passengers. New bookings retain the ten-stop default, and existing itineraries, fares, interruptions and cancellation rules persist.

The scanner checks active visible attention, loaded geometry and player-sector context before surface queries, including after movement. Inactive modules use the existing remote survey path when enabled. No turret, ledger or menu layouts change. Companion Forge/Astrid, Builder, habitat, drone and teleport sources remain unchanged.

The latest supplied log confirms 623 uniquely keyed payments totalling 994,060,000 Cr, each matching its recorded balance change. 459 Python contracts and 91 Lua mocks pass; the new native transporter, physics and save/load behavior needs live X4 acceptance. [Full log findings, limits and live checks](LOG_REVIEW_0.4.8.md). The separate Compatibility 1.0.1 and Hyperion Ascendant packages address the other bounded errors and quest/ship request.

## 0.4.7: hacker offices, signal results and worker scheduling

Hacker menus now inspect the installed native security/engineering room definitions as well as existing rooms. A selected missing office is prepared with real native assets only after actual docking; actual panel slots, tool costs, effect verification and same-crew return remain mandatory. Old partial catalogues refresh. Extension-created rooms have guarded cleanup; ordinary station rooms and all UI files are unchanged.

Signal surveys now find assigned off-screen market contacts and the native NPC registry, and report accepted surveys, confirmed native discounts and actual visible offers in the existing General logbook/debug log. A request is distinguished from a generated offer; black-market access still requires the actual native delivery job. Crystal worker bookkeeping now yields between fast-return calls. Existing bookings, stock, invoices, crews, orders and the ten-stop tour default remain.

The new log confirms **66,010,000 Cr** across 192 matching payment records. Its logged worker path now has explicit yields, but the crash cause cannot be established: the game continues for another 3,986 game seconds and the file contains no fatal/crash stack. [Full findings, constraints and live checks](LOG_REVIEW_0.4.7.md). 440 Python contracts and 91 Lua mocks pass; new native office/panel execution requires live X4 testing. Companion sources remain unchanged.

## 0.4.6: spacesuit context reset and station NPC guard

A stalled confirmed **Use Spacesuit** request now rebuilds the original ship context using the native teleport command, waits for the actual native teleport event, then makes one suit exit. It verifies the suit, both control references, room and transit state. A failed exit gets one return to the same ship; the request then stops. Changed player/source context cancels recovery. Existing saved requests are cleared on upgrade/load. No crew, equipment, ship orders or UI layouts are changed.

The new log confirms the previous recovery fired; it ends 0.36 game seconds later, before the old verification could run. A separate native station-workforce error indexes an empty service-slot list. One exact pre-creation guard prevents that invalid branch. The log also confirms **10,700,000 Cr** from 26 crystal sales and two completed tours, with all 28 observed balance differences matching. [Evidence, limits and reproducible checks](LOG_REVIEW_0.4.6.md). 415 Python contracts and 91 Lua mocks pass; new native recovery/population execution still requires live X4 confirmation. Companion sources remain unchanged.

## 0.4.5: ten-stop default and one extra game hour

Newly assigned Tours default to **10 stops**; valid existing settings and accepted bookings keep their promised route/fare. Active booked-tour task and native docking deadlines gain one game hour once per helper-issued deadline. Cancelled-tour grace gains one hour above its previous duration-based estimate, with a **three-hour minimum**; pending saved deadlines extend once. Temporary orders retain the party, and taxi/crew timers remain unchanged. Default fare stays 500,000 Cr per delivered passenger.

The new manifest44 log records four completed twenty-stop tours and 193 crystal sales, totalling 28,993,000 Cr in balance-matched payments. It has no error block explicitly naming this suite, but records an unpaid Envoy evacuation after its role changed to Scanner and other task-timeout diagnostics. [Evidence, exact scope, remaining errors and same-save checks](LOG_REVIEW_0.4.5.md). 400 Python contracts and 91 Lua mocks pass; new timeout integration still needs live confirmation. Companion sources, payment/physical passenger/crew actions and UI are unchanged.

## 0.4.4: cold-start and compatibility corrections

The supplied 0.43 log confirms a full twenty-stop tour across fifteen sectors: all ten passengers depart at the booked station and the player receives 5,000,000 Cr. Another 136 crystal sales pay 8,353,000 Cr; all 137 recorded balance differences match their payment amounts. Thirteen scanner visits complete. The previous scanner-reference, CHC and character-model floods are absent.

Fixes one early registry lookup and removes our incorrect explicit-null station-wares overrides (55 logged failures), restoring the original native list argument. Extends optional Auto Trade Subscriptions compatibility to the eighteen additional bare-faction conditions in this log. Its initialization/purchases are not forcibly replayed. AI, navigation, bookings, payments, crew-return actions, turrets, UI and companion sources remain unchanged. 387 Python contracts and 91 Lua mocks pass; new native corrections still need live confirmation. [Evidence, remaining UI/faction errors and existing-save checks](LOG_REVIEW_0.4.4.md).

## 0.4.3: native scanner mission-offer reference

The new 0.42 log confirms 4,137,000 Cr in 68 balance-matched crystal/taxi/escort/patrol payments, nine morale services and ten component/signal surveys. AKD-700 moves across roles and sectors; tours progress as far as 17/20 stops. Fixes five failed native mission-offer requests (ten error entries): the MD cue is `md.GenericMissions.SelectMission`, not a Manager property. A safe existence guard preserves other station benefits if that native cue is unavailable. New literal native-cue validation and eight boundary tests catch the exact old error. 378 Python contracts and 91 Lua mocks pass; corrected native generation remains runtime-unverified here.

Only scanner mission-request gameplay logic and extension metadata change. AI/navigation, crew, bookings, payments, UI and all companion sources remain unchanged. [Full evidence, remaining external errors, limitations and same-save live check](LOG_REVIEW_0.4.3.md).

## 0.4.2: new roles move while old crew recovery continues

Fixes the shared departure gate that held every occupation while a crystal representative remained ashore, including ships already in space. The current crystal service still waits at its own actual shop dock; changing roles permits travel while the original same-NPC twenty-minute recall and financial state continue independently. Background crew visits no longer overwrite another role's status or disable its timeout recovery. Runtime 42 repairs eligible existing workers without taking over player orders or a currently deployed hack.

Scanner eligibility uses the assigned ship's equipment rather than the player's current scan cap or ship class. Completed timed samples can wait in a bounded persistent queue for actual native scan publication while the survey ship keeps working. Signal-leak station effects remain independent. Native information is acknowledged only after a real scan-level change; queued work is labelled pending. [Exact new-log evidence, changes, limits and existing-save live checks](CREW_ORDER_RECOVERY_0.4.2.md). 370 Python contracts and 91 Lua mocks pass. Actual X4 movement, NPC recovery, scan publication and save/load still need live verification. Only Occupations source changes; all companion sources remain unchanged.

## 0.4.1: station signals, passenger handoffs and spacesuit recovery

The station scanner now surveys signal leaks, offers timed off-screen module/network equivalents, applies real station coupons/trade subscriptions and discovers native jobs/black-market contacts. It supports scanner-equipped S/M/L/XL ships and exposes two functional controls. Boarding/departure now accept valid disconnected NPCs and recover stalled visible walks using the same actor. [Mechanics, constraints and reproducible checks](SURVEY_BOARDING_0.4.1.md). These new native paths remain runtime-unverified.

Adds a twelve-second, single-attempt native recovery only after the vanilla Use Spacesuit confirmation, with actual suit/control/room checks, cancellation on later player actions and thirty-second expiry while native transit remains active. Fixes the invalid passenger-recovery pilot role check and adds role-literal validation. [Actual log findings, supported APIs, limits and in-game checks](SPACESUIT_RECOVERY_0.4.1.md).

Kopis/Astrid 1.16 fixes the logged component-blackboard flood and suspends braking during partial player transitions. No Forge weapon asset changes. The new log records ten crystal sale completions totalling 541,000 Cr and 40,000 Cr in escort/patrol balance-confirmed payments. The supplied log predates these boarding changes; their native execution still needs live confirmation. All 348 Python contracts and 91 Lua mocks pass; new spacesuit recovery is unverified in X4 here.

## 0.4.0: delayed crew recall and cancelled passenger departures

Stranded crystal/hacker crew get a same-NPC native recall after twenty game minutes away from their station. Genuinely cancelled taxi bookings get thirty minutes before unpaid evacuation; tours get at least two hours, extended by observed cruise duration. The exact original service in the default/current/queued orders protects passengers during combat, lockboxes, manual orders and player control. Resuming before expiry clears the timer and keeps the party and route. Deliberately recruited passengers remain crew; cancelled contract IDs cannot collect fares.

New tours default to twenty stops; existing accepted bookings retain their promised itinerary. A separate persistent registry handles timed cleanup without taking over ship orders. Normal booked deliveries and earned payments remain unchanged. [Exact rules, native alternatives, tests and live checks](RECOVERY_POLICY_0.4.0.md). All 299 Python contracts and 78 Lua mocks pass; new native recovery execution is unverified here.

## 0.3.9: paid crystal representative return

The new log verifies 337,000 Cr from seven crystal sales, including a physical seven-item, 7,000 Cr sale on Astrid Tours. That representative remained in the counter phase. The exchange now commits its exact paid invoice and persistent return state itself. The independent Mission Director controller can reconcile a completed invoice and recover the already-paid seven-item visit without a second reward. Its saved-visit registry is repaired independently of the AI caller. Actual same-actor ship-room return and restored crew flags remain mandatory before departure; blocked same-dock walks retain their bounded native placement recovery.

Crystal parameter patches now guard missing fields, including an already-version-12 order missing the sales flag. Earlier inserted blocking calls have explicit import-version metadata, safe result reads/defaults and state-preserving runtime-39 recovery. 255 Python contracts and 78 Lua mocks pass. New return recovery is unverified in X4; this log still shows one tour waiting at 0/2 boarding. [Exact evidence, preserved state, remaining errors and acceptance steps](LOG_REVIEW_0.3.9.md). Only Occupations source changes.

## 0.3.8: stock-backed off-screen sales and real passenger handoffs

The new log identifies 27 errors from an NPC passed to an object-only API, plus docked miners with no loaded trader rooms. The invalid call is removed. Physical sales now use native floor/path validation at the real merchant and actual same-crew counter presence/return. `Simulate crystal sales off screen` defaults on: below visible attention outside the player's sector, the miner actually docks and settles only its finite saved stock through an explicitly custom station broker. Cash, invoice retries and controlled reputation are shared with the physical path; no inventory items or fictional visits are generated. Old prepared crew are restored before switching modes; crew already ashore must return.

Taxi/tour retain real named actors and crew-capacity-limited native passenger rosters. Off-screen native-style actor/roster transfers no longer require loaded body points; the same actors materialise when visible. Physical arrival is used near the player. All passengers must leave at the booked station after the whole tour itinerary before the fare settles. Real room lookup is broader and a missing pier flag no longer prevents actual station searches.

242 Python contracts and 78 Lua mocks pass; new native integration is still unverified in X4. This log verifies two 8,000 Cr patrol payments, no crystal or passenger payment. [Exact findings, source provenance, remaining errors and acceptance steps](LOG_REVIEW_0.3.8.md). Only Occupations source changes; other companion mods remain unchanged.

## 0.3.7: crystal-sale first-use and counter recovery

The new log proves service docking and shared travel now progress. Astrid Tours targeted actual crystal deposits with six selected turrets, picked up seven real drops and retained seven sale items. Three older miners retained their 24-item batches. No crystal sale completed: visits stalled at trader discovery or a missing customer position.

The sale now explicitly permits missing first-use population/payment clocks, searches all free nearby NPC positions, and asks for an interaction point at the actual merchant instead of the whole station. A separate cooldown is saved for every failed buyer. New population, movement-request, actual-counter and preparation-failure diagnostics distinguish stages. Destroyed deposit listeners no longer report errors for an expected vanished source. Existing stock, crew, bookings and unpaid claims are preserved; the native ledger and Protected UI remain intact.

211 Python contracts and 78 Lua mocks pass. These fixes still require live confirmation. [Exact log findings, source fixes, remaining errors and acceptance steps](LOG_REVIEW_0.3.7.md). The current six-mod bundle also includes the small Auto Drones 1.02 missing-statistics guard; other companion sources are unchanged.

## 0.3.6: docked services, crew counter sales and galaxy routing

The new log proves finite DockAt was followed by a native automatic Undock before the custom behaviour could resume. A narrow native dispatch guard now permits the exact owned taxi/tour/crystal/hacker worker to resume at its recorded service dock under a bounded lease. Explicit departure clears that handoff. This addresses passenger departure and crystal-sale execution, not just an isolated helper return.

Taxi drop-off is locked when booked; tours return to the original pickup station. No automatic alternate/safety station is chosen after boarding. Missing permission or a destroyed destination retains the party with a blocked status. Walking recovery remains within that booked station. Existing passengers, stops, stock and unpaid balances are retained.

Four scoped native jump-discovery attribute changes honour the worker's declared galaxy-routing setting while keeping blacklists and other orders intact. This covers Morale and all thirteen shared roles. Crystal search uses persisted ore/silicon alternation instead of invalid time-remainder arithmetic. [Log evidence, all-role verification matrix, source provenance and live tests](LOG_REVIEW_0.3.6.md). New native integration remains unverified in X4.

Crystal sales now send an available existing crew member (or captain) to a real inventory trader's counter. Only the finite batch the merchant actually accepts is invoiced, and the same crew member must return aboard before the occupation departs. The merchant receives the items; custom sale credits use native average prices and observed balance changes. Missing rooms, counters or paths retain stock and report the blockage. Escort/patrol payments also retain rejected or partial balances for retry instead of marking them paid early. [Crew sale mechanics and live checks](CREW_CRYSTAL_SALES_0.3.6.md).

## 0.3.5: taxi and tour departure, completed fares

Both passenger services now release their booked roster templates before native walking while retaining the SAME real NPCs. Real station-room arrival and the whole party are checked before completion. Station transport points support dock/pier fallback; blocked visible paths get a bounded native-style room-transfer recovery after two minutes. Missing rooms/failed placement never count as delivery. Existing passengers and tour progress are retained.

Passenger fares now use observed-credit accounting: failed/partial payment preserves the unpaid balance, paid IDs follow full credit, and a completed booked fare survives faction/minimum-setting changes. Taxi remains 8,000 Cr per passenger; default luxury tour remains 500,000 Cr per passenger after the booked itinerary and sector coverage (twenty sites by default for new tours). Reputation stays restricted to eligible foreign factions with cooldowns. [Departure/payment mechanics, limits and live test steps](PASSENGER_COMPLETION_0.3.5.md).

## 0.3.4: taxi travel, escort discovery and persistent job recovery

The supplied debug(8) exposed a regression: the sector-yield optimization introduced 374,816 errors. It is removed. All 141 recorded sector-travel attempts also returned without arrival. Shared travel now disables the native sector shortcut, checks actual arrival and retries twice with a delay. Taxi/Tour/Hacker/Crystal sales queue a separate finite native docking order, preserving the persistent default and the same real passengers while it runs.

Escort and Morale now fall back to a throttled, bounded search over permitted galaxy sectors. Morale probes actual editable crew without requiring a commable pilot. Wrappers retain their assigned default across internal queue transitions and no longer self-edit recursively during version patches. Legacy critical defaults receive guarded recovery with exact settings and persistent state. Existing Holds remain player-controlled; reassign a role once if an older build already lost it.

The release also contains two exact optional compatibility expression fixes and small native station-loadout/stale-cue guards. Some third-party source files remain unavailable and their unrelated errors are explicitly unresolved. [Full findings, source provenance, limits and live tests](LOG_REVIEW_0.3.4.md). The new engine integration is unverified here; static green checks are not gameplay proof.

## 0.3.3: galaxy-wide crystal mining and automatic cash sales

Crystal miners no longer follow the player. Away from the player's sector and below visible attention they travel to real ore/silicon resource fields, work for a configured interval, and convert **actual native depleted yield** into a finite, saved crystal sale batch. Defaults are 24 items per five game minutes, consuming 100 ore/silicon units per item. This is the requested custom off-screen crystal simulation, not physical crystal firing in unloaded space.

They then travel to a reachable faction station and actually dock. When visible, an existing crew representative visits an actual inventory-trader counter. In 0.3.8 off-screen sales default to the finite-stock broker alternative and do not require instantiated interiors. Credits go directly to your account. Failed docking preserves stock; partial/rejected payment preserves only the unpaid remainder. Existing player crystals are not swept or sold. The real visible turret/drop path remains and puts collected items into the same automatic-sale stock. All normal armed S/M/L/XL ships are eligible; no mineral hold is needed. The Behaviour menu exposes simulation, batch time and batch size alongside galaxy range/risk.

Detailed mechanics, accounting, native references, limitations and live tests: [Crystal commerce review](CRYSTAL_COMMERCE_0.3.3.md). Actual engine integration remains unverified here.

The included 0.3.2 log repairs fix null sector-cache lists, conflicting hacker order attributes, passenger private-room/waypoint lookup and activity credit units. The supplied log confirms one 5,000,000 Cr tour and three 8,000 Cr patrol payments. [Exact log findings and other errors](LOG_REVIEW_0.3.2.md). Prior menu recovery is retained.

## Install and operate

1. Fully exit X4. Extract `Galactic_Occupations_0.4.1_DEV.zip` into the game installation directory, producing `extensions/vardath_galactic_occupations/content.xml`. Overwrite this extension in place. Keep Protected UI enabled and Inventory Collector installed.
2. Load the existing save. The implementation does not require a new game. Existing passengers, itineraries, equipment, crew, ownership and diagnostic history are retained. Reassign jobs that an older build already lost to Hold Position; intentional player orders are not overwritten.
3. Select a player ship with an AI captain, then select the occupation in Default Behaviour. Range **99 means the entire connected accessible galaxy**, 0 means the home sector, and 1–98 specifies a jump radius. Native travel blacklists still apply. Risk 0/1 avoids hostile territory; 2 permits it.
4. Inspect vanilla General Logbook for `Galactic Occupations: activity`, `completed` and `Vardath Payment`. Five-minute activity reports show observations, not paid completions. Debug lines `GO completed:` identify successful work; `GO payment:` includes promised/actual money and before/after balances; passenger settlement uses `GO passenger payment:` with contract IDs and unpaid balances.

## Behaviours

| Behaviour | Actual implemented work | Money and constraints |
|---|---|---|
| Galactic Escort Service | Follow a trader's actual station destination; require arrival, time and meaningful close-range protection. | Custom 12,000 Cr fee for a verified foreign-faction service, plus controlled reputation. Does not accept vanilla mission offers. |
| Galactic Taxi Service | Board up to ten actual NPC passengers according to free crew berths, travel to a station and disembark the accepted manifest. | 8,000 Cr per delivered passenger; no fare for reservations, approach or timer expiry. Native NPC movement near the player; verified real actor/roster handoffs away from the player, without requiring rendered interiors. |
| Station, Component and Signal Scanner | Survey real modules and public signal leaks across the galaxy. Timed off-screen equivalents publish actual native component information, station bonuses and real mission/contact discoveries. | Scanner-equipped S/M/L/XL; player scan cap; actual native signal slots for remote network surveys; 24-hour shared bonus cooldown. No scanner wage, invented market or auto-completed mission. |
| Wormhole and Anomaly Mapper | Survey real anomalies/gates/accelerators; catalogue actual destinations separately. | Optional safe transit fallback uses a permitted real anomaly exit and the same ship. No invented links or wage. |
| Galactic Sightseeing Tour | Board up to ten real passengers; visit twenty distinct global sights by default and normally at least three sectors; dwell, return and disembark. | Default 500,000 Cr per delivered luxury passenger for the fully booked itinerary. Fare requires the booked route and completed disembarkation. |
| Autonomous Crystal Miner | Real loaded deposit/turret harvesting; native-resource-backed custom mining off screen throughout the permitted galaxy. Saved batches travel to actual dockable faction stations; off-screen finite broker settlement or a visible same-crew inventory-counter visit and return. | All normal armed S/M/L/XL ships. Credits paid to player at native average inventory prices after finite broker settlement or verified counter presence and actual merchant acceptance; no mineral hold or following the player. Small completed-sale reputation with shared cooldown. New engine integration remains unverified. |
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

**The remote native API invocation and NPC paths have not been tested in X4 here.** In particular, whether the engine permits this player-attributed call away from the player and streams a usable NPC path must be checked in game. Missing geometry/API/effect yields waiting or failure with no invented hack/payment. Before deployment, unavailable interiors/panel paths time out after five minutes and return unused tools before another station is tried. Missing-tool waits are separate and retain their ten-minute recheck. Native NPC transit may be handled off screen by the engine; visible physical walking requires loaded interiors. Direct orders retain priority if the ship leaves a deployed actor ashore. Redocking permits normal walking return; after twenty game minutes away, the same crew member is recalled using its original native roster/post. No replacement captain or changed control post is created. The new emergency recall needs live confirmation; see RECOVERY_POLICY_0.4.0.md.

## One station, selected panel

Select an AI-controlled player ship on the map and right-click a faction station. **Hack station → actual panel name** adds a finite `Hack selected station panel` order to the existing queue. This additive native submenu lists the station's discovered panel types. It may first say it is checking panels. The existing default behaviour and earlier queued orders remain intact. It uses the same tools, physical actor, effect and return checks as the autonomous job. Choosing several ships does not bypass the station reservation; they wait for access and do not all charge an already-active panel.

## Crystal turret control and sales

Mine Crystals is a selectable addon option in Map → Information → Loadout → Turret Behaviour for existing player S/M/L/XL ships, including groups and missile turrets. Existing-ship outfitter controls also receive it. It is a controller layered on native turret control, not a new engine enum. Native selections and equipment remain intact; the standalone controller yields to the active crystal occupation. No custom mode ID is written into a build plan.

The visible path collects only real nearby crystal drops. Captain inventory removal is measured before stock is credited. If a native current-drop pickup credits player inventory, only its observed, drop-bounded increment can enter sale stock; pre-existing inventory remains yours. Off-screen simulation uses native finite field depletion and a saved virtual batch, with no crystal items/crates generated. Both paths automatically sell at dockable faction stations and pay cash. The [0.3.8 report](LOG_REVIEW_0.3.8.md) adds off-screen finite broker settlement and corrects the earlier [crew counter-sale path](CREW_CRYSTAL_SALES_0.3.6.md), which superseded the docking-only sale stage in the [resource/stock accounting report](CRYSTAL_COMMERCE_0.3.3.md); older crystal reports describe superseded inventory-delivery behaviour.

## Payments, reputation and the vanilla UI

Only verified sponsored services and actual sales can issue money; exploration, hacking and other unsponsored actions do not receive wages. Rewards use the native credit action and only the **observed positive player-balance change** enters the income history. A promised reward with zero balance change generates a warning. Taxi/tour fares, crystal invoices and verified escort/patrol fees retain unpaid balances for throttled retries; paid markers follow full credit. Duplicate assignment/passenger payment guards persist. Small eligible service reputation gains use a shared 30-minute faction cooldown; hacking grants none.

The vanilla transaction ledger remains the original renderer. There is no custom income screen, row injection, graph/table/search replacement or fabricated financial transaction. An optional published UIX callback adds descriptions to uniquely matched existing native payment records; without that callback the engine's ordinary descriptions remain. The shared MD consumer writes detailed paid receipts in vanilla General Logbook independently of UIX, including Builders payments. Item delivery is logged separately from credits.

## Compatibility and verification

Requires X4 9.00 or later; DLC content is discovered at runtime. No required dependencies on removed mods, no complete vanilla AI replacements (two narrowly scoped native AI attribute diffs are included), no ledger screen replacement and no change to Protected UI or Inventory Collector. Optional Sector Explorer/Auto Trade Subscriptions attribute patches and two small native MD guard patches and one additive leak-offer registration are included; see the current review. The six-mod bundle includes Auto Drones 1.02 and Cargo Teleport 1.01 with a bounded native docking retry for a failed undocked zero-transfer trade. Builders 1.75 and Yaki Habitats 1.23 remain unchanged. Kopis/Astrid 1.16 changes only braking state/transition guards and metadata/docs; Forge special weapon assets and Astrid equipment remain unchanged.

[Hacker/log review](HACKER_REVIEW_0.3.1.md), [reproducible in-game tests](TESTING.md), [implementation notes](IMPLEMENTATION.md) and [version history](CHANGELOG.md) distinguish source checks from unverified runtime stages. Keep a backup before testing this development build.
