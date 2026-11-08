# Reproducible tests — 0.3.6 development

**No actual X4 runtime test has been performed in this environment.** XML/API/reference checks and inventory/UI mocks are separate. Use a backup save, Protected UI enabled, the new extension installed, and a fresh debug log. Keep Inventory Collector and your normal mod load order.

## Current native handoff and all-role acceptance

Run [the six 0.3.6 live acceptance sequences](LOG_REVIEW_0.3.6.md#live-acceptance-on-the-existing-save) first. A successful landing must resume the occupation at its service dock, not insert immediate Undock. Verify actual taxi/tour NPC exit at the booked station, real sale money, Morale travel/effects and every role across sectors. Isolated helper mocks previously missed this dispatcher boundary. No alternate passenger station is now selected; an unavailable booking is explicitly blocked.

## Earlier passenger completion acceptance

Run [the six 0.3.5 passenger acceptance sequences](PASSENGER_COMPLETION_0.3.5.md#reproducible-live-checks) first. Verify actual station-room arrival for the whole taxi/tour party and actual credit balances, including the vanilla transaction ledger and General payment notices. Roster release alone is not departure. Test blocked native walking, documented two-minute same-actor recovery, partial parties, old-save retries, player-station pickup and duplicate prevention.

## Earlier recovery acceptance

Run [the six 0.3.4 acceptance sequences](LOG_REVIEW_0.3.4.md#live-acceptance-steps) first: the already-boarded taxi's real sector travel/docking/drop-off, remote escort discovery, Morale startup and actual crew effects, critical/default recovery, queued docking/player-order priority, and off-screen crystal work/sales. Existing saved Holds must be reassigned manually so intentional Holds are preserved. Tests must show actual arrival and NPC departure, not just a successful native return value.

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

203 Python contracts and 78 Lua mocks pass. This includes 19 native docking/routing cases, 23 crew retail cases and nine persistent service-invoice cases. The actual five native patch selectors and native 9.00 diff grammar are checked separately. Seven source/ZIP packages and the five-mod bundle are byte-checked. These are source/mock/packaging checks. All live role interface, physical action, save/load, installed load-order and full-loop acceptance tests above remain necessary in X4; the log confirms only the specific earlier events recorded in LOG_REVIEW_0.3.6.md.
