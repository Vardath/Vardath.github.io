# Taxi and tour departure/payment repair — 0.3.5 DEV

Updated 8 November 2026. This repair follows the reports that real taxi passengers remain aboard and no fare is paid, with a request to check tours too. Both services used the same departure path. No new post-0.3.4 log, installed X4 executable, current save or complete merged catalogs are available. The findings below come from the actual shipped code and native 9.00 references; new engine execution remains unverified.

## Corrections

| Area | Earlier implementation | 0.3.5 |
|---|---|---|
| Passenger attachment | Kept the ship's passenger roster template until after attempted station arrival. | Follow native passenger cleanup order: release only each booked passenger's template before departure movement. Keep the same persistent actor and manifest until real arrival. Existing captain/service/marine templates are not selected. |
| Visible departure | Retried generic slots with no bounded recovery for a live but stuck actor. | Prefer actual station transport waypoints, keep each chosen exit and original retry time, signal native walking, and after two minutes use the native-style failed-path room transfer for the SAME actor. No new NPC is created. |
| Dock/pier rooms | Required `dock.walkablemodule` before considering any exit. | Search real station transport/room points when a particular pier lacks that walkable module. If no real point exists, retain the manifest and withhold completion. This does not fabricate a station room. |
| Proof of departure | Could accept an old arrived flag and actor context without checking the actual room again. | Require the actor to exist in a real destination station room outside the ship, then observe a five-second station interval and successful removal of that passenger's template. Template release, a timer or a true placement result alone is not delivery. |
| Retrying a partial party | Boarding validation rejected an absent template even when it had been deliberately released during departure. | Allow already-boarded, explicitly released passengers to resume the same departure. Preserve per-person flags and original movement deadlines across retries; do not recruit a replacement passenger. |
| Tours | Same departure faults, plus generic fare handling. | Use the same corrected departure system only after the booked number of distinct sites and sector coverage. Ten stops remain the default; all actual passengers must leave. |
| Payment | Set paid IDs before confirming credits, then cleared the delivered contract even after zero credit or an unsuitable faction gate. | Dedicated passenger settlement tracks the booked fare and observed credits. Mark fully paid only when the entire amount arrives. Zero/partial credits preserve the unpaid remainder and retry after one game minute. |
| Fare source and settings | Required a current foreign friendly faction and minimum reward even after the journey was completed. | An accepted passenger contract owes its fare even if picked up at a player station, faction relations change, or minimum-reward settings change after booking. Faction reputation remains independently restricted and subject to the existing cooldown. |
| Repetition and statistics | A failed credit could still stop repeat-disabled work and count later settlement attempts repeatedly. | Repeat-disabled jobs wait for full settlement; completed-party statistics are recorded once per contract. Positive observed credits use the existing native transaction receipt and General Logbook paths. No custom ledger UI is added. |

The unchanged fares are **8,000 Cr per taxi passenger** and the **booked luxury ticket price, default 500,000 Cr per tour passenger**. A full ten-person default tour therefore earns 5,000,000 Cr after the itinerary and full departure. Walking/approach/boarding, partial tours and incomplete parties do not pay.

## Existing saves and preservation

Existing actor identities, passenger manifests, tour stops/sectors, contracts, captains, crew, equipment and ownership are retained. An updated active worker receives a guarded restart; released passengers need no fresh crew berth to finish leaving. An intentional player order still has priority. The update does not replace arbitrary Hold defaults: reselect a job only if an earlier build already changed it to Hold.

A passenger may disappear from the crew roster while their actual actor is still walking off. That is the native-style release step, not proof of delivery; the manifest retains the actor until the physical station check succeeds. Visible native walking is preferred. The two-minute blocked-path recovery repositions the same NPC to a genuine station point, as native failed-path handling does; this is explicitly a recovery alternative, not a claim of uninterrupted walking. Off-screen handoff uses the same genuine actor/room placement checks.

Already-lost historical fares cannot safely be reconstructed from an old paid marker or missing manifest. No speculative backpay is generated. Existing on-board parties and newly completed contracts use the repaired flow. Runtime logs showing a historical zero/partial credit would be needed to reconcile a previously cleared claim without risking duplicate payment.

