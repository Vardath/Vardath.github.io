# Version history

## 0.5.6 — 2026-11-14 — player-controlled EVA and boarding rescue

- Add two **manual** owned-ship interaction-menu entries: **Emergency EVA (outside hull)** and **Rescue: board this ship**. These are explicit requests, not automatic player movement.
- Safe EVA requires the player to be physically inside the target's room, the source ship to be player-owned and undocked, and no suit/conversation/native transit. X4 9.00 `teleport_player_to_spacesuit emergency=true instant=true allowinhighway=false` places the suit outside the ship bounding box.
- Recovery boarding requires an actual spacesuit, an owned destination ship within 2km and in the same sector, and no conversation/transit. The native `teleport_player object=target instant=true force=true control=false` requests its interior destination. The only time forced teleport is allowed is this explicit, bounded recovery.
- A single two-second delayed input-release request follows a manually initiated transition, not a periodic player-control override. Original `UserQuestionMenu.confirm`, transporters, airlocks, normal docking, and all saved v46 cue IDs remain untouched.
- Add translated text IDs 76–79 to all 13 native X4 language files and the English fallback: **64 entries** per locale.
- The supplied 2026-11-14 log does not record a definitive cause of the player control lock. It includes multiple installed spacesuit/teleport mods, 2,795 `Personal_Envoy_Full_Crew` missing `$PilotActor` errors, extensive missing Amaterasu assets and small-screen UI layout failures. Unavailable third-party code and missing ship meshes were not fabricated or patched.
- Preserve all 13 occupations, passenger/crew state, payments and ships. X4 runtime testing still required; see `SPACEWALK_AUDIT_2026-11-14.md`.



## 0.5.5 — 2026-11-14 — multilingual interface tables

- Add fully populated, language-ID-correct X4 XML localization tables for Russian (007), French (033), Spanish (034), Italian (039), Czech (042), Polish (048), German (049), Brazilian Portuguese (055), Japanese (081), Korean (082), Simplified Chinese (086) and Traditional Chinese (088).
- Maintain English (044) and the language-neutral `0001.xml` fallback. Each translated file contains the same 60 text entries, including 13 job names, 13 job descriptions, settings and hacking commands.
- Use lowercase filenames for Linux. Spanish Spain and Latin American language selection share the standard X4 Spanish ID 034. Do not fabricate unsupported language IDs.
- Add localization coverage contracts, package assertions, translation-contributor guidance and versioned distribution.
- AI-assisted first-pass translations should be reviewed by native speakers. The 60 static text entries are localized; some runtime-generated logbook/debug text and Lua strings remain in English.
- No ship AI, faction jobs, orders, passengers, mining, payments, crew, saves, or custom UI behaviour has changed. Same-save compatible; no X4 runtime/localized-client test conducted.


## 0.5.4 — 2026-11-13 — scanning, selective hacking and crystal-only fire

- **Station scanner:** publish each verified close-range module survey to the native map snapshot with `set_known updatesnapshot=true` and `set_object_scanned`. The player receives actual module identity independently of a deferred high-detail scan. No unvisited modules are revealed.
- **Optional EMP blueprint recovery:** scanner Behaviour gains a disabled-by-default toggle. Each eligible new blueprint costs one real `bomb_player_limpet_emp_01_mk1` from player inventory after a ten-second close-range sample and only when all native Player HQ research prerequisites are complete. Respect native `noplayerblueprint` and already-owned checks. This simulates the EMP/leak outcome without physically launching a bomb or faking data leaks; shipyard/wharf/equipment-dock blueprints remain restricted.
- **Selective station hacking:** autonomous hacker Behaviour gets a number-coded objective (0=random, 1=production, 2=turrets, 3=shields, 4=storage, 5=radar, 6=build modules, 7=watchdogs). Actual native panel catalogue filters the job; no substitute when a requested panel is absent. The existing one-time right-click menu still targets individual real panels.
- **Crystal turrets:** selecting Mine Crystals now snapshots the original native weapon mode, switches that turret to native hold fire to prevent its ordinary mining AI targeting asteroid bodies, and restores the exact original mode upon deactivation. Visible-attention script selects only `class.crystal` deposits, with increased 15 km/96-asteroid candidate search. Existing-save enabled modes are migrated when the controller runs.
- No protected UI replacement, crew/equipment/order reset, player teleport, or new game. Static validation cannot replace live X4 turret physics or blueprint-UI checks.


## 0.5.3 — 2026-11-13 — redocking and player-control safety

