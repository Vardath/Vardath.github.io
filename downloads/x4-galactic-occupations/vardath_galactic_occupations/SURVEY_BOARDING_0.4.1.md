# Station signal intelligence and passenger handoffs — 0.4.1

## Station, Component and Signal Scanner

The existing galaxy-range/risk controls and native route navigation remain. The scanner now accepts normal S/M/L/XL ships with scanner capability. Two real Behaviour controls are enabled by default: **Simulate surveys without loaded geometry** and **Decode signal leaks and station intelligence**. Turning either off disables that path; explicit false values survive default-order repair.

For an unscanned module, the ship still travels to that real module. With geometry loaded, the existing surface approach and ten-second line-of-sight survey remain. Away from loaded geometry, the new custom equivalent spends ten active game seconds near the module and rechecks ship control, ownership, distance, faction hostility and the module's continued existence on each sample. It then invokes native `set_object_scanned` on **that component only**, at the player's native scanner cap, and counts success only when real scan level/discovery increases. No arbitrary station-wide 100% flag is assigned. Eight module successes per assignment bound the work before the next search.

The job also finds existing unlocked public data/voice signal leaks, approaches them and spends fifteen active seconds decoding. Visible physical leaks require line of sight to their parent object. Locked leaks and `signalleaktype.mission` story leaks are excluded. Actual data leaks are consumed; voice leaks are retained so their real native missions remain available.

Native leak objects are normally spawned on visible surfaces. Off screen, the ship instead surveys the station's **actual native signal-leak attachment slots**, requiring a real station visit and fifteen seconds of active proximity work. No slots means no invented leak target. Player arrival during that work prevents the off-screen completion. This is an explicitly simulated network survey, not an assertion that a rendered data-leak object was present.

Successful leak/network work can apply these gameplay effects:

| Effect | Native implementation and limit |
|---|---|
| Station trade discount | Namespaced native station coupon for 24 game hours, amount 4 on the native ware-price-variation scale. This is **not** a flat 4% discount. A native discount-added event writes a separate confirmation to General. |
| Trade updates | 20% chance of a permanent native trade subscription on the same station. |
| Existing job offers | Reveal the actual registered native leak/ordinary mission offer in the vanilla mission system. No automatic acceptance, success, mission payment or player briefing cutscene. |
| Additional job opportunity | Ask the native generic mission selector for one actual station job, respecting its exclusions, tutorial disable, docking relation and sector quota. Native selection/setup may legitimately produce no offer. |
| Black-market location | Identify a real existing shady-guy control entity and log its actual station/sector. No trader or market is invented. |
| Locked black market | Offer native `GM_BringItems.Start` using that actual contact/station and real native illegal-item delivery requirements. Access is awarded by the native mission only after the player accepts and completes the work. |

A shared **24-game-hour station cooldown** limits the coupon/subscription/new-job opportunity, including across ships and save/load. A physical leak can be processed once. Own stations, destroyed targets, direct-order interruptions, too-short or stale work witnesses, unsafe distance and hostile changes cannot grant these effects. The scanner has no artificial wage or cash-on-scan timer.

The actual native `GenericMissions.Signal_Leak_Offer` library receives one additive registration action. Existing player decoding/cutscene/acceptance handlers are preserved. Older already-running leak offer instances may be registered only when native leaks refresh. The selected native offer is unhidden with galaxy-wide space; actual display and lifetime still depend on the native mission and require live checking. Blueprint lotteries/research unlocks and plot-specific leak callbacks are not replicated by this custom survey; their native player mechanics remain.

## Taxi/tour boarding and departure

The native 9.00 `GenericMissions.CleanupActor` explicitly avoids `exists` checks for disconnected NPCs. The previous Occupations off-screen boarding/exit helpers required `actor.exists`, rejecting a valid named passenger identity when its body was not connected. They now check the actual NPC class, the exact ship passenger template, native transit state and the resulting role object. Boarding detaches the body **before** assigning its ship role object. The same actor is retained; no replacement passenger or captain is generated.

The same identity-versus-body correction also protects twenty-minute crystal/hacker recalls, restoring their original crew flags and returning only actual borrowed tools without repeating an invoice. Native roster/post checks remain required.

Both boarding and departure now support unobserved, bodyless interiors in the player's sector as well as other sectors. When the player actually observes the ship/station, physical walking remains the normal route. After a visible boarding path stalls for two game minutes, guarded native placement recovers that **same** booked NPC to an actual available ship room point; roster and real resulting room context must be observed before acknowledging boarding. Untagged native path waypoints in unlocked walkable rooms provide an additional fallback without taking service/marine crew seats.

Up to ten passengers still require actual free native crew capacity. No fare is paid at boarding. Existing immutable pickup/destination bookings, whole-party departure, full tour itinerary, actual-credit receipts, cancellation grace and saved identities remain. The log proves the old wait, but contains no per-actor state proving a single exclusive cause; these are repaired code-level blockers, not a claim of a newly observed successful tour.

## Validation and live acceptance

**No new X4 runtime run is available here.** All 348 Python contracts and 91 Lua mocks pass. The survey suite executes the actual module simulation, leak discovery, timed navigation/MD dispatch and benefit handlers against refusal/interruption cases. Passenger fault tests disconnect the same real mocked NPC with `exists=false` and clear its role object during detach, exercise the full boarding/departure/payment sequence and reject a native placement that reports success without actual room change. Eleven XPath operations across five native patch files match the inspected 9.00 reference and diff grammar; the installed merged mod graph remains unverified.

1. Reassign a scanner with galaxy range 99 and both new controls enabled. Record an unscanned station/module and its scan information. Keep the player in another sector. Verify actual travel, ten-second samples, native information changes, another station and saved progress. Repeat with simulation disabled and while issuing a direct order.
2. Inspect a station with real leaks while present. Verify approach/dwell, obstructed-view rejection, one data-leak consumption, retained voice leak and General discount confirmation. Check the actual station trade prices. Confirm there is no scanner wage or invented transaction row.
3. Survey a remote station with native leak slots. Verify fifteen seconds of actual work, the 24-hour cooldown across two scanners and save/load, and abort when the player arrives mid-sample. Inspect native mission offers and their acceptance/objectives. Finding an offer must not complete it or award its payment.
4. Use a station with an existing black-market contact. Check the logged location, actual native delivery offer, required inventory removal only after real acceptance/delivery and normal market access afterward. No market should appear where no real contact exists. Log any native offer setup error or visibility problem.
5. Resume the already-stalled Astrid tour and a taxi with their saved passengers. Away from the player, verify the same names/templates board, the ship launches and navigates, and everyone is removed from its roster at the **booked** destination. Return while boarding/aboard/disembarking to check the same bodies materialise. When watching, test walking and the guarded two-minute blocked-path recovery. No extra crew or early fare.
6. Complete every booked tour stop before return, then verify real passenger departure and one actual fare in the vanilla ledger/General. Test a direct order, combat, cancellation, save/load and recruited passengers retained as crew. Continue the spacesuit/Astrid checks in [SPACESUIT_RECOVERY_0.4.1.md](SPACESUIT_RECOVERY_0.4.1.md).
