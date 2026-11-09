# Reproducible tests — 0.4.7 development

## Current 0.4.7 office, survey and scheduling checks

Run [the current existing-save sequences](LOG_REVIEW_0.4.7.md#existing-save-acceptance). Recheck the previously production-only station's menu, actual office creation after docking, same-NPC physical walk, native tool charge/effect and return for every available panel type. Validate occupied-room cleanup and absent assets/docking. Check an actual accepted signal survey, native station discount, six-second actual offer count and real locked-market delivery offer; absence of an eligible native offer must remain explicit. Continue the previously paid crystal worker through another sale and inspect for rapid wake warnings. 440 Python contracts and 91 Lua mocks pass; no native execution test is available here.

## Current 0.4.6 spacesuit and station population checks

Run [all current existing-save checks](LOG_REVIEW_0.4.6.md#existing-save-acceptance). Normal exits must remain native. Reproduce the null-suit/null-control/old-room stall; observe source reset, its actual native success event, one suit exit, real control and re-entry. A refused transfer must stop or return once, never loop. Verify manual reseating, teleport, source docking/loss, conversation, save/load and blocked/transit boundaries. Observe station population at multiple docks with and without service slots. 415 Python contracts and 91 retained Lua mocks pass; no X4 executable or installed merged catalogs are available here. Earlier sections below retain their release-specific evidence; current tour defaults are ten stops and minimum cancelled-tour grace is three hours.

## Current 0.4.5 tour defaults and timeout checks

Run [the five current existing-save sequences](LOG_REVIEW_0.4.5.md#validation-and-install). Verify new ten-stop defaults without rewriting accepted/configured routes; one extra hour per active tour task/dock deadline without repeated padding; minimum-three-hour cancelled-tour grace and one-time legacy extension; direct/queued order priority, party retention, booked destination departure and no premature/duplicate fare. Already disposing parties stay void. 400 Python contracts include thirteen new cases; 91 retained Lua mocks cover unchanged UI. No new X4 runtime test is available here.

## Current 0.4.4 cold-start and compatibility checks

Run [the five current existing-save checks](LOG_REVIEW_0.4.4.md#validation-and-existing-save-acceptance). Verify registry presence precedes count; station finalisation uses the original list-valued wares argument; optional trade subscriptions keep native eligibility and existing-subscription protection. Do not replay a completed third-party initializer. Continue booked tours, crystal invoices, direct orders and crew visits unchanged. 387 Python contracts include nine new boundary cases; 91 retained Lua mocks cover unchanged UI. Nine native selectors across five diff files remain. The supplied manifest43 log confirms particular tour/sale outcomes, not runtime execution of these new fixes.

## Current 0.4.3 scanner native request check

Run [the four current live steps](LOG_REVIEW_0.4.3.md#install-and-live-check) using an eligible non-player station outside the existing twenty-four-game-hour survey cooldown. Verify the old Manager.SelectMission/null-cue errors disappear while real payload, native exclusions/cap and other station effects remain. Confirm existing orders, bookings, stock, invoices and recovery clocks continue. 378 Python contracts include eight new reference/dispatch boundaries; 91 retained Lua mocks cover unchanged UI. No new native runtime test was possible here. The supplied manifest42 log establishes the particular recorded payments and completions, not a runtime result for this correction.

## Current 0.4.2 crew/order regression

Run [the six current existing-save acceptance sequences](CREW_ORDER_RECOVERY_0.4.2.md#validation-and-remaining-runtime-checks), especially the reported AKD-700 paid representative state followed by Scanner/Patrol. Verify actual flight while the same NPC remains ashore, no background status takeover, direct-order priority, non-sliding twenty-minute recall, same-NPC redock/recall and no duplicate invoice. Test native scanner caps -1/0, scanner-equipped capital ships, queued actual publication, signal benefits independent of publication and saved pending samples. There is no new X4 runtime result from this environment.

370 Python contracts (22 new) and 91 Lua mocks pass. Native diff selectors/grammar and package/source audits are separate static checks. Earlier sections retain their release-specific evidence and outstanding runtime checks.

**No actual X4 runtime test has been performed in this environment.** XML/API/reference checks and inventory/UI mocks are separate. Use a backup save, Protected UI enabled, the new extension installed, and a fresh debug log. Keep Inventory Collector and your normal mod load order.

## Current station signal and boarding acceptance

Run [the 0.4.1 scanner/passenger tests](SURVEY_BOARDING_0.4.1.md#validation-and-live-acceptance) first: real module information, public leaks, timed off-screen alternatives, station bonus cooldowns, actual native offers/market delivery work and the existing saved party boarding/launch/drop-off/fare. The new source paths have not been run in X4 here.

## Current spacesuit exit and Astrid acceptance

Run [the 0.4.1 checks](SPACESUIT_RECOVERY_0.4.1.md#validation-and-live-checks) first. Normal exits, changed/cancelled requests, native transfer refusal, actual suit control/HUD and re-entry must all be verified with the installed spacesuit mods. Retest full-speed Astrid braking and partial-control transitions without any ship-blackboard errors. New native recovery has not been run in X4 here.

## Current cancellation and stranded crew acceptance

Run [the 0.4.0 live sequences](RECOVERY_POLICY_0.4.0.md#validation-and-live-checks) first. Leave the same crew ashore and verify its native roster/post return after twenty game minutes; test normal redocking, failure retries, player control and saved clocks. Cancel persistent taxi/tour services and verify unpaid 30-minute/minimum-two-hour departure. Retain default/queued services through combat, lockboxes and manual orders beyond those times: no passenger should leave. Resume just before expiry with the same party/route, preserve recruited passengers as crew, and reject all fares for expired contracts. Verify new twenty-stop defaults and unchanged already-booked routes.

## Current paid crew-return acceptance

Run [the 0.3.9 live sequence](LOG_REVIEW_0.3.9.md#live-acceptance-on-the-existing-save) first, using the saved Astrid Tours seven-item sale. Record balance and the existing representative's identity. The same actor must return from the actual counter to a real ship room, preserving its crew role/control post, with no second payment. Test loss of the AI caller, a blocked path, save/load mid-return, player control and leaving/redocking under a direct order. Allow two game minutes for documented same-dock native placement recovery. Then verify AI departure and another full cycle. The new source tests inject a lost return value; this is not a finding that this specific native fault caused the stall.

## Current off-screen and physical service acceptance

Run [the 0.3.8 live sequences](LOG_REVIEW_0.3.8.md#live-acceptance) first. Check a saved seven/24-item batch at a real remote dock: finite broker sale, actual money and native receipts, next-cycle undocking. Separately observe the physical same-crew counter/return path near the player. Test the off-screen-sales toggle, player arrival during the wait, partial invoices, save/load and direct orders. Taxi/tour must preserve named real rosters, launch, actually arrive, release every booked passenger at the immutable destination and then pay once. Enter the sector mid-transfer and confirm the same actors reappear. No new full service cycle has been run in X4 here.

## Earlier native handoff and all-role acceptance

Run [the six 0.3.6 live acceptance sequences](LOG_REVIEW_0.3.6.md#live-acceptance-on-the-existing-save) first. A successful landing must resume the occupation at its service dock, not insert immediate Undock. Verify actual taxi/tour NPC exit at the booked station, real sale money, Morale travel/effects and every role across sectors. Isolated helper mocks previously missed this dispatcher boundary. No alternate passenger station is now selected; an unavailable booking is explicitly blocked.

## Earlier passenger completion acceptance

Run [the six 0.3.5 passenger acceptance sequences](PASSENGER_COMPLETION_0.3.5.md#reproducible-live-checks) first. Verify actual station-room arrival for the whole taxi/tour party and actual credit balances, including the vanilla transaction ledger and General payment notices. Roster release alone is not departure. Test blocked native walking, documented two-minute same-actor recovery, partial parties, old-save retries, player-station pickup and duplicate prevention.

## Earlier recovery acceptance

Run [the six 0.3.4 acceptance sequences](LOG_REVIEW_0.3.4.md#live-acceptance-steps) first: the already-boarded taxi's real sector travel/docking/drop-off, remote escort discovery, Morale startup and actual crew effects, critical/default recovery, queued docking/player-order priority, and off-screen crystal work/sales. Existing saved Holds must be reassigned manually so intentional Holds are preserved. Tests must show actual arrival and NPC departure, not just a successful native return value.

## Earlier supplied-log acceptance

Run the [0.3.7 live checks](LOG_REVIEW_0.3.7.md#live-acceptance) first: existing stock at dock, actual population request, correct merchant/customer point, real same-NPC outward/return walk, finite accepted inventory, player cash and native receipts, per-buyer backoff, save/load and direct orders. The prior source/mocked pass missed null first-use clocks and the station-targeted interaction query. The log proves real pickups and no sales; a new complete sale must be observed before calling this verified.

## Crew counter-sale acceptance

Run all seven [crew sale acceptance sequences](CREW_CRYSTAL_SALES_0.3.6.md#live-acceptance). Observe the same existing NPC walking to the actual station inventory trader and back. Check merchant inventory/finite batch, actual positive cash and one native receipt. Missing counter or failed walking cannot pay or consume stock. Save/load a partial invoice and a paid visit awaiting crew return; do not count an empty batch as permission to leave. Also reject/delay a verified escort/patrol payment and confirm only the unpaid balance is retried.

## Current menu and crystal repair

Run [the 0.3.1 reproduction](MENU_CRYSTAL_REVIEW_0.3.1.md) first. The open station submenu must replace Checking on a reply **without** manually re-preparing/closing it. Test pause/ten-second UI timeout/retry, numeric MD boolean flags, empty/unavailable interiors, lost UI event and stale ship/station selection. Mission Director requests still need unpaused simulation.

Crystal Miner now defaults to **Simulate crystal mining off screen**. The earlier following-player fallback is superseded. Run [all six current crystal-commerce acceptance steps](CRYSTAL_COMMERCE_0.3.3.md#reproducible-live-test): remote field travel, actual finite depletion, active elapsed ticks, stock, real docking, crew-counter sale/native cash, save/load and interruptions. Test the retained visible turret/drop path separately. Neither the log's earlier zero crystal total nor source mocks verify the new flow.

## Hacker: full visible cycle

1. Use an AI-controlled player ship with an existing captain and preferably an idle service crew NPC. Record crew names, roles, counts, ownership and player hacking-tool inventory. Select Galactic Station Hacker, range 99, risk 2. Verify it stays assigned and chooses a real non-player dockable station in another sector.
2. Initially provide no hacking tools. Confirm it waits, does not fly off/hack/gain tools, and inventory is rechecked after **600 game seconds**, including at the expected SETA rate. Add the actual native tool, such as the Security Slicer or Security Decryption System required by the selected panel. The next scheduled check must loan actual tools without duplicating or touching unrelated inventory.
3. Accompany it so ship/dock/security or engineering interiors are loaded. Confirm docking, the SAME existing crew member leaving, traversing native paths to the actual panel and pausing at it. For a captain-only ship, verify the captain leaves and later resumes the same control post. No NPC clone should appear.
4. Compare the chosen panel and its native status before/after. Confirm the real requested effect, native cost and tool consumption. Watch the player's own controls/animation for unwanted effects from the remote native API. If that API refuses a remote invocation, record the reason; this is an unresolved acceptance case, not a successful hack.
5. Follow the same actor back through the dock into a ship room. Completion must wait for return. Confirm unchanged crew identity/role/owner/count, normal captain control, actual undocking and a new station in a different sector. No automatic hacker wage or positive reputation should appear.
6. Repeat with S/M/L/XL docking geometry and loaded/unloaded sectors. Off-screen native transit may differ; missing interiors must produce waiting/failure with no invented effect.

## Station context command

Select an AI player ship, right-click a non-player station, then Hack station. Confirm the native submenu populates real present panels, with active effects disabled. Choose one panel. A finite queued order must preserve the earlier queue and default behaviour, perform one matching hack, return the actor, then end and resume the previous default. Test an existing taxi/tour default with a real passenger manifest and verify its contract/configuration resumes unchanged. Player stations, the currently flown ship, unavailable docks and absent panels must not be hacked.

Choose multiple ships for the same panel: reservations must prevent duplicate costs/effects. Test a second panel later and a different station. The native transaction ledger must still open, search, page and graph normally.

## Hacker failure and save/load

Save/load before tools, during travel, with the actor ashore, after the native call and during return. Verify same actor/token/loan quantities and no repeated native charge. Issue direct movement/Hold orders at each stage. Direct orders must take priority; while ashore, the actor must wait for a restored station docking link and return physically. If the captain is ashore, restore that link with normal in-game controls; do not expect a replacement captain. Test station ownership changes, destruction, ship loss, missing panel, invalid room path and unavailable native bridge. Unavailable interior/panel geometry before deployment must defer after five minutes and try another station; it must not expire a ten-minute missing-tool wait or abandon an already deployed actor. No crew teleport, free tool, fake hack or unsponsored payment should occur. Capture any stalled path with its status and ship ID.

## Actual money tests

Record player credits before/after each completed sponsored contract. Verify native incoming ledger entry, `GO payment:` or `GO passenger payment:` actual/balance values, one `Vardath Payment` General receipt and the matching activity total. Activity/approach/sight visits are not payments.

- Escort: a foreign trader must reach its real station after meaningful protection; default fee 12,000 Cr.
- Taxi: all accepted actual NPCs must board, depart and disembark; 8,000 Cr per delivered passenger. Test 0/1/10 available berths and interrupted boarding/delivery.
- Tour: board actual NPCs, visit ten distinct sites across the connected galaxy (normally three or more sectors), dwell and disembark. Default fare 500,000 Cr per delivered passenger for ten verified stops. No partial-route/partial-manifest fare.
- Trade patrol: follow actual traffic and verify meaningful protection/arrival; foreign service 8,000 Cr, own trader 0 Cr. Save/load after completion must not pay twice. Previous zero-fee completions are not backpaid.
- Builders 1.75: observe its existing genuine contract/progress payment and the shared-cursor receipt; unchanged source still measures the actual credit delta. Do not count the private income journal as a second payment.
- Crystal sales: only finite saved stock after actual station docking, quoted at native inventory prices; observed cash must match receipts. No separate completion wage.
- Hacker, surveys, mapping, morale and other unsponsored tasks: no invented wage. Morale/service reputation requires an actual eligible improvement/completion and obeys cooldowns.

## All existing occupations

For each default verify selection, executable targeting/movement, actual effect, completion, next work, save/load, player-order interruption and invalid-target recovery in at least two sectors. Range 99 must use connected galaxy coverage. A safe deferred action or prerequisite wait is not a successful job.

- Crystal miner: all armed ship sizes, remote resource-backed simulation, partial/empty fields, actual docking, stock/claim settlement and native cash/receipt; real visible forward/turret damage/drop collection and current-drop inventory redirection with Inventory Collector. Existing player inventory must remain untouched. Test repeat, cancellation, buyer loss, range/risk, multiple miners, pause/SETA and save/load. Use the current commerce report rather than superseded inventory-only tests.
- Scanner: record individual module/component native scan level; approach a real surface and maintain line of sight. Verify a genuine level/information increase, resume large stations and defer unloaded geometry without marking it scanned. Default ship eligibility is S/M.
- Mapper: actual gate/anomaly destination records, invalid/mission exclusions, and permitted same-ship transit with equipment/crew retained.
- Lure: actual hostile attention and pursuit, valid friendly anchor, breakoff if not followed or outmatched; physical forward firing requires loaded simulation.
- Demolition: actual destructible rock damage/destruction, appropriate weapon/size and next target; no vanished-reference success.
- Morale: actual crew morale increase with limits and eligible faction reputation cooldown; maxed crews produce no improvement reward.
- Inspection: native scan, actual faction illegality, jurisdiction, noncompliance and no selection-only neutral hostility.
- Recruitment: hostile below 25%, actual capture eligibility, probabilistic failure/cooldown and success ownership transfer with original hull/equipment/crew safely retained.

Attach the new complete debug log and the observed ship ID/stage for any failed acceptance case. The older debug(6).log cannot verify new 0.3.0 actions.

## debug(7) recovery cases

Test an old/default worker with an absent or present-null cached sector list; it must search and travel without a `.count` lookup error. Check actual reached sectors in `GO sector travel:`. Confirm the one-off hacker order produces no `default`/`immediate` parser warning. Keep actual NPC/context/full-manifest gates during private-room/transport-waypoint boarding and disembarkation. Activity income must display 5,000,000 Cr for the recorded tour, not 500,000,000. Check Cargo Teleport's zero-transfer native failure receives at most one docking retry and no duplicate goods or payment.

## Local validation for this build

299 Python contracts and 78 Lua mocks pass. Forty-four new cases execute delayed lifecycle/native-boundary recovery. Thirteen new cases exercise independent paid-visit and import recovery. Thirty-one new cases cover the log-11 broker/roster/room/upgrade boundaries. This includes 19 native docking/routing cases, 23 crew retail cases and nine persistent service-invoice cases. The actual five native patch selectors and native 9.00 diff grammar are checked separately. Seven source/ZIP packages and the current six-mod bundle are byte-checked. These are source/mock/packaging checks. All live role interface, physical action, save/load, installed load-order and full-loop acceptance tests above remain necessary in X4; the log confirms only the specific earlier events recorded in LOG_REVIEW_0.3.6.md.