- Disable the v46 spacesuit "recovery" path which intercepted broad transporter confirmations and, after 12 seconds, issued a forced player-to-ship teleport followed by an emergency spacesuit ejection. This is unsafe around docking and interior transporters. The 2026-11-13 log proves that the two forced commands ran near the end of the session; it does not prove the precise floor collision.
- Retain every persistent MD cue/library identifier so old saved tasks remain loadable; a newly loaded pending request is cleared on the next poll and cannot issue movement. No normal X4 transporter, docking or spacesuit confirmation is overridden.
- Remove the UserQuestionMenu.confirm wrapper entirely. Galactic Occupations no longer tries to repair native spacesuit exits automatically.
- New MD and Lua regression contracts confirm no forced teleport/ejection commands remain, saved pending work is disarmed, and native menu confirmations are untouched.
- All 13 jobs, ships, trading, crew, passenger transfers and payments remain unchanged; no new game required.
- Additional independent warnings remain: repeated undersized-widget reports (615 height versus required 732), third-party XR Shippack collision mesh errors, noncrafting inventory ware definitions, and invalid mission ID queries. This release does not claim to repair them.


## 0.5.2 — 2026-11-13

- Remove a nonessential custom "Occupation:" row which hard-coded a 13-column span into X4's native Map/Ship Loadout information table. The latest new-game log reports invalid information-table cells and narrow-column/height failures; this is a precautionary source repair, not a confirmed cure for all UI failures.
- Keep the Mine Crystals turret dropdown, all native information rows, existing occupations, crew, orders and native transaction ledger intact.
- Lua regression contract checks that no extra status row is injected even when saved occupation state is present.
- No custom protected UI override, game-menu replacement or saved-state mutation. Requires live X4 verification.


## 0.5.1 — 2026-11-13

- Added universal English text fallback `t/0001.xml`, preserving English-specific strings in `t/0001-l044.xml`. Other language clients can show readable English instead of missing `ReadText191180` entries.
- Updated the outdated tour description from twenty to ten default sightseeing stops to match the current game-code setting. Existing itineraries are untouched.
- Added source-level localization checks and a detailed Nexus feature guide covering all thirteen jobs and manual station-panel hacking.
- No gameplay, worker, crew, save, payment or UI layout changes. Actual multi-language X4 runtime checks are pending.


## 0.5.0 — 2026-11-12

- Guard both shared native-income Lua adapters against incomplete save imports: reject nil receipt sequences, invalid row types and invalid bindings without writing any fictional transaction or cancelling the real payment event.
- Preserve the 0.4.9 stale-POI tour catalogue fix, native transaction ledger, orders, passengers, crew and saved task data.
- Add test cases for malformed save receipts and empty native binding tables. Static source/ZIP/Lua test suites only; live X4 validation still required.


## 0.4.8 — 2026-11-10

- L/XL sightseeing eligibility and real same-NPC transporter-point boarding/departure, preserving capacity, bookings and fare gates.
- Stable first station-arrival clock, rollback on refused transfer, exclusion of other docked ships and protection for ordinary crew/player actors.
- Station scanner visible-attention/geometry/sector guards before surface and LOS work; existing remote simulation retained.
- 459 Python contracts and unchanged Lua/vanilla UI integration; native execution requires live acceptance.


## 0.4.7 — 2026-11-09

- Added positive, versioned waits around the logged crystal worker fast-return chain and new-iteration boundary. Preserved runtime42 and saved work; no mass worker restart or payment changes.
- Hacker catalogue now inspects installed native security/infrastructure room macros for supported panel types, without creating rooms while browsing. Versioned partial caches refresh. Eligible dockable faction stations may provide a native dynamic office even before one is instantiated.
- After actual docking, prepare only the selected missing compatible native office with verified corridor/room definitions and fresh output references. Refresh actual rooms before panel probing. Track only extension-created interiors; retain active/player-occupied rooms, release unused persistence, and never force-remove an NPC-occupied room. Existing native offices are unchanged.
- Resolve real assigned/off-screen black-market NPCs and native registry mappings. Added accepted-leak, actual native discount-event and delayed visible-offer/contact diagnostics to the existing logbook/debug log. Real native delivery and unlock requirements remain; no fabricated traders or auto-accepted/completed missions.
- Added 25 source-executing fault-injection cases: 440 Python contracts and 91 unchanged Lua mocks pass. Supplied log verifies 66,010,000 Cr in 192 balance-matched receipts. Crash attribution remains unknown without a crash stack; native office/panel integration requires live testing. See LOG_REVIEW_0.4.7.md.

