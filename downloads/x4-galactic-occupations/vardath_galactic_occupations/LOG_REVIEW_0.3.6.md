# debug(9): native dock handoff, galaxy movement and booked destinations — 0.3.6 DEV

Updated 8 November 2026. The new log contains 1,895,509 bytes, 12,915 lines and 1,268 error-tagged records. It demonstrates that earlier isolated helper tests missed an actual native order-dispatch boundary. Green static/mocked checks did not establish functioning passenger departure or sales. This release fixes the demonstrated boundary and adds tests that include it. No X4 executable, current save or complete installed merged catalogs are available here; newly changed native integration remains unverified in-game.

## What the log proves

| Observation | Evidence and interpretation |
|---|---|
| Taxi lands and immediately takes off | Astrid Tours AKD-700 queues DockAt at 3599.73, 3697.70 and 3766.40. At 3640.06, 3717.83 and 3784.67 the monitor reports `docked=1 cancelled=0 current=Undock default=VGO_taxi`. This is the landing loop, not a completed passenger transfer. |
| Crystal sellers have the same interruption | CAT-914 reaches its buyer, then reports `docked=1 cancelled=0 current=Undock` at 3764.42 and 3784.67. No crystal-sale credit is recorded. The stock must survive the failed handoff. |
| Cross-sector movement often aborts | 86 of 88 shared travel returns are false. Morale JHK-505 fails remote sector attempts and later reports Company Regard while approaching a miner. The log does not prove it is permanently stationary, but does show repeated failed routing and no new morale completion. Its eight reported completions are saved history, not eight new visits in this log. |
| Crystal simulation has a type error | Four errors reject the old time-valued remainder expression in the ore/silicon search. Three later batches nevertheless record actual native depletion of 2,400 resource units and 24 saved items each: **72 simulated crystals total**, without player-inventory credit. |
| Payments/completions | One new patrol completion records an observed 8,000 Cr increase. No taxi/tour departure trace, passenger fare or crystal sale is recorded in this log. Saved activity totals are separated from new payments. |
| Other execution errors | Two imported worker contexts report blocked run_script without a child, and native NPC pathing reports 12 invalid endpoints plus 12 related distance lookups. The latter do not identify the owning passenger/job, so no broad native NPC-state rewrite is substituted. |

## Implemented repairs

### Keep the occupation at the service dock

Native 9.00 `orders.base` checks a hard-coded allowlist before starting an order on a docked ship. Custom VGO behaviours are absent, so its catch-all inserts Undock before the behaviour can resume. This explains why a successful finite DockAt alone did not allow the later passenger/sale code to execute.

One **attribute-only native XML diff** suppresses that pre-start check only when all these conditions hold: the ship is player owned; the current order is its exact tracked VGO taxi, tour, crystal, hacker or single-hack worker; it is docked at its recorded operational service station; and the saved handoff has not expired. Other orders, a different dock, lost ownership and expired/missing handoffs retain native handling. The helper records a bounded 30-minute handoff before queuing native DockAt. The completed-order watcher clears only its finite-order bookkeeping, keeping this separate handoff. Explicit `vardath.go.depart` clears it before undocking.

This is a narrow necessary native integration patch, not a replacement `orders.base` script or an invented `allowdocked` order attribute. Native order definitions do not expose a general custom-behaviour flag for this rule. Player orders still take priority. No native turret/UI files are altered.

### Deliver at the booked station

Taxi destination is fixed when its real manifest is booked. Tours return to their pickup station after the booked distinct-site/sector itinerary. The old automatic alternate-station search has been removed. Existing boarded taxis preserve their saved planned destination; an older tour without a booking snapshot restores its saved pickup station. An original taxi destination already overwritten by an older version cannot be inferred from a missing historical snapshot, so no guessed station is invented.

The shared departure code refuses a station other than that booking. Walking-path recovery moves the SAME NPC only to a genuine point at the booked station; it does not send anyone to a safety/backup station. Missing permission, a destroyed station or no real usable room means retained passengers and an explicit blocked status, not a substitute destination or fake fare. The worker waits rather than rotating sectors looking for other work while holding a blocked booked party.

The existing whole-party physical station-room check and observed-credit/unpaid-balance accounting remain. A missing legacy departure clock is initialised without resetting each person's original movement deadline. Existing NPC identities, crew/equipment, tour progress, sale stock and outstanding fares are preserved. Already-inserted Undock orders are not indiscriminately cancelled; a ship already launching may finish that launch, then its next planned docking uses the corrected handoff.

### Honour galaxy routing for the actual occupation

`move.generic` declares a `useknownpath` parameter, and the VGO helpers pass false, but its four native jump-discovery calls hard-code player-known paths. Four attribute-only changes honour the declared parameter only while a player ship is executing its exact tracked VGO worker at runtime version 36 or later. Vanilla orders and other contexts retain the original expression. Native travel blacklists, range/risk and route existence checks are retained; this does not invent a gate or bypass player blacklists.

