# Galactic Occupations 0.4.6 — spacesuit control handoff and log review

## Evidence

Reviewed the complete supplied `debug(20261109-035808).log`: 1,542,561 bytes, 10,144 lines, SHA-256 `9c44ca8751897ac4c1dbf8b6577035dadd52c4a6f7ce02d404ce85afee72568d`. It identifies Occupations 0.45 / release 0.4.5.

At game age **19912.19**, the confirmed exit observer records source ship `0x7af77`, player room `0x7af7c`, controlled object null and spacesuit null. At **19925.32**, the old controller attempts its native emergency exit with the same incomplete handoff. The file ends at **19925.68**, only **0.36 game seconds later**, before its delayed two-second verification. Thus the log proves the observer and old recovery ran; it does **not** show whether that native call completed or identify the underlying engine/mod conflict. The user's loss of controls is the reported gameplay outcome. No error block explicitly names VGO or another Vardath suite script, but that is not proof of correct gameplay.

The prior implementation consumed its request before the native exit and had no return path if that call left the player in a partial transition. Source mocks previously assumed a successful native suit handoff and could not establish real engine behavior. This release changes the recovery protocol and preserves diagnostics rather than claiming to have reproduced the engine fault.

## Implemented correction

- Normal vanilla transporter confirmation/exit remains the original call. The existing observer and all UI files are unchanged. Recovery can only follow that explicit confirmation from a real, undocked source ship in the same sector.
- Give the native exit twelve game seconds first. If still incomplete, perform **one native teleport to the original ship with control=false, instant=true and force=true**, subject to the engine's `player.canforceteleportto` permission. This rebuilds the ship room context without explicitly taking the pilot seat or changing NPC control posts.
- Require **event_player_teleport_successful** for that actual source-ship room before making **one** native emergency spacesuit exit. Seeing the old room alone is insufficient. A failed/no-event reset expires without an exit.
- Poll actual player suit, player.controlled, player.entity.controlled, room context and native transit. Both no room and a suit's own cockpit room are acceptable; a remaining ship room is not. General logbook outcomes distinguish native suit handoff, original-ship return and blocked handoff.
- If the suit exit fails, make one bounded native return to the original ship. A stale first transfer is allowed thirty seconds before resetting; a stale suit-exit transfer receives a bounded wait before the return. No repeated eject/teleport loop is scheduled. Ship return alone is explicitly not verification of suit controls or first-person input.
- Reseating, controlling another object, changing ship/sector, moving to another room before recovery, leaving the source context, source destruction or docking cancel the request. Conversations defer action and expire under a fixed deadline. Save/load and the one-time upgrade clear pending exit intent; old saved recovery requests are never replayed. A new confirmed Use Spacesuit request is required after updating.
- Each native phase records before-call state and a command-return message. The native source-teleport event and subsequent verification are separately logged. If a command itself stalls, the last completed phase can be identified from the next debug log.

The implementation uses the actual 9.00 `teleport_player`, `teleport_player_to_spacesuit` and `event_player_teleport_successful` definitions in `libraries/common.xsd`, plus the declared player properties. Primary reference: ArtByunex/x4-foundation-artbyunex commit `e3e8a345e5624db118bff3eb171b60b0993fcc2c`. This is a pinned extracted native reference, **not** the user's merged installed catalogs. Emergency suit exit ignores the launch flag, so the redundant launch setting is removed. No ship position/equipment/crew/order mutation commands are introduced.

## Other error repaired

At **19271.46**, native `NPC_Instantiation.StartTrackingObject` reports indexing `this.$ServiceSlots.{1}`, followed by `add_actor_to_room` receiving a null slot. The source is actually its included **InstantiateNPCs** library: the combined generic/service-slot gate can admit a workforce iteration without a service slot, yet its non-casual branch selects one.

One exact attribute diff requires a nonempty service-slot list **before actor creation**. Its selector matches the pinned 9.00 source exactly once at line 1854, enclosing the reported line-1907 failure. The original reserve-one-space rule and every nonempty service-slot decision remain. As a conservative tradeoff, this workforce branch also skips possible casual recruits when all service slots are exhausted; native visitors, merchants and already-created NPCs remain unchanged. This avoids creating an orphan actor as a side effect of merely suppressing the later invalid placement. The new guard requires live population testing against the installed mod stack.

## Verified job payments in the supplied log

| Work | Completed receipts | Observed player credits |
|---|---:|---:|
| Finite-stock crystal sales | 26 | 1,700,000 Cr |
| Completed luxury tours | 2 | 9,000,000 Cr |
| Total | 28 | **10,700,000 Cr** |

Every recorded before/after difference matches the paid amount. Crystal sale ship/sequence pairs are unique. The two tour records explicitly state that ten passengers disembarked after twenty distinct sites across sixteen sectors, and eight disembarked after twenty sites across fourteen sectors. These were existing twenty-stop bookings; 0.4.5's ten-stop new-assignment default and extra hour remain intact. Three station/component/signal survey completions are also recorded; native scan publications can remain queued while the current player context has scan cap -1.

This is evidence for those particular payments and completions, not a runtime pass for every occupation. No new payment logic, passenger action, worker restart or pending-invoice reset is introduced in 0.4.6.

## Remaining log messages

The file contains **1,057 error-tag occurrences**, including repeated data loading and diagnostics deliberately logged with an error filter. Occurrence counts below are not distinct root-cause counts.

