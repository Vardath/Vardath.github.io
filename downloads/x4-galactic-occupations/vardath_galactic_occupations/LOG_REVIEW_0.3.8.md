# Log review and service recovery — 0.3.8, 8 November 2026

## What the supplied run proves

Reviewed `debug(20261108-021152).log`: 1,572,205 bytes, 10,845 lines and 1,084 error records. Of these, 27 are attributable to the new Occupations counter code: `find_actor_interaction_point object="$trader"` received a merchant NPC, while that API requires `class.object`. This was a regression introduced in 0.3.7. Earlier mocked tests did not model that native type boundary.

| Observation | What it establishes |
|---|---|
| Seven `GO service dock resumed` events | The native DockAt-to-default handoff now executes; this alone is not a completed service. |
| CAT-914, QVT-051 and HNC-507 population diagnostics: zero traders/actual counter slots | Remote dock interiors are not supplying usable trading corners. Requiring a physical counter for every off-screen sale blocks galaxy-wide work. |
| Two completed patrols, each `actual=800000`, with matching balance deltas | Two real 8,000 Cr payments, 16,000 Cr total, in this run. Native raw money is hundredths of a credit. |
| No crystal-sale or passenger-fare payment trace | No new crystal sale or taxi/tour fare is verified by this log. No backpay is invented. |
| Earlier debug(10): seven real crystal pickups; this log retains sale stock | Physical collection has occurred. It does not establish a completed sale. Existing seven-item and 24-item batches must be retained. |
| Earlier boarding reports: `0/2 ... waiting for walkable interiors` | A docked ship without loaded room points can block indefinitely if body geometry is required everywhere. |

## Implemented corrections

### Crystal sales across the galaxy

`Simulate crystal sales off screen` is a real Behaviour boolean, default **on**, independent of the mining simulation toggle. The worker saves it and guarded default-order recovery preserves an explicit false value. A custom broker sale is allowed only outside the player's sector, below visible attention, on the exact owned tracked default Crystal Miner, actually docked at an operational permitted non-player/non-ownerless station. Risk and docking permission are checked. No representative may be deployed ashore.

The sale snapshots finite saved stock before 30 game seconds of broker work, then rechecks all permissions, orders, attention and docking. The shared `crystal.exchange` consumes no more than the smaller of actual stock and that snapshot. It creates no inventory items, crates, merchant or crew visit. This is the custom off-screen sale simulation requested by the player, using native crystal average prices, not a vanilla NPC trade transaction. Off-screen mining remains backed by actual native ore/silicon field depletion and does not follow the player.

One saved invoice handles both physical and broker modes. Missing/null invoice counters and stock keys are explicitly initialised before numeric comparisons; an absent first-sale value is not assumed to equal zero. Stock transfers/conversions occur once; rejected or partial native money preserves only the unpaid remainder, with a one-minute retry. Only observed positive native credit changes produce receipts. Sold totals, completion and small cooldown-limited faction reputation follow full settlement. Existing batches and claims are retained. The next mining cycle calls the native undock path; a miner is not left in a permanent sales state after a fully paid broker transaction.

An old physical preparation first restores its existing representative's saved traits/control post aboard, then switches to the broker path if eligible. A representative already ashore must return before any switch or departure; an empty paid batch does not bypass that return.

### Physical counter visits when the player can observe them

The invalid NPC-as-object call is removed. The controller searches actual nearby free room slots and waypoints. If none qualify, five bounded offsets are derived from the real merchant's real counter slot and validated by native `check_walk_path`, using the documented room/position form with `checkstate=false`. This avoids rejecting a floor solely because the actor is off attention; the native path query must still accept it. The native NPC state machine supports `npc_move_to` with room/context/offset as well as a slot.

A requested/accepted path is not a sale. The same crew actor must actually occupy the merchant's room, stop walking within four metres, dwell for five seconds, and pass presence checks before and after ten seconds of work. The merchant's observed inventory increment limits the physical invoice. Return walking is retried; after two minutes at the same dock, native placement can reconnect the SAME actor aboard. There are no cloned crew, crew-template deletions, rewritten roles/control posts or equipment changes. A direct order that leaves the representative ashore still takes priority and may require redocking.

### Real taxi and tour passengers without permanent unloaded-room waits

Both services retain actual named NPC actors and native passenger templates, limited to ten and actual free crew berths. In the player's sector they use native room walking/placement and actual arrival checks. The room helper now also considers actual free non-generic room points, excluding service/marine posts and docked-ship points in the station fallback. Missing walkable pier metadata no longer blocks searches of the actual station rooms.

Outside the player's sector below visible attention, native-style abstract transfer retains each real cue actor and native roster entry while uninstancing its body. Boarding requires an existing non-transit template and an observed ship role-object assignment. A newly visible party materialises the SAME actors in real ship points; it does not create replacements. This follows the native passenger mission's distinction between roster state and rendered bodies, while providing a custom autonomous service rather than claiming native mission acceptance.

Drop-off is allowed only at the immutable booked taxi destination or original tour pickup, actually docked, after the tour's full booked stops/sector coverage. The exact booked template is removed and absence observed, and the same actor's station role-object transfer must succeed. Five seconds of confirmed whole-party departure precede completion. A rejected handoff, remaining template or unfinished itinerary cannot pay. If a released passenger's body is absent when the player arrives, it is reconnected only to a real room of that booked station before physical confirmation. No alternate or safety station is selected.

