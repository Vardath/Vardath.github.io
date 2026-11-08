# Crystal crew-return repair — 0.3.9, 8 November 2026

## Evidence from the supplied log

Reviewed `debug(20261108-032505).log`: 1,765,348 bytes, 12,175 lines and 1,162 error records. Eleven error messages explicitly name Occupations: three imported `crystal.shop` call contexts blocked without a child script, five unguarded `$simulatesales` parameter-migration lookups, and three missing `$sold` reads after the imported calls. The previous merchant-NPC/object error does not recur.

The physical sale itself succeeded. Astrid Tours AKD-700 sent its existing crew member Marelle Kevlin AAS-369 to the actual trader. At game time 5653.99 the controller confirmed counter arrival. At 5664.02 the native account increased from 78,197,600 to 78,897,600 raw money: **7,000 Cr**, with zero remaining invoice. Later activity reports still show the crew in the at-counter phase, seven sold, zero stock and zero unpaid balance, with no crew-return or completed-assignment event. This matches the reported stranded NPC. Payment did not mean the visit had finished.

| Verified crystal sale | Credits |
|---|---:|
| CAT-914, invoice 1 | 65,000 |
| HNC-507, invoice 1 | 56,000 |
| QVT-051, invoice 1 | 51,000 |
| AKD-700, physical seven-item invoice 1 | 7,000 |
| CAT-914, invoice 2 | 33,000 |
| QVT-051, invoice 2 | 65,000 |
| HNC-507, invoice 2 | 60,000 |
| **Total observed crystal credits** | **337,000** |

Each amount has a matching observed native balance delta. Six off-screen sales complete, and the miners resume resource-field work and a second sale cycle. The log also records an 8,000 Cr patrol fee and a 12,000 Cr escort fee. These payments are evidence of those specific services, not certification of all occupations. No past payment is awarded again.

## Implemented repair

The sale previously left its return handoff to the caller of the settlement helper. The independent Mission Director crew controller did not reconcile a completed invoice if that handoff was lost. The log proves the saved paid-at-counter state; it does not establish exactly which native scheduling/interruption path lost the AI handoff.

1. A physical exchange records the exact active counter invoice. On full observed settlement it commits `shop_success`, the persistent `returning` phase and its timestamp before returning to the AI caller. It also registers the existing visit with the independent controller. Off-screen sales retain their existing no-crew path.
2. `ReconcilePaidVisitV39` independently matches the active invoice to the completed invoice, with zero unpaid money/remaining invoice units. It can start the return even if the caller result is lost, the AI worker is paused or a save/load interrupted the call chain. No native money or inventory action is used by this recovery.
3. A narrow legacy migration handles the exact old stranded state: deployed actor, physical counter mode, positive matching completed invoice, no remaining stock or unpaid units/money, and a nonempty departure manifest. A new visit records its invoice baseline so a previous visit's payment cannot satisfy it. This recovers the already-paid seven-item visit without a second payment, stock conversion or crew replacement.
4. A five-second registry repair reattaches pending saved visits from the existing active-ship registry, without a galaxy scan. The return remains independent of the ship AI stack. Status now says that the sale is paid and the same crew member is returning, with one return-request diagnostic.
5. Existing native return walking and its bounded recovery are retained. At the same actual dock, a walk that remains blocked for two game minutes may reconnect the **same existing actor** to the saved ship origin/native control-post location. Actual ship-room presence is required before completion and departure. Saved temporary/busy/Stay flags and the existing control post are restored. No NPC is cloned or crew template deleted.

A direct player order still takes priority. If it takes the ship away while the representative is ashore, the mod does not cancel the order or teleport the actor across space; redocking at that same station restores the return link. The repair can bring the representative back while the player is aboard or the AI occupation is paused, provided the ship remains docked there.

## Upgrade errors

All crystal order-parameter migration conditions now check for missing values and use optional reads. The sales toggle migration is applied at wrapper version 13 so a version-12 save with the missing field can be repaired; explicit false remains false.

