# Version history

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