| Message family | Occurrences | Finding/action |
|---|---:|---|
| Invalid mission ID UI queries | 60 | Three stale mission IDs; no originating Lua file/stack. Do not invent a caller or replace the protected vanilla ledger/menu. |
| Missing/destroyed component UI queries | 10 | Follow the old suit recovery near the log end; caller omitted. Temporal coincidence is not proof that the suit controller or a particular UI mod owns the calls. |
| Native workforce invalid-slot errors | 2 | Narrow pre-creation guard implemented above. |
| Missing Koha engine loadout | 4 | No compatible engine candidate in merged faction equipment. This suite does not define Koha; complete installed macro/faction data is required for a correct equipment repair. |
| No suitable ShipGenerator | 16 | Includes loanshark plundererplunderer and fallensplit plunder requests. No ship catalogue/job definitions are fabricated. |
| Missing HQ-manager conversation actor | 2 | ResearchBlueprintsMod named by the log; its actual source is unavailable here. |
| Missing/nonunique diff selectors | 59 | Named external patch files include Gramston Ships (22), Trader Seminars (16), Pirate Chaos Conflict (6), NPC Economy Tweaks (5), No Ship Limits (2), Pilot Training (2), and six single occurrences. They require the relevant loaded mod versions/targets for a reliable patch. |
| Inventory-type resources on non-crafting wares | 280 | Repeated equipment/ware-definition warnings; not evidence of crystal sale duplication. |
| Construction plan warnings | 84 | Missing/incompatible saved plan components require the absent catalog context; no replacement modules or save edits are invented. |
| Unknown khaak production method | 14 | Ware/production data compatibility warning. |
| Partial save-header metadata parsing | 20 | Queries use maxsize=0x1000; these messages alone do not establish save corruption. |

There are also character/asset, duplicate-definition, text and startup blackboard messages. The old suite registry-before-init, explicit-null loadout wares and bare-faction subscription failures do not recur. Unsigned-file signature diagnostics do not identify a broken mod. Improved Spacesuit and Redneck Spacesuit Engine are loaded, but this file contains no exception assigning the exit failure to either; neither is disabled or altered. Inventory Collector and Protected UI remain supported.

## Validation

- **415 Python contracts** pass. Expanded actual-controller mocks reproduce the logged null-suit/null-control/ship-room boundary, require a real native reset event, reject a wrong-room/no-event response, handle refused reset/exit and stale transit, enforce bounded rollback and cancellation, preserve other ships/orders, and clear old saved intent. Five new population cases reproduce the empty-list failure and preserve all previously valid nonempty-slot choices.
- **91 Lua boundary mocks** pass against unchanged UI sources. Local execution uses the Lua 5.4 shared library with the existing unpack compatibility alias; GitHub checks use Lua 5.1 syntax/mocks.
- Native command/property metadata and ten exact selectors across six native diff files are checked against pinned 9.00 source; diff grammar and source/archive byte comparisons pass. Seven extension source/archive audits pass. Companion source files, Forge special weapon and all UI files are byte unchanged from 0.4.5.
- The installed-game schema/runtime checks are **not run**: no X4 executable, current save, merged installed catalogs or engine log reproduction environment is available. An attempted full pinned MD XSD compilation did not finish and was stopped; no full-schema pass is claimed. XML parsing, declared command signatures, native selector/diff grammar checks and mocked execution are separate checks.

## Existing-save acceptance

1. Exit X4 fully. Overwrite only `extensions/vardath_galactic_occupations/` using the 0.4.6 ZIP, retain Protected UI/Inventory Collector, then load the same save. Existing bookings, orders, crystal stock/invoices, equipment and crews remain. Any old pending suit request is cleared; confirm **Use Spacesuit** again for the new controller.
2. From an undocked ship, confirm a normal native exit. Verify the suit HUD, translation/rotation, weapon controls, oxygen and re-entry. The delayed controller must not reset an already healthy native exit.
3. Reproduce the reported stuck exit. After twelve game seconds, look for `GO spacesuit reset v46`, its command-return message and the actual `source teleport observed` event. About two game seconds after the reset, expect one `GO spacesuit exit v46`. Confirm the actual external suit and all controls, then native ship re-entry. A General logbook success requires the complete observed suit/control/room/transit condition; reading this message still does not replace testing input.
4. If a native transfer refuses/stalls, retain the complete debug log through at least sixty **unpaused game seconds**. There must be at most one source reset, one suit exit and one original-ship return. Inspect the final distinct verified/returned/blocked outcome. A returned-room outcome must not be reported as a verified suit exit. If the engine/render loop itself freezes, the final before/returned phase message helps locate the native boundary; script code cannot guarantee repair of a halted engine.
5. Before recovery acts, reseat, manually teleport to another ship, move rooms, or dock the source: no later forced exit. Test save/load and update with pending old intent, conversation, source loss, permission refusal, and the installed spacesuit mods. Retest Astrid Tours full-speed braking/re-entry; its source and Forge weapon were not changed.
6. Visit several busy stations and small platforms with few/no service slots. Confirm native merchants/visitors remain, recruitables appear where valid slots exist, and neither ServiceSlots.{1} nor null-slot add_actor_to_room recurs. Existing saved NPCs must remain.
7. Continue an existing crystal invoice and tour booking; verify the same party/stops/stock, actual native ledger payments and no duplicate credits. Newly assigned tours should still default to ten stops, retain the extra hour, and respect direct orders. All thirteen occupations remain present; this update does not restart their workers.

The new native recovery and population paths are **implemented, statically/mocked checked, and not yet verified in X4**.