## 0.4.6 — 2026-11-09

- Replaced the consumed one-shot spacesuit retry with a bounded native original-ship context reset, real teleport-event acknowledgement, single emergency suit exit and polled suit/control/room/transit verification.
- Added one original-ship return if the suit handoff fails, including bounded stale-transit handling. No repeated exits, player-seat takeover, ship-order changes or unrequested recovery. Native commands log before/after state; changed context, permissions, conversation and expired intent are respected. Old saved requests are cleared on upgrade/load.
- Accept a suit's own cockpit room as healthy; do not confuse it with the old ship room. Verification, ship return and blocked transfer have distinct General logbook outcomes.
- Guarded native NPC_Instantiation.InstantiateNPCs workforce generation before actor creation when its service-slot list is empty. This prevents the two logged invalid-slot failures; native visitors, merchants and existing actors are untouched.
- Added/expanded failure boundaries: 415 Python contracts and 91 unchanged Lua mocks pass. Log proves 26 crystal sales and two tour fares paid 10,700,000 Cr; new native execution remains unverified. Other occupation AI, payment/passenger systems, UI and companion sources are unchanged. See LOG_REVIEW_0.4.6.md.

## 0.4.5 — 2026-11-09

- Newly assigned Tours default to ten stops; editable 10–20 range, valid saved settings and accepted bookings are preserved. Ticket-fee default remains 500,000 Cr per delivered passenger.
- Added one game hour to active booked-tour task and own native docking deadlines, tracked per absolute deadline so repeated polls/load do not pad it again. Other occupations/direct orders are excluded.
- Added one hour above cancelled-tour measured grace (minimum three hours), with one-time saved-pending-deadline migration. Already evacuated/disposing parties are not recreated; taxi and crew-return timers remain unchanged.
- Added thirteen timeout/default contracts; 400 Python and 91 Lua checks pass. Supplied manifest44 log records 28,993,000 Cr across 197 balance-matched payments and no explicitly named suite exception. New native integration requires live testing; see LOG_REVIEW_0.4.5.md.

## 0.4.4 — 2026-11-09

- Guarded the crew-recovery registry's presence before its count at cold startup, preserving existing registry/actor actions.
- Removed two faulty explicit-null loadout-wares overrides from station compatibility. Native list arguments and missing-faction equipment guards remain; no faction catalogue or equipment is fabricated.
- Extended optional exact-expression Auto Trade Subscriptions guards to the eighteen additional logged bare-faction checks. Existing corrected code is a no-op; eligibility, purchases, UI and completed cue state remain unchanged.
- Added nine boundary cases, including reproduction of the actual old null argument. 387 Python contracts and 91 Lua mocks pass. Native patch selectors decrease from eleven to nine because the two bad overrides are removed; five diff files remain.
- New log confirms a completed twenty-stop/15-sector ten-passenger luxury tour paid 5,000,000 Cr, plus 136 crystal sales paid 8,353,000 Cr. New corrections require live confirmation; all job AI/UI/payment/crew actions and companion sources stay unchanged.

## 0.4.3 — 2026-11-08

- Corrected the native scanner mission-request cue to its declared script-wide identifier and added a safe existence guard; missing/disabled native generation leaves other earned station benefits intact.
- Retained existing native faction/docking exclusions, sector cap, station cooldown and exact actual station/sector payload. No mission acceptance or reward simulation.
- Added a 44-identifier pinned native cue index, a validator for literal native MD references and eight dispatch/reference regression cases. 378 Python contracts and 91 Lua mocks pass; new native generation still requires live confirmation.
- Reviewed the full new log: 68 balance-matched payments total 4,137,000 Cr; the previous global movement lock is not reproduced. Companion and all AI/UI/payment/crew source files remain unchanged. See LOG_REVIEW_0.4.3.md.

## 0.4.2 — 2026-11-08

- Fixed the shared ashore-crystal-crew departure hold after takeoff/role changes; retained the actual current service's docked return wait and direct/player-order priority.
- Scoped background crystal/hacker status and timeout protection to the owning order, with a separate one-time background recovery notice. Preserved twenty-minute same-actor recall, original crew flags, bookings, stock and settled/unpaid invoices.
- Added runtime-42 import recovery without restarting a genuinely deployed current hacker operation. Returning captain recall defers during player transit/occupancy.
- Removed the missed worker capital/player-scan-cap gate. Scanner-equipped ships now sample independently of the player's on-foot cap and queue real samples for bounded native publication; signal benefits continue independently. No invented scan-level API or false full-scan flags.
- Added 22 mocked XML regression cases. 370 Python and 91 Lua checks pass; native execution remains unverified here. See CREW_ORDER_RECOVERY_0.4.2.md for exact supplied-log evidence and acceptance steps.

