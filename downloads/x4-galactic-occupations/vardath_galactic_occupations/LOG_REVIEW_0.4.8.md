# 0.4.8 — capital tours, Hyperion update and 150118 log review

## Evidence

`debug(20261109-150118).log`: **15,061,244 bytes / 75,369 lines**, SHA-256 `84f0a4fa7f1fa72ab3c85d61ad2afe059f11a0e0590f1ec14fb5b46e49699c80`. It runs Occupations **0.4.7**, Compatibility **1.0.0**, X4 **9.00**. There are 2,306 error-tag occurrences, including repeated metadata/data warnings and three successful Drone Auto-Stocker reports with `errors=0`. No exact fatal/exception/access-violation/out-of-memory/crash-dump marker is present. Unsigned-file diagnostics do not establish a crash cause.

The supplied file contains 418 crystal sale receipts (26,504,000 Cr), 198 tour receipts (967,500,000 Cr) and seven patrol receipts (56,000 Cr): **623 payments, 994,060,000 Cr**. Every recorded before/after balance difference equals the paid amount. Ship/invoice and ship/service/contract keys are unique. These support those recorded payments only; they do not verify all thirteen occupations. No worker wake-loop warning recurs in this recording.

## Capital sightseeing tours

The Behaviour order's class filter now includes S/M/L/XL, retaining owner/unit/ship exclusions. The existing station selector requires actual docking permission and a compatible dock/pier; no capital is sent to an incompatible small-only facility. Passenger count remains `min(10, available crew berths)` with native template creation refused when full. New bookings default to ten distinct stops and the existing multi-sector itinerary; already-accepted itineraries and fees persist.

Visible L/XL boarding/departure now uses a dedicated same-NPC handoff:

1. Resolve actual `npc_waypoint stand npctransport` points on the station and ship or their existing rooms. Native L/XL bridges and station corridors expose these points under transporter groups. No fabricated room, passenger cargo or replacement actor is used. Other docked ships' bridges are excluded from station endpoints.
2. Require the actual ship to be docked at the booked station. Walk the booked passenger to the source point, observe it within four metres and stopped, then allow a two-game-second transfer window.
3. Stop the walk and clear the passenger's old pose before a departure template is removed. Use documented `add_actor_to_room` to hand the **same actor** to the receiving transporter, then verify its actual room belongs to the correct ship or directly to the station. A native success result alone is insufficient. A failed/refused placement attempts rollback and retains the booking; it cannot earn a fare.
4. Boarding also requires the actual booked template and no native transit flag. Departure requires real template release, actual station arrival and the existing role/settling/all-passengers gates. Captains and ordinary crew cannot enter this passenger path. Arrival time is stored once, not restarted each poll; otherwise payment could wait indefinitely. Passengers move away from the receiving transporter where real room points are available.

This is a custom NPC handoff at real native transporter locations, using supported actor/room actions. It is not a claimed new engine-wide teleport mode or a player teleport command. Native uninstanced NPC/template handoff remains the off-screen alternative. Missing transporter/interior data remains waiting rather than falsely complete. Existing cancellation grace, interrupted journeys, crew recall, fare IDs, vanilla ledger and direct-order rules remain.

The 19 new contracts execute shipped control flow with native boundaries mocked, including ten actual-model passenger departures and a single earned payment, refusal, false success, missing points, undocking, saved retries, transit flags, wrong ship context and crew protection. They found and fixed a repeat-check arrival-clock reset during development. The existing 440 contracts and 91 Lua mocks also pass. They do **not** run the X4 engine.

## Scanner correction

At game age **31510.21**, the scanner's surface query fails on an inactive Swamp Plant Production module in Profit Center Alpha. `isphysicsready` describes loaded collision meshes; it was not sufficient to establish active physics. Scanner version 8 now requires visible attention, ready meshes and current player-sector context at every surface attempt and LOS sample, including after movement/yields. Low attention enters the existing timed remote-survey branch when enabled. Existing native scan acknowledgement, signal work, offers/discounts, cap checks and queued discovery publication remain. No raw “100% scanned” flag or free mission completion is introduced.

## Hyperion story and ship

