# Crew recall and cancelled passenger bookings — 0.4.0

This update implements the requested recovery policy. No new game log was supplied for this change, and it has not been run in X4 here. The previous log's observed 337,000 Cr of crystal sales remains evidence for those earlier payments, not for these new timers or native recalls.

## Rules

| Situation | Behaviour |
|---|---|
| Crystal salesperson or hacker left ashore when the ship departs | Recall the same original crew NPC after about **20 game minutes** away from that station. |
| Taxi service genuinely cancelled with booked NPCs still aboard | Allow **30 game minutes**, then evacuate the cancelled passengers **unpaid**. |
| Sightseeing tour genuinely cancelled with booked NPCs still aboard | Allow **at least two game hours**, longer when measured cruise duration warrants it, then evacuate **unpaid**. |
| Combat, a lockbox, docking, a manual order, or player control while the original default/queued service is retained | Keep the same passengers, itinerary and booked destination. No cancellation timer or evacuation. |
| Original service resumed before the cancellation deadline | Clear the timer and continue with the same party and itinerary. |
| A removal fails after the deadline | Keep the booking void, retry the remaining native removals, and block new boarding/payment until cleanup completes. |
| A booked passenger has deliberately become service crew, a marine or a captain | Preserve that NPC and native crew entry; remove only its obsolete booking. |

Every interval uses `player.age`, so pause stops it and SETA advances it with game time. The controller checks every 30 game seconds; observable expiry/recall may follow a boundary by roughly one check interval. Old stranded visits without an away timestamp start their twenty-minute clock when first observed by this update.

## What counts as cancellation

The accepted manifest's stored service type is authoritative. The controller looks for that exact taxi/tour ID in the ship's default behaviour, current order and remaining native order queue. It does **not** treat a different current order or player control as cancellation. This preserves bookings through ordinary combat, lockbox collection and other overrides. Pausing the service by flying the ship yourself is also safe while its default or queued service remains.

Remove/change the persistent service and leave no current/queued instance to cancel the booking. Grace begins when that absence is first observed. A brief script restart or rapid change/reselection cannot instantly delete passengers: reselecting the service clears the pending timer before expiry. A cancellation notice is delayed until the absence has lasted one minute to avoid noisy transient notices. An already-expired partly evacuated party stays void if the service is reselected; a new booking starts only after its remaining cleanup.

Changing Taxi to Tour cannot silently convert the old taxi party into luxury passengers, or disembark it through the other service's transfer cue. After the old party leaves, a new service can book normally. Completed, already-earned fares with no live manifest are retained for settlement; this policy does not erase legitimate unpaid invoices.

## Twenty-stop tours and adaptive grace

New tours default to **20 distinct stops**. The prior default value of 10 is migrated to 20 for future bookings. Existing accepted routes retain their stored stop count, ticket price and original return station; the update does not double an already-booked itinerary. The existing 10–20 setting remains available, and explicit future changes are read from the live order parameter at booking.

There is no single honest duration for a twenty-stop galactic cruise: ship speed, gate distances, route, docks and interruptions vary. The controller therefore uses a two-game-hour minimum and extends it using:

- The last actually completed cruise duration, scaled to the current booked stop count.
- The current trip's measured active time per visited stop, projected over its booked stops, plus a thirty-minute allowance for returning to port.

The larger value is saved when cancellation is detected; repeated checks do not keep moving its deadline. A tour with no visited stops cannot turn an idle/blocked wait into an enormous projected cruise. A ship with no usable history uses the two-hour minimum.

Active work is sampled while the owned tracked tour/default or its own finite dock order runs, with passengers aboard. Combat, lockbox overrides and player control are excluded. A long gap between checks contributes at most one minute rather than inventing hours of observed work. Legacy cruises with prior stops may initialise conservatively from their saved embarkation age; new bookings start fresh clocks. A completed cruise updates history only after the full booked itinerary and passenger departure, not for a cancellation or an individual stop. These are implemented estimates; no new in-game twenty-stop duration was measured in this environment.

## Stranded crew recall

The crystal and hacker paths share the native recall helper. The twenty-minute away timer is separate from job interruption/cancellation and starts only while the existing deployed actor is away from its ship and the ship is no longer docked at the deployment station. Redocking cancels that away timer and allows normal return walking. Staying away, crossing sectors, changing jobs or taking player control does not restart it.

Before recall the helper checks the **same actor's native `npctemplate`** against the original ship's actual people list, its role-object assignment, and absence of a native scheduled crew transfer. It will not steal a crew member who was deliberately assigned elsewhere, replace a dead actor, create a new actor/template or rewrite crew ownership, role or control post.

At expiry it stops the old walk, tries the original valid ship room point, then uses native `add_actor_to_post_location` as needed. The original crew role, post and native roster must still match afterwards. A visible return requires actual ship-room presence. If the ship interior is uninstantiated away from the player, the existing native roster/post assignment plus absence of an ashore body can confirm the abstract return. This is the requested teleport-style emergency recall, not a claim that an NPC physically walked across sectors. No script manually destroys/uninstances the permanent crew actor to achieve it.

The original crystal/hacker return controller then restores its saved flags, checks actual/native return and finishes the visit. Hacker tool loans remain attached to their original measured return accounting; the recall does not create, consume or lose tools. A failed native placement/post operation remains pending and retries at thirty-second intervals. No ship order is inserted/cancelled, and player controls retain priority.

