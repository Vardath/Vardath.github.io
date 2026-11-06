# Version history

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