Protected UI, Inventory Collector, all other occupations and the other four bundle extension sources remain. The Kopis special weapon/Astrid equipment are untouched. Earlier unrelated external-mod limitations remain listed in [the debug(8) report](LOG_REVIEW_0.3.4.md#remaining-errors-requiring-their-actual-installed-sources-or-more-evidence).

## Verification

All **152 Python contracts** and **78 Lua menu/native-bridge mock checks** pass locally. The 25 new passenger cases execute the shipped XML with mocked native room/roster/money operations, covering taxi and ten-person tour departure, incomplete itineraries, one passenger still aboard, false arrival flags, false native success without movement, failed releases/placement, missing rooms, pier fallback, disconnected actors, saved-state retry, zero/partial credits, duplicate guards, changed factions/minimums and repeat-disabled settlement. They do not run X4 or establish native walking, rendering, engine money changes or save/load execution.

XML syntax, action/parameter metadata, script references, archive CRC/extension layout and source/archive byte agreement are checked separately. All seven extension packages and the current five-extension bundle are audited. The new `clear_actor_roomslot` action is documented in the existing command reference at `common.xsd:33094`; no guessed command is used.

Primary inspected native 9.00 sources at pinned commit `e3e8a345e5624db118bff3eb171b60b0993fcc2c`:

- [GM_Transport_Passengers](https://github.com/ArtByunex/x4-foundation-artbyunex/blob/e3e8a345e5624db118bff3eb171b60b0993fcc2c/md/gm_transport_passengers.xml): `CleanUp` removes passenger templates before signalling their departure; station transport waypoints are used for exits.
- [NPC_State_Machines](https://github.com/ArtByunex/x4-foundation-artbyunex/blob/e3e8a345e5624db118bff3eb171b60b0993fcc2c/md/npc_state_machines.xml): `TRANSITION_move_to`, `MoveFailedHandling_ToSlot`, native room placement on failed paths.
- `scriptproperties.xml`: `component.room`, room/component context, `npctemplate`, role object and the meaning of `exists` (connection to the game graph). A disconnected cue actor is not automatically a new passenger.

## Reproducible live checks

1. Fully exit X4. Overwrite the existing extension with 0.3.5, restart and load the same save. Keep Protected UI and Inventory Collector. Look for the `Galactic Occupations 0.3.5 loaded` notice. Active jobs recover; reselect only a job already replaced by Hold.
2. Resume a taxi with existing passengers. Follow it to the real destination with an AI captain. Observe the SAME passengers leave, their crew roster entries clear, the activity count reach the full party, a `passengers delivered` notice and one `passenger fare paid` notice. Check actual player credits and the vanilla transaction ledger: 8,000 Cr times the delivered count. An NPC roster disappearance alone is insufficient.
3. Repeat for a tour with the existing route progress. No departure/fare before all booked sites and sector coverage. At the return/drop-off station every NPC must leave; a full ten-person default party earns exactly 5,000,000 Cr. Watch native walking at a loaded dock and the documented two-minute recovery if it stalls.
4. Test 1/10 passengers, an S/M dock and a large-ship pier where supported, and off-screen delivery. Deliberately block an interior or refuse a dock. No point/failed placement means no fake departure or fare; manifests and unpaid balances must remain for retry.
5. Save/load during walking, after one NPC leaves, after the party leaves and immediately after receiving money. There must be no NPC replacement, lost remaining party or duplicate fare. Issue a direct Move/Hold while leaving; it must take priority, and reassigning the original service must retain its state.
6. Test pickup at an owned station and a foreign station, and change minimum reward after boarding. A completed booked fare remains payable; reputation applies only to eligible foreign factions. With repeat disabled, the job must complete settlement before stopping. Zero/partial credit is tested here by mocks; if seen live, retain the logged before/after balances and contract ID.

Useful debug lines are `GO passenger departed:`, `GO passenger transfer:` (recovery/off-screen placement) and `GO passenger payment:` with contract, owed, actual, received and total amounts. General Logbook records group departure, pending fare and full payment. A fresh complete game log and ship ID are needed if native movement still stalls.