This addresses a verified implementation mismatch affecting shared travel/approach, including Morale. It is an inference that the known-path mismatch contributes to the log's failed attempts; the log does not expose every route/blacklist decision. No claim is made that all 86 failures have one cause. New boundary tests cover all thirteen role IDs, and a Morale test executes remote approach followed by the actual timed crew-improvement XML. In-game travel still needs confirmation.

### Correct crystal search typing

Replace the invalid time-remainder resource ordering with a saved boolean alternation between ore-first and silicon-first searches. No new resource or credit is generated by that choice. Existing finite native depletion, stock, real buyer docking, observed sale cash and unpaid balances remain. Crystal sellers receive the same corrected dock handoff as taxis/tours. The newly requested existing-crew counter visit, merchant item acceptance and physical return are now implemented; see [the retail report](CREW_CRYSTAL_SALES_0.3.6.md). No new in-game sale is claimed from the old log.

### Retain earned service invoices

The wider audit found that the old generic reward helper marked escort/patrol work paid before checking actual credit. It now saves the verified fee/serial/faction, records only observed credits, retains rejected/partial balances and retries the remainder before another assignment or repeat-off standby. Reputation and the paid marker follow full settlement. The successful morale path grants its controlled zero-cash reputation once; unsuccessful/no-improvement visits remain unrewarded. Already marked historical assignments are not guessed into retroactive cash.

## Review of all thirteen occupations

| Occupation | Implemented action/guard checked | Current runtime evidence or limitation |
|---|---|---|
| Escort | Real active trader voyage, shared travel, proximity/arrival before fee | One saved earlier completion; no new escort completion proved by log9. New routing and persistent fee settlement need live confirmation. |
| Taxi | Real party, booked destination, docked handoff, whole-party exit, observed fare | Log9 proves the old native undock loop; new complete handoff is exercised with mocks, not X4. |
| Station/component scanner | S/M module surface/line-of-sight custom survey equivalent and verified native scan-level change | Not assigned in log9. Appropriate ship/scanner and loaded geometry remain required; no fake scan state. |
| Wormhole/anomaly mapper | Real connections, recorded visits and permitted transit | Not assigned in log9; actual traversal/save-load integration remains unverified. |
| Luxury tour | Real passengers, distinct galaxy itinerary, original return station and fare | Log9 shows failed travel/pickup; new shared handoff/locked return tested with mocks. |
| Crystal miner | Finite depleted-yield off-screen batches and saved sale stock; retained visible path | Three batches/72 items recorded. No sale is proved; docked boundary and actual-crew/counter/invoice/return sequence implemented and exercised with native mocks. Visible deposit/turret/drop integration remains unverified. |
| Hostile lure | Hostile/anchor selection, actual provocation and pursuit checks | Log9 defers physical weapon operation without visible attention. Off-screen physical provocation is still a stated constraint, not simulated success. |
| Asteroid demolition | Real destructible targets and weapon/damage checks | Not assigned in log9. Appropriate ship/weapon and physical simulation remain required. |
| Fleet morale booster | Remote approach, timed support, actual editable crew increase and controlled reputation | Eight completions are saved history. No new improvement in this log; shared routing is corrected and full XML action is exercised with mocks. |
| Traffic inspection | Native-style proximity/time inspection, jurisdiction and actual native cargo illegality | Not assigned in log9; new engine execution unverified. |
| Emergency recruitment | Hostility/hull/eligibility, conservative probability, ownership/crew preservation | Not assigned in log9; live ownership-transfer/save-load effects unverified. |
| Trade route patrol | Real trader route/proximity/arrival, legitimate fee | One new observed 8,000 Cr payment in log9. Shared route correction and persistent unpaid service invoices retained. |
| Station hacker | Same existing crew member, real panels/tools, return before continuing | Not assigned in log9. Receives docked handoff integration; actual panel/actor bridge remains unverified. |

The log does not prove every occupation performs its intended effect. Static checks and mocked action execution cannot establish that result, and prerequisites/engine constraints are not silently replaced with timer rewards. All thirteen role definitions and shared galaxy range remain; no requested role is removed.

## Validation and native sources

All **203 Python contracts** and **78 Lua menu/native-bridge mocks** pass locally. The 19 new cases include the missing native pre-start dispatch decision, unpatched landing-loop reproduction, queued dock to actual departure XML, tours and crystal stock settlement, player-order/ownership/expiry/different-dock guards, immutable destinations, all thirteen shared route IDs and remote Morale approach followed by observed skill change. An additional 23 retail cases execute the actual MD/AI counter/crew/invoice paths with native effects mocked, and nine service cases reject/partially apply credit and retry earned fees. They remain mocks of native effects, not engine tests.

The actual native 9.00 diff grammar validates both new patch files. All five new selectors match exactly one intended attribute each in the inspected native sources. Command metadata, XML syntax, script references, archive layout/CRC and byte agreement are checked separately; seven extension packages and the five-extension bundle are audited. Installed merged-mod patch resolution remains unverified.

