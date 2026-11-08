# debug(10): crystals harvested, counter sale blocked — 0.3.7 DEV

Reviewed 8 November 2026. The supplied log is 7,452,958 bytes and 96,598 lines, with 28,388 error-tagged records. Most are initial import errors; 173 occur after the load-import interval. This report separates actual observations from source repairs and tests. No X4 executable/save is available here to confirm the new changes in game.

## Did the landed miner make progress?

The old immediate-undock problem is no longer the main blocker. The log records seventeen `GO service dock resumed:` entries, including CAT-914, QVT-051 and HNC-507 resuming the crystal occupation at real stations.

Those three miners repeatedly report **waiting for a real inventory trader**. Each retains its existing 24-item batch, has zero sold items and zero sale income. They time out preparation after about five game minutes and alternate between TEL Refined Goods Complex II and TEL Teladi Trading Station. Twelve old `GO crystal shop returned ... sold=0` messages are unsuccessful preparation/cleanup cycles; that message alone does **not** establish that a crew member left the ship. No crystal-sale payment trace occurs anywhere in this log.

There is also new, specific evidence that physical crystal work can progress on Astrid Tours AKD-700:

| Time | Actual log evidence |
|---|---|
| 4721.60 | Turquoise Sea X: 96 asteroid candidates, six crystal deposits found. |
| 4724.82 | Aguilite deposit selected; six turrets selected and 4,400 m forward laser range reported. |
| 4770.20 / 4888.04 | Bandannite deposits selected for physical firing. |
| 4915.65–4917.07 | Seven separate real drop pickups, each with native acknowledgement and the actual drop no longer existing. |
| 5107.58 / 5438.05 | Seven actual harvested items remain in sale stock, zero sold. The reported blockage is **no real walkable customer position at this counter**. |

This verifies the recorded deposits/weapon selection/pickup on that ship, not every weapon, turret arc, ship class or out-of-sector physical harvesting configuration. The source still checks observed inventory changes before crediting sale stock. The log proves no completed crew counter sale or sale cash.

## Repairs in this build

1. **First population request.** The old positive population gate compared an absent optional timestamp with current time. It now explicitly allows an absent timestamp, then throttles real native trader-population requests to once per station/minute. The previous mock supplied zero for a missing clock, masking this first-use case. Modelling missing clocks as null reproduces the old failure. A log without a population trace cannot establish whether every absence was caused by this gate or by unavailable station props/interiors.
2. **First payment attempt.** The counter payment gate had the same missing-clock assumption. A new visit removes the old payment timestamp, so the initial attempt must explicitly allow a missing value. Future retry times are still honoured. Actual counter/dock/crew/merchant stock acceptance and observed-credit checks remain required.
3. **Actual customer target.** The fallback asked `find_actor_interaction_point` about the entire station rather than the merchant the crew should approach. It now queries the actual trader and their real slot. The nearby-position search considers all free, unblocked NPC slots within four metres rather than only slots tagged `npc_generic`. No room, counter or position is invented. Native acceptance of the new merchant interaction query still requires a live test.
4. **Per-buyer backoff.** Every failed buyer has its own saved ten-minute cooldown. The old single last-failed marker let the nearest two unavailable stations alternate indefinitely. The current buyer and subsequent candidate search both honour the saved deadlines. Existing stock and earned unpaid invoices remain intact.
5. **Useful diagnostics.** Throttled population logs include real counter-slot and trader-candidate counts. Separate messages record the outbound movement request, actual verified counter state, successful return, and preparation ending without a visit. A failed preparation gets a General Logbook entry with the actual blockage. A movement request is not proof of physical arrival; only actual room/distance/dwell checks authorize sale.
6. **Expected destroyed deposit.** Four errors bind the crystal task's drop event to an already destroyed deposit. The supported event-source `check="false"` suppresses that expected missing-source error while retaining the exact deposit filter. The independent bounded real-drop query/collection remains, including the path that collected the seven recorded items. No global unfiltered drop subscription is added.
7. **Save upgrade.** Runtime recovery 37 reuses the established exact-default/state-preserving restart. It retains the sale registry, same actor, stock, unpaid invoices, passenger bookings and tour progress. Intentional Holds, player control and direct orders are preserved. It can recover applicable VGO workers after importing old stacks; it cannot retroactively prevent or repair unrelated engine import errors.
8. **Auto Drones 1.02.** The log reports a missing `$VAD_Stats.$errors` field immediately after loading. Its diagnostic uses an optional read. Drone supply, bridge behaviour, managers and existing station orders are unchanged. Its package workflow is deterministic to avoid timestamp-only archive commits.

## Other activity and remaining errors

The log records **23 successful arrivals out of 25 shared sector-travel attempts**; the two failed attempts concern The Moon. It also records a new Morale completion improving five crew values aboard an FRF Scavenger Manticore, and a verified foreign trade-route protection payment of **8,000 Cr** with matching observed native credit. These are actual new events, not saved activity totals.