Taxi remains **8,000 Cr per delivered passenger**. A default completed ten-site luxury tour remains **500,000 Cr per delivered passenger**, up to 5,000,000 Cr for ten. Fare balances/paid IDs, native credit accounting, controlled reputation, and save/load state are preserved.

## Native sources checked

Pinned X4 9.00 source: [ArtByunex/x4-foundation-artbyunex, e3e8a345e5624db118bff3eb171b60b0993fcc2c](https://github.com/ArtByunex/x4-foundation-artbyunex/tree/e3e8a345e5624db118bff3eb171b60b0993fcc2c).

- `md/npc_state_machines.xml`: `TRANSITION_move_to` accepts a slot or context/room/offset. Native path-to-position uses `check_walk_path` with start/end components and position children.
- `md/gm_transport_passengers.xml`: real passenger templates; rendered body walking/removal differs between visible player-ship and other/off-screen cases. No ordinary cargo substitution.
- Native command metadata: `check_walk_path` permits `checkstate=false` and positional start/end children; `remove_actor_from_room destroy=false` requires cue retention for disconnected entities. These actors are created in the persistent Init cue. `set_entity_role_object` accepts the actual ship/station object. `find_actor_interaction_point` does not accept an NPC as its object.

Sources establish available interfaces. They do not establish their merged behavior in the user's installation.

## Other errors remain separate

The rest of this log includes unsupported inventory resources in non-crafting recipes (280), duplicate module definitions (68), invalid/old construction-plan content (56 header records), blueprint/trade-license warnings, equipment-mod definitions, stale component macros, missing ship generators, optional map/ware patch misses, Kuertee object-resolution failures, and a restricted `OnlineHasSession` call from Mod Support APIs. The 0x1000-limited save-header reads end mid-attribute; those messages alone do not establish whole-save corruption. These are not all caused by Occupations and are not fixed by pretending its counter change removes them. Relevant third-party/effective merged sources are unavailable here; no installed mod or save was deleted or rewritten.

Only Occupations source changes in 0.3.8. Companion source hashes are retained: Builders 1.75, Forge/Astrid 1.15 (including special main weapon), Yaki Habitats 1.23, Cargo Teleport 1.01 and Auto Drones 1.02. Protected UI, Inventory Collector, the native transaction screen and shared General paid receipts remain intact. The six-mod ZIP is a convenience package, not six new changes.

## Validation and remaining limits

242 Python contracts pass, including 31 new cases executing the shipped broker/exchange/MD paths: the saved seven-item batch through actual commercial dispatch and undock; all grades; stock snapshots; partial money/reload/duplicate prevention; invalid docks/orders/visibility; old-visit recovery; accepted/rejected floor candidates; real two/ten-NPC roster handoffs; rejected role/template actions; immutable destinations/full tours; same-actor reappearance; real room-point fallback and option preservation. The earlier suites continue to cover all thirteen wrappers, shared galaxy routing, morale effects, escort/patrol payment recovery, scanning source guards, hacker tools/menu, crystal harvesting accounting, native dispatcher boundaries and interruptions.

XML/API/reference validation, Lua mocks, native patch grammar/selectors and package/source checks are run separately. Native results in the Python/Lua contracts are mocked. There is no X4 executable, save or full installed catalog/load order here: **no new complete sale, passenger path, hack, turret hit or full thirteen-job runtime certification is claimed**. Existing reports explain physical simulation limits for scanning, lure and demolition, native menu/control restrictions and other unverified stages. Range 99 remains the whole connected accessible galaxy, subject to native blacklists and docking/geometry restrictions.

## Live acceptance

1. Exit X4, overwrite only `extensions/vardath_galactic_occupations` from 0.3.8, keep Protected UI/Inventory Collector, and load the same save. Existing workers receive guarded version recovery. Reassign any occupation already replaced by Hold Position in older saves; intentional Holds are preserved.
2. Leave the player outside a docked miner's sector. Enable `Simulate crystal sales off screen`. Record pending stock and cash. Expect broker status, one positive `GO crystal sale`/`GO crystal off-screen sale completed`, sold quantity and only the matching balance change in the native Transaction Log plus `Vardath Payment` in General. Allow the normal 20–30 second work-loop interval, then verify undocking and resource-field travel. No physical counter visit should be claimed off screen.
3. Save/load before payment and after payment. Remaining stock/claim must match; a paid invoice cannot pay again. Disable broker sales and repeat near the player: watch the SAME crew leave, reach the actual trader, sell, return and undock. Watch for any native floor/path errors. A missing/unreachable real counter must not consume stock or grant cash.
4. Test taxi with two free berths and tour with ten, away from the player. Confirm native roster names, unchanged own crew, actual launch and travel; taxi drops at its booked station, tour returns after ten distinct sites and required sector coverage. Confirm all booked passengers leave the roster, their contracts complete, and only then the full fare arrives. Save/load during boarding, route and departure. No alternate drop-off.
5. Enter a passenger sector mid-trip/mid-transfer. Confirm the same named actors materialise, visible departure reaches the actual booked station, and money/manifest cannot duplicate. Test full crew, vanished/refused destination and new player orders: retain blocked parties/unpaid claims without launching a landing loop.
6. Repeat every role's interface/action/next-task/save-load/interruption checks from [TESTING.md](TESTING.md) and the all-thirteen-role matrix in [LOG_REVIEW_0.3.6.md](LOG_REVIEW_0.3.6.md). Morale needs actual crew skill changes; scanner needs an actual scan increment; hacker needs the actual selected native panel effect and same-crew return. An activity line alone is never completion evidence.