Primary sources are [orders.base.xml](https://github.com/ArtByunex/x4-foundation-artbyunex/blob/e3e8a345e5624db118bff3eb171b60b0993fcc2c/aiscripts/orders.base.xml), [move.generic.xml](https://github.com/ArtByunex/x4-foundation-artbyunex/blob/e3e8a345e5624db118bff3eb171b60b0993fcc2c/aiscripts/move.generic.xml), `order.dock.wait.xml`, `order.wait.xml`, `order.wait.signal.xml`, `order.trade.perform.xml` and `libraries/aiscripts.xsd` at the same pinned native 9.00 reference commit. Crew sales additionally inspect `md/npc_instantiation.xml`, `md/npc_itemtrader.xml` and `md/npc_state_machines.xml` there; native `$Stay`, `npc_move_to`, itemtrader placement and `stop_actor_walk` are verified in those sources. New schema/method names are not guessed.

## Live acceptance on the existing save

1. Fully exit X4, overwrite the matching extension with 0.3.6 and restart. Keep Protected UI, Inventory Collector and normal load order. Confirm the 0.3.6 loaded notice. Existing active workers restart with their state; reselect only a job already lost to Hold. Do not start a new game.
2. Resume AKD-700 at PAR Microchip Factory I. If a launch was already inserted, allow it to finish once. The next successful landing must produce `GO service dock resumed:` rather than another immediate Undock. Existing real NPCs must leave at the BOOKED station, then one fare must actually reach the player and appear in the vanilla transaction ledger/General log. No extra party should board in the meantime.
3. Resume the tour, retain its existing stops, complete the booked itinerary and return to the saved pickup station. Every NPC must leave there. A different station must not be substituted. Test blocked/destroyed/permission-refused destination: passengers remain with a clear blocked status and no fare; resolution of an unavailable booked station needs player intervention, not automatic diversion.
4. Check JHK-505 Morale crosses sectors, reaches a real crewed target and records actual morale increases before reputation. Then assign each other role at range 99 and verify real cross-sector movement/effect/repetition. Deliberately block a route to ensure native blacklists remain respected. Record actual ship IDs/sectors and `GO travel:` results.
5. Resume CAT-914/QVT-051 and other miners with saved batches. Confirm no time-remainder error, actual stock, real buyer docking, `GO service dock resumed:`, the same existing crew member at an actual trading-corner merchant, one observed sale credit and matching vanilla receipt, then that crew member back aboard before the occupation launches. No cash just for landing. Interrupt/save-load before, during and after settlement; finite stock/unpaid claims must prevent duplicate proceeds. Test visible real crystal harvesting separately. Run [all retail counter/stock/return tests](CREW_CRYSTAL_SALES_0.3.6.md#live-acceptance), including absent counters and stalled paths. No counter means no stock consumption or cash.
6. Save/load with passengers departing, some already ashore, a pending fare, a seller at dock and a hacker ashore. Test new direct orders and other vanilla behaviours. Only the exact owned service context may bypass the native pre-start undock branch. Preserve the fresh complete log if no handoff trace appears: selector/load-order failure must be distinguished from actor/path or payment errors.

## Remaining external errors

This log still contains missing removed-extension construction-plan dependencies, invalid/duplicate third-party recipes and production methods, Terran ship generator failures, mission-ID/UI errors and bounded 4 KiB save-preview parser messages. The 24 native NPC path errors are not safely attributed to a specific VGO actor. These are not hidden or declared fixed by this release. Earlier external-source requirements and preservation decisions remain in [the debug8 report](LOG_REVIEW_0.3.4.md#remaining-errors-requiring-their-actual-installed-sources-or-more-evidence). The Kopis special weapon, Astrid equipment, other companion source mods and the vanilla UI renderer are preserved. Private full logs/screenshots are not republished.

## Specification audit result

Every shipped role definition, shared scope/dispatcher, individual task, result gate, monetary path and applicable failure guard was reviewed against the requests. All thirteen use the same connected-galaxy range sentinel, with per-role real target prerequisites. This does **not** certify that every feature currently works in the game. In particular: custom escort/taxi services do not accept vanilla mission offers; component survey is an explicit loaded-geometry equivalent; taxi/tour menu eligibility is S/M; demolition uses S/M physical weapons; lure physical provocation needs visible simulation; anomaly traversal fallback is opt-in; the turret mode is an additive controller option rather than an engine enum; NPC remote hacking and the new counter-sale paths need live engine confirmation. The fare is 8,000 Cr per taxi passenger and the booked default 500,000 Cr per luxury passenger, only after whole-party delivery. Crystal sales require actual merchant acceptance of finite stock and use a custom native-average-price broker payment, followed by crew return before occupation departure.

General activity totals are not completion evidence. Each role needs assignment, executable movement, actual gameplay effect, verified completion/repetition, a save/load interruption and unavailable-target recovery observed in X4. No such full thirteen-role runtime run was possible in this environment. The matrix and live steps expose these remaining checks instead of describing this development build as fully verified. Companion packages were also checked for XML/API/reference/archive consistency; that check does not diagnose inaccessible third-party installed sources.
