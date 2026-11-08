# Version history

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