No taxi/tour fare or new full passenger journey is established. Astrid LMF-454 remains at 0/2 boarded passengers because a usable dock/ship room point or actor connection is unavailable. Native NPC state machines also report invalid movement endpoints. Those interior/path failures are not declared fixed by the crystal-specific changes. The hacker is not assigned in the activity reports, so this log provides no native hack/crew-return verification.

The large initial import burst includes 13,033 string-value import errors and many invalid table/list values across saved script contexts, including non-VGO names. Four VGO workers report a blocked child call and one crystal helper reports an incompatible saved caller. The log does not identify a safe universal repair for the imported string/table failures. This update does not delete mission state, reset other mods or require a new game to conceal them.

Other unresolved records concern removed-extension construction plans, unsupported third-party recipes, a loanshark ship generator, native unloaded data-leak geometry, Mod Support API restricted `OnlineHasSession`, another collector's attempts to collect ammunition containers, VRO animation/missing mesh/sound assets, Kuertee object/cue lookups and bounded 4 KiB save-preview parsing. Signature-verification messages for unsigned extension files are not themselves proof that their scripts failed. No unsupported attribution or broad native replacement is made.

## Validation and provenance

All **211 Python contracts** and **78 Lua mocks** pass. Eight added cases cover first-use native-population replies with both clocks absent, actual-merchant interaction fallback, future population/payment deadlines, no real counter, independent failed buyers, candidate selection and the scoped missing-source flag. Existing control-flow/accounting cases retain finite goods, partial-credit claims, same-actor return and direct-order priority. The changed mock treatment of null clocks makes the two old first-use expressions fail before the fix. Mocks are not engine tests.

XML/API/reference, seven source/archive packages and the current six-extension bundle are checked separately. The existing five narrow native patch selectors/diff grammar remain checked against the pinned reference. The installed merged catalogs, runtime UI, NPC paths and full new sale loop remain unverified.

Primary sources inspected: native 9.00 [npc_instantiation.xml](https://github.com/ArtByunex/x4-foundation-artbyunex/blob/e3e8a345e5624db118bff3eb171b60b0993fcc2c/md/npc_instantiation.xml), [npc_itemtrader.xml](https://github.com/ArtByunex/x4-foundation-artbyunex/blob/e3e8a345e5624db118bff3eb171b60b0993fcc2c/md/npc_itemtrader.xml), [npc_state_machines.xml](https://github.com/ArtByunex/x4-foundation-artbyunex/blob/e3e8a345e5624db118bff3eb171b60b0993fcc2c/md/npc_state_machines.xml) and the native scriptproperties/command metadata. The event-source metadata documents `check`; interaction metadata documents the actual target object and slot-relative offset; NPC slot metadata documents occupied/blocked filtering. Calling the native population cue is a real request, not proof that a station has instantiated a usable trader corner.

## Live acceptance

1. Exit X4, overwrite Galactic Occupations with 0.3.7 and Auto Drones with 1.02, then restart the existing save. Keep Protected UI and Inventory Collector. Existing stock, passengers, equipment and crews must remain. Only roles previously lost to Hold need reselection.
2. Resume CAT-914/QVT-051/HNC-507 with their saved batches. Observe `GO service dock resumed:` followed by `GO crystal shop population:` or an already available real trader. Zero actual counter slots is a precise remaining interior/prop blockage; it must not create goods or cash. A failure should log its reason and try a different permitted buyer, respecting every saved cooldown.
3. At an actual trader counter, observe the same existing crew member leave, stop near the merchant and produce `GO crystal shop counter:` only after actual room/range/dwell checks. For AKD-700, retain and sell its seven harvested items rather than generating a new batch. Verify the actual merchant accepts a finite quantity, the saved stock decreases by exactly that quantity, native player credits increase and the vanilla ledger/General receipt matches.
4. Observe the same NPC return aboard before the occupation launches, then another mining/sale cycle. Save/load while walking out, at the counter, partly paid and while returning. No duplicate goods, cash or crew may appear. Test a direct player order; restoring a ship taken away while crew are ashore can require redocking that same ship.
5. Test two failed buyers, a station without a real counter, an unavailable merchant, a future retry deadline, no nearby generic-tagged slot, a stalled path and a destroyed deposit. Missing geometry/failed native operations must report failure and preserve the appropriate stock/claim. A blocked native path is still not permission to fake a sale.

To watch the captain run the ship, stand out of the pilot seat: native `player.occupiedship` is the ship whose pilot seat the player occupies, and the occupation yields to that control. The broader thirteen-role audit and previously documented constraints remain in [the 0.3.6 review](LOG_REVIEW_0.3.6.md); this log does not certify every role's full lifecycle.