The log confirms **More X3 Sectors – Reunion 0.33** (`ws_3835983248`, folder `fab_reunion_sectors`). Its actual author catalog was inspected with per-file checksum verification; the map changes links including `720To049` and `720To721`, adds intermediary sectors and links to sector 730. These can invalidate a story table cached before installation.

The separate **Hyperion Ascendant 1.0.0** extension uses native jump-path results and real active gates instead of trusting the old current-sector table. It can relocate a gate-free search sector to the next actual scan gate along that route and rebuild a stuck current scan stage in an existing save. Native scan requirements, earlier chapters, actors, counter and rewards remain; it does not complete the plot or create gates. If no valid scan route exists, it logs a bounded pending condition. The new file contains no fresh Hyperion stack; earlier cache errors, the actual map and the user's confirmed symptom informed the repair.

It also supplies a separate equipped Yaki-crewed Hyperion with custom stronger hull/shield/drive, six main batteries and eight beam turrets, maintaining one player-owned copy. The original Hyperion, Forge and Astrid definitions are untouched. See the ship's README for exact parameters, reference provenance and live checks.

## Other log fixes and limits

**Compatibility 1.0.1** fixes a native cleanup list being mutated by immediate callbacks (one new index error), Inventory Collector's missing common-handler debug local (23), HeadHunter's absent pilot/tracking cleanup (three) and a late Emergent Missions rescue-end signal (three). The original six guards remain. Their original error signatures do not recur in this recording. See that extension's `REVIEW_1.0.1.md` for source-matched versions and tests.

Unresolved data families include missing Koha engines (21), ShipGenerator candidates (62), external patch selectors (59), truncated save-header metadata reads (334), construction/ware/character data and stale UI requests without callers. HeadHunter's Lua import remains blocked by Protected UI; protection is preserved. Those are not silently hidden, replaced with arbitrary assets or blamed for a crash without a stack.

## Install and live acceptance

Exit X4 and extract the three-mod update into its game directory. It overwrites Occupations and Compatibility and adds Hyperion Ascendant. Enable the new extension; the logged installation already has its Hyperion Pack/Cradle of Humanity requirements. Keep Protected UI and Inventory Collector. No new game or mass worker reset. Save files containing custom Hyperion equipment need that extension to remain installed.

1. Assign Galactic Sightseeing Tour to an L ship and an XL ship with free berths. Confirm it appears in the vanilla Behaviour list and selects a faction station with a compatible pier. Observe from the station or another craft while the AI operates, following the existing player-occupied-ship pause policy.
2. Observe the actual passengers at station/ship transporter points. Confirm actual boarding before departure, up to ten passengers, and continued galaxy travel through ten real sights. For an existing twenty-stop booking, retain its accepted target instead of forcing it down mid-trip.
3. At the actual booked drop-off, observe the same passengers use the ship transporter and appear on the station. Read `GO capital passenger transporter:` diagnostics. Require all to leave and the native settling/role/template gates before the fare. Confirm one balance increase and corresponding vanilla ledger/logbook records, then another booking.
4. Save/load boarding, cruise and disembarkation. Interrupt with a direct order, combat or undocking; it must not count an incomplete transfer, create extra actors or pay. Cancel a booking and test existing grace/cleanup. Block a transporter/room in an isolated test copy and verify waiting/unpaid recovery.
5. Move away from a scanner's station or leave its sector between attempts. The inactive object must not receive a surface query. With simulation enabled, verify genuine timed remote work/scan acknowledgement; with it disabled, verify waiting/retry rather than fabricated scan credit.
6. Follow Hyperion Ascendant's README to test its actual spawned equipment/crew, single-copy replacement, native current-map quest guidance and save/load. A missing-route notice is not evidence of completed quest recovery.
7. Continue all other occupations and rerun their existing acceptance checklist in `TESTING.md`. Existing invoices, passengers, equipment, crew, ownership, turret modes and direct orders must persist.

All source/reference, mocked, XML and archive checks pass. **No X4 executable, user save or effective merged installed catalogs were available.** New transporter movement, native routing/recovery, actual ship creation/handling/weapon behavior and save/load remain live acceptance work. Static checks are not represented as in-game verification.