## 0.4.1 — guarded spacesuit recovery and logged role/braking fixes

- Observe only confirmed vanilla Use Spacesuit transporter requests. Allow twelve seconds for native completion; check real suit/control/room state, cancel changed contexts, expire native-transit waits and consume intent before one native emergency-form suit teleport. Log actual verification without claiming a camera repair from a successful call alone.
- Preserve vanilla confirmation and return values; add no menu, ledger replacement or automatic ejection loop. Isolate missing observer APIs and retain other addon call chains.
- Replace invalid `entityrole.pilot` with actual pilot identity, retain recruited crew/player and validate all native role literals. Preserve 0.4.0 lifecycle timers and delayed cleanup.
- Companion Kopis/Astrid 1.16 removes unsupported ship-blackboard braking state and excludes player/native/suit transitions. No Forge equipment or weapon-recovery changes.
- Extend scanner to timed off-screen component surveys and public signal-leak/network intelligence. Apply real station coupons/subscriptions with a shared 24-hour cooldown; expose actual native job offers, report real black-market contacts and offer normal native item-delivery unlock work. Preserve plot leaks and native acceptance/rewards. Add functional controls and scanner-equipped capital eligibility.
- Repair disconnected NPC identity checks, detach/role assignment order, same-sector unloaded interiors and two-minute visible boarding recovery without creating replacement passengers. Keep booked destinations, whole-party/tour completion and fare accounting.
- Supplied log confirms ten crystal sales (541,000 Cr), two escorts (24,000 Cr), two patrols (16,000 Cr) and a morale completion. Tour boarding remains blocked. 348 Python contracts and 91 Lua mocks pass; new native suit/survey/boarding recovery remains live-unverified. See SPACESUIT_RECOVERY_0.4.1.md and SURVEY_BOARDING_0.4.1.md.

## 0.4.0 — delayed recovery without cancelling temporary work

- Recall stranded crystal/hacker crew after twenty game minutes away, using the same native actor/template, original role/post and guarded room/post placement. Preserve manual transfers, player orders and hacker tool-loan accounting.
- Track real service cancellation separately from current orders. Retained default/current/queued service protects combat, lockboxes and manual control. Save taxi thirty-minute and tour minimum-two-hour unpaid grace; resume before expiry with the same party.
- Extend cancelled-tour grace using measured active cruise/history; default new tours to twenty stops while preserving accepted bookings and reading live settings for future ones.
- Remove immediate interruption cleanup; retain manifests in persistent registries, void expired contract IDs before native passenger removals, retry failures and preserve recruited crew. No cancellation payment/reputation or fabricated ledger transaction.
- Add 42 executed lifecycle/native-boundary/integration contracts. All 299 Python contracts and 78 Lua mocks pass, alongside XML/API/reference/patch/package checks. New X4 recalls/evacuations remain unverified; prior boarding limitations are not claimed fixed. See RECOVERY_POLICY_0.4.0.md.

## 0.3.9 — paid crystal crew return and imported-state recovery

- Commit the exact physical invoice and returning phase when native sale money is fully observed; do not rely solely on the settlement caller. Independently reconcile paid visits and the exact old seven-item stranded state without issuing money or replacing crew.
- Recover pending-visit registry membership, report return status and preserve same-actor native walking/blocked-path recovery, flags/control post, direct orders and actual ship-room departure gates.
- Guard missing order parameters, heal version-12 missing sales toggles at wrapper version 13, annotate earlier inserted blocking calls and suppress missing result reads. Retain guarded worker/default recovery at runtime 39 and all existing state.
- Add 13 executed recovery/import-boundary contracts; all 255 Python and 78 Lua checks pass. Latest log verifies seven crystal payments totalling 337,000 Cr, but no physical crew return or tour fare. New return recovery remains runtime-unverified. See LOG_REVIEW_0.3.9.md.

## 0.3.8 — galaxy service and unloaded-interior recovery