## Unpaid passenger evacuation

After a confirmed cancellation deadline, the current booking ID is marked void **before** native removals. Only its recorded passenger templates and actors are touched. The helper checks the native role before removal and preserves any actor/template that has become ordinary crew. It confirms template absence, removes the cancelled passenger's body, and checks it is no longer aboard. Rejected removals remain pending; repeated checks do not delete unrelated crew or pay anything.

This is deliberately an unpaid teleport-style cancellation cleanup wherever the ship is. It does not pretend the passengers arrived at a station or that a mission completed. Normal paid services still require their booked destination, complete itinerary and genuine full-party departure. Every expired ID stays in a saved void history, so a later cancellation cannot make an older void fare eligible again. Missing legacy numeric IDs are normalised before table lookup. Cancelled IDs and the cleanup-in-progress flag are rejected by payment, boarding and delivery helpers. Cleanup does not set delivered/completed/reputation/payment markers or overwrite another occupation's reward state.

The manifest is cleared only after every booked entry has departed or been preserved as deliberately recruited crew. Passenger berths are then available for new contracts. Cancellation notices, completed evacuation and crew recall use the vanilla General Logbook. No financial ledger entry is fabricated for these zero-payment events, and the vanilla transaction screen is unchanged.

## Persistence, native mechanisms and compatibility

`md/VGO_Recovery.xml` uses its own persistent registry, populated by real booking/deployment signals, initial saved-state recovery and a five-minute scan of the mod's existing blackboard keys. It does not scan the galaxy every frame. The normal ship watchdog keeps live manifests registered after a default is changed; recovery also finds old pending manifests that earlier versions stopped tracking. Timers, contract IDs and per-entry removal progress survive save/load.

The old immediate `cancel`-phase passenger deletion is removed. Boarding interruptions retain the party for resumption; the separate persistent-service rule governs cancellation. Expired cleanup blocks simultaneous new boarding/native handoff, and the immutable recorded service type prevents cross-service misdelivery. Runtime 40, worker version 19 and tour wrapper version 10 retain the existing guarded upgrade/default recovery.

Native interfaces were checked against the pinned X4 9.00 command/property source already used by the mod: `entity.roleobject`, `npc.npctemplate`, `ship.people`, native order queues, `table.keys.list`, native room placement and `add_actor_to_post_location`. The latter moves the **existing** actor to its default control-post location. See [native source](https://github.com/ArtByunex/x4-foundation-artbyunex/tree/e3e8a345e5624db118bff3eb171b60b0993fcc2c) and [IMPLEMENTATION.md](IMPLEMENTATION.md). Native acceptance and merged installed behavior still need X4 confirmation.

Only Occupations source changes. Other mod source hashes, Forge's special weapon, Astrid equipment, Protected UI, Inventory Collector, existing payments and normal turret controls are preserved. No new game is required by the implementation.

## Validation and live checks

299 Python contracts pass, including 44 new executed lifecycle cases: exact 20/30/120-minute boundaries, longer measured tours, zero-stop waits, retained defaults/queues, combat/lockboxes/player control, resuming and cancelling again, saved stable deadlines, rejected native removals, recruited passengers, voided fare protection, normal earned claims, independent registry recovery, original crew identity/post preservation, failed native recall/retry, unloaded roster return, and integration with the existing paid crystal return controller. The earlier 255 cases remain, with the tour default guard updated to the new requirement. 78 Lua mocks, XML/API/reference validation, five native patch selector/grammar checks, seven package/source audits and bundle integrity are separate checks.

The local native actions are mocked. **These new timers, emergency returns and cancellation evacuations have not been live-tested in X4.** The earlier tour boarding `0/2` report is not proved fixed by this policy; it now has a defined unpaid release if the service is actually cancelled. Other prior runtime limits remain documented.

1. Use a backup of the same save and keep Protected UI/Inventory Collector. Exit X4 and overwrite the extension with 0.4.0.
2. Leave a real crystal/hacker representative ashore and fly away. Keep its name/role/post recorded. At twenty game minutes away, check the General recall notice and the **same** NPC's native crew entry/availability. Test visible and unloaded ship interiors. No extra NPC, money or hacking tool should appear.
3. Redock before twenty minutes and let the original walking return finish. No premature recall should occur. Repeat after a save/load and with player control/manual orders; those orders must remain intact.
4. Board a taxi party, remove its persistent service and queue, then wait thirty game minutes. Confirm only booked passenger berths/bodies clear, with no fare or reputation. Test a rejected removal/reload if a suitable debugging setup is available.
5. Repeat with a tour: minimum two game hours after actual cancellation. Use a slow cruise/history with a longer measured estimate and inspect the logged grace in minutes. Existing booked stops remain intact; a new default booking targets twenty.
6. During both services, insert combat/lockbox/manual orders or pilot the ship yourself while retaining the default or a queued instance. Wait beyond the cancellation limits: the same party and route must remain. Change/remove the service, then restore it just before expiry: the timer clears and the original party resumes.
7. Recruit a booked passenger into ordinary crew before cancellation expiry. It must retain that role, native crew entry and actor. Independently transfer a deployed crew member to another ship: emergency recall must not pull it back.
8. Verify a successful normal booked delivery still pays once and an already-earned unpaid fare remains owed. A cancelled/evacuated contract must never pay, even if the service is later reselected. Check General and the original native Transaction Log.