New blocking calls inserted during the earlier version-3 shop/version-2 settle refactor now carry native `run_script sinceversion` metadata. Optional result reads and safe imported local defaults avoid the observed uninitialised `$sold` return. Shared worker version 18/runtime 39 uses the existing guarded restart/default recovery, preserving stock, paid invoices, passengers, equipment and player orders. The engine may report an already-broken imported stack before recovery actions run; this update does not rewrite saved AI serialization or claim every import warning can be retroactively suppressed.

The metadata and existing pinned native X4 9.00 scripts were inspected: [native source e3e8a345e5624db118bff3eb171b60b0993fcc2c](https://github.com/ArtByunex/x4-foundation-artbyunex/tree/e3e8a345e5624db118bff3eb171b60b0993fcc2c). `run_script/@sinceversion` identifies when a blocking action was introduced; the native script framework uses versioned patches, optional reads and guarded interrupt recovery. The fix uses those existing interfaces and the already-integrated same-actor native room movement; it adds no new UI or engine function.

## Other findings and limits

The remaining 1,151 error messages do not explicitly name Occupations. They include the previously reported ware/production/mod import problems, invalid old construction-plan references, missing ship generators, Kuertee null-object resolution and a restricted Mod Support APIs UI call. They are not all explained or fixed by this crew-return change. Third-party/effective installed source and the save are unavailable here; nothing was deleted to conceal those errors.

Astrid LMF-454 still reports tour boarding `0/2` while waiting for usable interiors. This log has no passenger boarding/departure/fare trace. That remains a reported gameplay limitation; this narrowly scoped crew-return release does not claim it has been resolved. Other roles without a complete observed work cycle also remain unverified. All thirteen behaviours and range 99's connected galaxy scope are retained.

Only Occupations source changes. Builders 1.75, Forge/Astrid 1.15 (including the special weapon), Habitats 1.23, Cargo Teleport 1.01 and Auto Drones 1.02 keep their published source hashes. Protected UI, Inventory Collector, the native ledger and General payment receipts remain unchanged. No new game or equipment/crew replacement is required by this implementation.

## Verification

255 Python contracts pass, including 13 new cases that execute the shipped XML: financial commit before caller resumption; lost-result fault injection; exact legacy paid-seven-item recovery without a reward; paused AI; unpaid/mismatched/old-visit rejection; partial merchant acceptance; saved blocked return with the same actor; manual undocking; registry recovery; safe parameter patches and blocker-version metadata. The existing 242 checks continue to pass. 78 Lua mocks, XML/API/reference validation, five native patch selector/grammar checks, seven package/source audits and bundle integrity checks are separate validations.

These native actions are mocked in the local tests. There is no X4 executable/save/full installed catalog here. The log now verifies physical and off-screen sale money, but **this new crew-return recovery is not yet live-tested**. A lost-result test demonstrates the recovery boundary; it does not prove that a lost return result caused the user's native stall.

## Live acceptance on the existing save

1. Exit X4 and overwrite `extensions/vardath_galactic_occupations` with 0.3.9. Keep Protected UI, Inventory Collector and the same save/mod load order. Do not remove the stranded crew member or restart the contract.
2. Load the save with AKD-700 still docked at its actual sale station. Unpause. The completed seven-item invoice should produce `GO crystal shop paid-return recovery` or an existing saved return, then `GO crystal shop return requested`. The same Marelle Kevlin should leave the desk and return aboard. If the native path remains blocked, allow two game minutes for the documented same-dock same-actor placement recovery.
3. Verify the same NPC is in a real ship room with its original crew role/control post and restored flags. Expect `GO crystal shop returned`. No second 7,000 Cr credit, extra crystals or new crew actor should appear. The occupation can then mark the existing visit complete and, under AI control, undock and seek work. Intentional player control/orders remain in charge.
4. Repeat a new visible sale with an ordinary service representative and a captain-only ship. Save/load at counter arrival, after money and during the return. Completion must wait for the same actor aboard, while cash/stock remains exactly once. Check native Transaction Log and General receipts against actual balances.
5. Give a direct order while at the desk, first keeping the ship at the dock, then leaving and redocking. The first allows return; the second preserves the ashore actor until the same link is restored. Never duplicate or silently erase the representative to permit departure.