- Remove 0.3.7's invalid merchant-NPC object interaction call. Use actual free counter-room slots/waypoints and native-validated floor offsets; retain observed counter/dwell/merchant acceptance checks and same-crew return. Recover a stalled same-dock return using the same actor.
- Restore explicitly requested off-screen sales as a real configurable, finite-stock broker alternative at an actual permitted dock. Snapshot/recheck before conversion; preserve one shared invoice, unpaid money, stock, crew and cooldown-limited reputation. No imaginary NPC visit or free crystals.
- Transfer real named taxi/tour roster actors off screen without requiring loaded body geometry; observe template/role-object results and materialise the same actors when visible. Preserve booked destinations, capacity limit ten, full tour itinerary and whole-party departure before fares. Broaden actual room points and recover released bodyless passengers at their booked station.
- Upgrade workers/defaults to runtime 38 without dropping explicit false settings or creating state fields before their tables. Keep all companion sources, equipment, Protected UI, Inventory Collector and native ledger.
- Add 31 executed native-boundary/accounting/transfer tests; 242 Python contracts and 78 Lua mocks pass. The new log confirms two 8,000 Cr patrol payments, no crystal/passenger payment; new X4 execution remains unverified. See LOG_REVIEW_0.3.8.md.

## 0.3.7 — first-use crystal counter recovery

- Address debug(10)'s no-merchant/no-customer-position sale stalls. Allow absent initial population/payment times explicitly rather than comparing a null clock to current time. The previous mocks incorrectly substituted zero for both absent values.
- Query all free nearby room slots and calculate the interaction point at the actual merchant rather than the whole station. Keep actual counter/actor/dock/stock/payment guards.
- Save independent ten-minute failed-buyer cooldowns instead of alternating the last two unavailable buyers. Add throttled population counts, movement-request/counter diagnostics and honest preparation-failure logs.
- Keep the drop listener scoped to the exact deposit but permit expected destruction via the supported event-source check flag. Retain state-preserving worker recovery for imported old stacks.
- Add eight relevant checks, including native population response with both clocks missing, merchant fallback, retry gates and multi-buyer recovery. All 211 Python contracts and 78 Lua mocks pass. No full in-game sale is asserted; debug10 proves seven real pickups, a morale improvement and one patrol payment. See LOG_REVIEW_0.3.7.md.

## 0.3.6 — native landing-loop and shared routing recovery

- Fix the demonstrated native DockAt-to-Undock boundary with one scoped attribute guard and a bounded saved service handoff. Keep own taxi/tour/crystal/hacker work at its actual service dock; clear before explicit departure. Other orders retain native handling.
- Lock taxi drop-off and tour pickup return stations after booking. Remove automatic passenger diversion, retain blocked parties and enforce the booked destination during actual departure. Initialise a missing legacy departure clock without resetting person-level deadlines.
- Honour the declared native known-path parameter in four jump-discovery attributes only for the tracked VGO worker. Cover all thirteen roles and remote Morale movement while retaining blacklists/range/risk.
- Replace invalid time remainder in crystal field search with persistent boolean alternation. Keep actual finite depletion, stock and observed sale accounting.
- Add a physical existing-crew crystal-sale visit: real native trading corner, actual merchant inventory acceptance, finite manifest/invoice, same-actor return and restored crew flags. No replacement crew or fictional shop. Preserve partial cash claims and native ledger receipts.
- Retry unpaid verified escort/patrol invoices without setting an early paid marker; retry existing claims before new work or repeat-off standby.
- Add 23 retail state/accounting and 9 service-invoice cases alongside 19 native-boundary/destination/route cases. All 203 Python contracts and 78 Lua mocks pass; five native selector matches/diff grammar checked. Log9 records 72 simulated items but no sale/passenger payment. New in-game execution remains unverified; see LOG_REVIEW_0.3.6.md.

## 0.3.5 — taxi/tour departure and booked fare settlement

- Release only booked passenger templates before native movement; retain the same actors until observed station-room departure. Prefer transport waypoints, allow real station points at non-walkable piers and recover blocked visible paths after two minutes using native-style same-actor placement. No timer/native-success-only completion.
- Preserve released passengers, per-person flags and movement deadlines through retries. Require complete tour itinerary and full party departure; keep existing NPCs, crews and stops.
- Add dedicated passenger fare accounting: actual-credit receipts, persisted unpaid remainder, one-minute retry, paid IDs only after full settlement, one completion record per contract, repeat-disabled settlement and independent controlled reputation. Accepted fares survive player-station pickup and relation/minimum-setting changes. No guessed backpay.
- Add 25 executed passenger control/accounting cases. All 152 Python contracts and 78 Lua mocks pass locally; new X4 execution remains unverified. Preserve native ledger UI and Protected UI. See PASSENGER_COMPLETION_0.3.5.md.

## 0.3.4 — debug(8) travel and job-start recovery

- Remove the invalid sector-yield property responsible for 374,816 errors. Verify actual arrival through a bounded shared travel helper with the native premature sector shortcut disabled.
- Replace borrowed native docking scripts with separate finite DockAt orders. Preserve manifests/defaults, handle new player orders, retain failed work and recover legacy critical defaults with exact declared settings.
- Retry persistent wrappers against their default identity, remove recursive migration self-edits, repair present-null new settings and log startup/end transitions. Existing player Holds remain untouched.
- Add bounded, throttled galaxy search for escort/patrol/morale candidates; use real trade destinations and editable morale data, retaining effect/payment/reputation checks.
- Add exact optional Sector Explorer and Auto Trade Subscriptions expression patches; guard missing native station equipment entries with native faction defaults and expired invincibility requester cues.
- Add 21 source/executed recovery tests and native diff grammar/reference checks. Log confirms 52,000 Cr prior escort/patrol income and eight morale completions; new runtime integration remains unverified. Other external errors/source requirements are listed explicitly.

## 0.3.3 — user-requested off-screen crystal commerce

- Replace player-following fallback with real resource-field navigation, bounded active mining time and native yield depletion; finite custom crystal conversion is capped by actual ore/silicon removed. All normal armed sizes; no mineral hold.
- Persist per-family stock and automatically simulate inventory-trader sales only at a real permitted faction station after docking. Native average prices; native cash directly to player. Correct `script_add` receipt matching, no duplicate completion wage.
- Track sale IDs and unpaid claims before receipt callbacks; retain failed/partial payments and failed docking. A fully paid foreign sale grants small trade reputation with the shared cooldown. No approach rewards or existing player-inventory sweep.
- Keep real visible crystal targeting/turret/drop collection and redirect actual observed harvests into sale stock. Preserve normal modes, Inventory Collector, Protected UI, existing saves and other job state.
- Expose simulation, batch duration and size in native Behaviour settings; migrate old workers/defaults safely. Add 21 executed XML accounting/source contracts and full live reproduction steps. Engine integration remains unverified here.

## 0.3.2 — debug(7) shared-worker recovery

- Guard missing and present-null sector caches at startup, saved-label resumes and refill; clone a valid cache. Log actual native travel results and reached sectors.
- Remove conflicting default/immediate hacker order attributes; enforce the actual game constraint during validation/audit.
- Query private passenger rooms and native transport waypoints for boarding, exits and rollback, caching only within the MD batch. Keep real actor/context/capacity checks. Report scanner prerequisites before searching.
- Correct activity money units to Cr. The supplied log verifies a 5,000,000 Cr luxury tour and three 8,000 Cr patrol payments; none is re-awarded.
- Companion Cargo Teleport 1.01 adds one bounded normal docking retry when undocked native execution fails with zero goods moved. No synthetic cargo or payment. Detailed remaining errors and runtime limits are recorded.

## 0.3.1 development — open-menu replies and actual crystal recovery

- Fix the confirmed stale Checking submenu: rebuild only custom actions before native draw, poll for missed replies, normalize MD numeric booleans/IDs and revalidate station/ship selection. Replace the old unrealistic prepare-after-reply mock with draw-only update tests.
- Add paused-safe ten-second UI timeout, explicit retry, empty/unavailable replies and short caching/refresh of unloaded station interiors. Native script requests still need unpaused gameplay.
- Add configurable active-simulation navigation for crystal mining rather than silently cycling through unsupported out-of-sector firing. Recover genuine loose crystal drops independently of the task event. Retry native pickup through an owned player-occupied ship only if NPC collection leaves the actual drop untouched; wait for native results and retain failures.
- Add search/damage/pickup/delivery diagnostics and native direct-delivery log receipts. No deposit/drop generation, manual crate deletion, fake inventory, cash wage or simulated out-of-sector damage. Actual harvesting/delivery remains runtime-unverified pending the next live log.
- Keep galaxy range, player orders, existing saves/passengers/crew, Protected UI, Inventory Collector, original ledger and other mod sources.

## 0.3.0 development — physical crew hacking and verified patrol payments

- Add galaxy-wide Galactic Station Hacker and queued station/panel context command using native actual panel discovery and costs. Existing crew/captain walk to the panel and back; completion requires the real native effect and actual return. No actor cloning, ashore teleport or whole-station hack flag.
- Loan actual player inventory tools remotely with measured transfers/rollback; retain failed returns, serialize native consumption and retry missing tools every ten game minutes. Persist actor/token/phase across saves and recover interruptions without replacing player orders.
- Use the native player-attributed StartControlPanelHack API after NPC arrival; remote invocation and native NPC transit remain explicitly runtime-unverified.
- Fix the log-proven zero patrol fee: future verified foreign-trader arrivals pay 8,000 Cr; own traders remain unpaid. Add promised/actual/before/after payment tracing and retain shared General paid receipts plus the original ledger.
- Keep all-size crystal/player-inventory fixes, existing passengers, Protected UI and all other mod sources. Add native order-type validation, 19 hacker accounting/source tests and 30 UI bridge/menu mocks; document unverified in-game cases and other log errors.

## 0.2.5 development — all-size crystal weapons and player inventory

- Remove beam-only/S/M restrictions for crystal mining; allow forward weapons, ordinary and missile turrets, and L/XL Loadout controls. Keep normal turret mode IDs and equipment unchanged.
- Use native per-asteroid component searches, weapon-range/hull-clearance approaches and four actual alignment orientations. Prevent competing occupation/standalone controllers. Release temporary region persistence after interruption/cleanup.
- Collect only actual attributed drops with native short-range pickup, then accountably forward existing crystal quantities to player inventory. Verify source removal and player credit; restore uncredited remainder. No cargo requirement, automatic sale, captain holding limit or free crystals.
- Retain and retry actual pending drops across task restarts. Legacy sale callers forward existing items instead. Add unique ship ID codes and item-delivery diagnostics without financial ledger fabrication.
- Add eight accounting checks and extend source/Lua contracts for the actual failures. New physical/inventory effects remain unverified in X4. Other mod sources, Forge/Astrid equipment, passengers and Protected UI are preserved.

## 0.2.4 development — job activity and transient target recovery

- Repair debug(5) failures: wait for and capture a real target sector; do not pass null sectors to native movement. Defer searches while the occupation ship itself is in transit.
- Reject missing-sector and non-operational live-service candidates before territory/capture/pilot properties. Revalidate recruitment after the communication delay; refresh the tour catalogue without resetting current passengers or itinerary.
- Add per-ship/per-job observational counters and roughly five-minute activity reports to vanilla General Logbook and the debug log. Completed assignments get actual-effect details; incomplete stages and tour sights do not become successful contracts. No reporting code creates rewards.
- Preserve scanner geometry wait reasons and stop checking an entire unloaded station. Explain missing damage, unconfirmed crystal collection, full morale, refused surrender and failed pursuit. Use a real destruction event/zero hull for demolition success.
- Native financial ledger and payment receipts, UI Protection, existing saves and all other mod sources remain unchanged. Full 0.2.4 gameplay acceptance remains unverified.

## 0.2.3 development — tour, taxi, neutral escort and drop-off

- Explicit native undocking before direct travel/proximity completion, with native skipwait handling; boarding hands tours immediately to a real sightseeing target.
- Taxi same-sector departure; shared actual-actor disembarkation for taxi/tour, with a full-manifest completion gate. Removed timer-only off-screen delivery. Visible actors walk off; off-screen transfers must actually connect the same actor to a real destination room or remain unpaid.
- Persistent neutral/player-trader convoy escort/patrol replaces the unsafe same-faction fleet escort call. Defensive combat uses a separate native override order, with bounded cleanup and route resumption.
- Correct boolean cargo illegality. Recheck recruitment ownership before commander/order changes, preserve float probability factors, require a front laser for lure provocation, and use the actual asteroid persistence target.
- New namespaced order-icon aliases reference native textures; no screen replacement or change to Protected UI.
- Yaki Habitats 1.23 directly dereferences construction-plan macros and fails closed on unreadable plans. Existing modules, Forge equipment and other mods are preserved.
- Boarding success is user-observed in 0.2.2. These repaired gameplay stages are still runtime-unverified; full per-job review and reproducible tests included.

## 0.2.2 development — failures from debug(3).log

- Safe non-null order-location fallback for all twelve behaviours, including Crystal Miner; explicit retry after an unexpected worker return.
- Native version patches/default-order recovery, missing scope/loop initialization and preserved direct-order priority. Existing Hold commands are not overwritten.
- Removed the rejected `@... ?` expression; guarded legacy passenger template arguments, missing turret registries and ownerless police jurisdictions. Staggered finder calls to avoid immediate-return wake loops.
- Native unlimited sector search omits maxdistance, as documented.
- Independent shared-cursor MD receipts for actual paid journal records; recover the latest twenty once without transferring money. General Logbook now distinguishes active orders, missing crystal equipment, actual work completion and paid receipts.
- Crystal turret preflight reports waiting and retains the behaviour. Harvesting, hits and collection remain runtime-unverified.
- Companion fixes: Builders 1.75 receipt consumer; Kopis 1.15 Astrid equipment-use/licence fields only; Yaki Habitats 1.22 indexes constructionsequence entries instead of invalid foreach, preventing mistaken missing-habitat decisions. No station/module deletion or Forge gun changes.
- No crash-cause assertion: the supplied log ends during asset loading without a fatal stack/dump.

## 0.2.1 development — native transaction screen repair

- Removed the preview income panel and all transaction renderer/table/graph/search/paging overrides from both Occupations and Builders. The supplied log confirmed the 0.2.0 frame/menu mismatch crashed the native transaction screen.
- Added descriptions only to unambiguous existing native payment IDs through the optional published UIX callback; no extra financial rows or duplicated income. Preserved shared payment history and lifetime counters, with detailed receipts in the native Logbook.
- Kept Protected UI Mode; no replacement game UI files, arbitrary extension-module imports or forced support-mod dependency.
- Fixed the log's unsupported ship/component blackboard writes by moving state to the real player entity's persistent per-object tables; added a compact UI state export.
- Scoped crystal drop events to the task's actual deposit and room events to the live passenger group. Fixed the migration cue's missing polling interval.
- Moved `shoot_at` into visible-attention blocks, with a non-simulating low-attention return, and removed an ineffective unsorted deposit limit.
- Added native default-order recovery for registered occupations, leaving direct orders and their queue priority intact.
- Builders 1.74 retains rates/SETA/debt accounting and removes the old income UI. Kopis 1.14 guards Astrid braking when the player is not aboard a ship; Forge weapon assets/recovery are preserved.
- Validated source, packages and mock data/UI contracts. In-game retesting remains pending.

## 0.2.0 development — 7 November 2026

- Made range 99 explicitly unlimited over the native connected accessible sector graph, rotated sectors after assignments and added a global, deduplicated tour catalogue.
- Replaced two-second template-only taxi pickup with up to ten actual NPCs, native dock walking, capacity reservations, physical per-actor boarding acknowledgments and persistent batch/contract IDs.
- Turned sightseeing into a passenger luxury service: ten distinct sites, at least three sectors where available, then drop-off. Default 500,000 Cr per passenger, configurable.
- Added Mine Crystals to existing S/M Loadout/outfitter dropdowns as a virtual mode with per-turret flags and a standalone controller. Preserved native mode callbacks and equipment. Runtime aim/menu verification remains pending.
- Removed the scanner level-equality rejection, added actual surface positioning, three viewing angles, ten-second LOS surveys, defence elements and observed progress diagnostics.
- Integrated verified payment labels/receipts into the existing vanilla transaction list, retaining the income preview.
- Added shared payment descriptions, individual entries, job filters and lifetime totals inside the main Transaction Log, including builder hire/active/standby/final payments.
- Added 16 source guards and 36 executable mocked UI checks. Existing saves are supported by scoped migration; full X4 runtime testing remains unavailable.

## 0.1.0 development — 6 November 2026

- Added twelve native infinite ship-order definitions and twelve task implementations.
- Added shared sector search, navigation, target leases, timeouts, completion ledger and status reporting.
- Added custom escort and passenger service contracts, crew morale support and conservative emergency recruitment.
- Added station module surveys, anomaly catalogue/traversal alternative, sightseeing itinerary, cargo inspection and traffic-following patrols.
- Added a scoped Mine Crystals direct turret controller, native real-drop collection, inventory limits and accounted broker sales.
- Added deterministic extension ZIP packaging, command/reference validation, a dedicated static GitHub workflow and per-occupation runtime test instructions.
- No existing mod files changed. All gameplay/runtime acceptance tests remain pending; this version is not a stable release.

Reputation update: completed escort/taxi services, actual morale improvements, verified trade-route escort arrivals and genuine contraband reports can award a small faction increase. Completed accounted crystal broker sales use a smaller trade increase. The shared 30-minute faction cooldown prevents stacking; discovery, sightseeing, demolition and captures do not grant reputation by proximity.
